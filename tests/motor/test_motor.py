import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch
from telazocraft.motor.biblioteca import Biblioteca
from telazocraft.motor.util import guardar_json
from telazocraft.motor.sesion import Sesion
from telazocraft.motor import copias, propiedades, mojang
from telazocraft.motor.consola import Consola
from telazocraft.motor.controlador import Controlador


class MotorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.b = Biblioteca(self.temp.name, crear=True)
        ruta = self.b.raiz / "servidores/prueba"
        guardar_json(ruta / "servidor.json", {"schema": 1, "nombre": "Prueba", "tipo": "vanilla", "version_mc": "1.21.1",
                     "version_loader": "", "java_mayor": 21, "ram_mb": 1024, "acceso": "abierto", "reinicio_h": 2,
                     "apagar_si_vacio_min": 10, "hardcore": None, "copias": {"locales": 2, "sesion": 2, "diarias": 2}})
        (ruta / "world/playerdata").mkdir(parents=True)
        (ruta / "world/level.dat").write_bytes(b"mundo-original")
        (ruta / "server.properties").write_text("# comentario\nlevel-name=world\nonline-mode=false\nmotd=Con amigos\n", encoding="utf-8")
        self.s = self.b.servidor("prueba")

    def test_bloqueo_exclusivo_y_dueño(self):
        a, b = Sesion(self.b, "prueba"), Sesion(self.b, "otro")
        a.adquirir()
        with self.assertRaises(RuntimeError):
            b.adquirir()
        b.cerrar()
        self.assertTrue(self.b.lock.exists())
        a.cerrar()
        self.assertFalse(self.b.lock.exists())

    def test_rutas_fuera_del_servidor_rechazadas(self):
        with self.assertRaises(ValueError):
            self.b.servidor("../otro")
        propiedades.escribir(self.s.ruta / "server.properties", {"level-name": "../../fuera"})
        with self.assertRaises(ValueError):
            _ = self.s.mundo

    def test_copias_rotan_archivando_y_restauran(self):
        for _ in range(4):
            copia = copias.crear(self.s, "manual", False)
        self.assertEqual(len(list((self.b.raiz / "copias/prueba/locales").glob("*.zip"))), 2)
        self.assertEqual(len(list((self.b.raiz / "archivo/copias_rotadas/prueba").glob("*.zip"))), 2)
        (self.s.mundo / "level.dat").write_bytes(b"nuevo")
        copias.restaurar(self.s, copia)
        self.assertEqual((self.s.mundo / "level.dat").read_bytes(), b"mundo-original")
        self.assertTrue(list((self.b.raiz / "archivo/restaurados/prueba").glob("*/level.dat")))

    def test_copia_sin_mundo_no_rota_la_ultima(self):
        copia = copias.crear(self.s, "manual", False)
        (self.s.mundo / "level.dat").unlink()
        with self.assertRaises(ValueError):
            copias.crear(self.s, "manual", False)
        self.assertTrue(copia.exists())

    def test_zip_malicioso_no_toca_mundo(self):
        p = self.b.raiz / "mala.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("world/level.dat", b"falso")
            z.writestr("../escape", b"no")
        with self.assertRaises(ValueError):
            copias.restaurar(self.s, p)
        self.assertEqual((self.s.mundo / "level.dat").read_bytes(), b"mundo-original")

    def test_propiedades_conserva_comentarios_y_orden(self):
        propiedades.escribir(self.s.ruta / "server.properties", {"online-mode": True})
        texto = (self.s.ruta / "server.properties").read_text(encoding="utf-8")
        self.assertEqual(texto, "# comentario\nlevel-name=world\nonline-mode=true\nmotd=Con amigos\n")
        with self.assertRaises(ValueError):
            propiedades.escribir(self.s.ruta / "server.properties", {"motd": "a\nb"})

    def test_parser_jugadores_y_vacio(self):
        c = Consola()
        self.assertIsNone(c.vacio_desde)
        self.assertEqual(c.recibir("[Server thread/INFO]: Ejemplo joined the game")["tipo"], "entrada")
        c.recibir("[Server thread/INFO]: Ejemplo left the game")
        self.assertIsNotNone(c.vacio_desde)
        self.assertEqual(c.recibir("[Server thread/INFO]: [Ejemplo] LV_MUERTE_HARDCORE")["tipo"], "muerte")
        for i in range(5010):
            c.recibir(str(i))
        self.assertEqual(len(c.lineas), 5000)

    def test_migracion_ida_vuelta_y_fallo_sin_cambios(self):
        nick = "Ejemplo"
        viejo = mojang.offline(nick)
        nuevo = "11111111-2222-4333-8444-555555555555"
        guardar_json(self.s.ruta / "whitelist.json", [{"name": nick, "uuid": viejo}])
        personaje = self.s.mundo / "playerdata" / (viejo + ".dat")
        personaje.write_bytes(b"personaje")
        resolver = lambda n: {"name": n, "uuid": nuevo}
        mojang.migrar(self.s, "premium", resolver)
        self.assertEqual((personaje.with_name(nuevo + ".dat")).read_bytes(), b"personaje")
        mojang.migrar(self.s, "abierto", resolver)
        self.assertEqual(personaje.read_bytes(), b"personaje")
        with self.assertRaises(ValueError):
            mojang.migrar(self.s, "premium", lambda n: (_ for _ in ()).throw(ValueError("sin premium")))
        self.assertEqual(self.s.datos["acceso"], "abierto")

    def test_proceso_real_falso_cierra_con_copia_y_sin_lock(self):
        falso = self.b.raiz / "servidor_falso.py"
        falso.write_text("import sys\nprint('Done (0.1s)!',flush=True)\nfor l in sys.stdin:\n if l.strip()=='list':print('There are 0 of a max of 20 players online:',flush=True)\n if l.strip()=='stop':break\n", encoding="utf-8")
        eventos = []
        with patch.dict(os.environ, {"GESTOR_NO_PLAYIT": "1"}):
            c = Controlador(self.s, lambda t, d: eventos.append((t, d)), [sys.executable, "-B", str(falso)])
            c.iniciar()
            self.assertTrue(c.listo.wait(10))
            c.comando("list")
            c.parar(esperar=True, timeout=20)
        self.assertEqual(c.estado, "apagado")
        self.assertFalse(self.b.lock.exists())
        self.assertTrue(list((self.b.raiz / "copias/prueba/compartidas").glob("*sesion*.zip")))
        self.assertFalse(c.proceso.vivo)


if __name__ == "__main__":
    unittest.main()
