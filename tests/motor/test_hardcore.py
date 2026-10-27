import json
import time
import unittest
import zipfile
from unittest.mock import patch
from . import test_motor
from telazocraft.motor.hardcore import Hardcore, preparar, formato_datos


class HardcoreTests(unittest.TestCase):
    setUp = test_motor.MotorTests.setUp

    def test_formato_real_26_y_legacy(self):
        for pack, esperado in (({"data_major": 121, "data_minor": 0}, 121), ({"data": 48}, 48), ({"data": {"major": 121, "minor": 0}}, 121)):
            with zipfile.ZipFile(self.s.ruta / "server.jar", "w") as z:
                z.writestr("version.json", json.dumps({"pack_version": pack}))
            self.assertEqual(formato_datos(self.s), esperado)

    def test_gracia_parser_y_partida_archivada_sin_destruir(self):
        self.s.datos["hardcore"] = {"gracia_seg": 30, "partidas_guardadas": 3}
        with zipfile.ZipFile(self.s.ruta / "server.jar", "w") as z:
            z.writestr("version.json", json.dumps({"pack_version": {"data_major": 121}}))
        enviados = []
        h = Hardcore(self.s, enviados.append)
        h.marcador.write_text("1", encoding="utf-8")
        h.entrada()
        self.assertTrue(h.gracia)
        h.tick()
        self.assertTrue(any("resistance" in e for e in enviados))
        h.muerte("Ejemplo")
        self.assertIsNone(h.muerto)
        h.fin = time.monotonic() - 1
        h.tick()
        self.assertFalse(h.marcador.exists())
        h.muerte("Ejemplo")
        self.assertEqual(h.muerto, "Ejemplo")
        semilla = h.nueva_partida()
        self.assertIsInstance(semilla, int)
        self.assertTrue(list((self.b.raiz / "copias/prueba/partidas").glob("*.zip")))
        archivado = list((self.b.raiz / "archivo/partidas/prueba").glob("*/level.dat"))
        self.assertEqual(archivado[0].read_bytes(), b"mundo-original")

    def test_fallo_copia_no_aparta_ni_sustituye_mundo(self):
        self.s.datos["hardcore"] = {"gracia_seg": 30}
        h = Hardcore(self.s, lambda c: None)
        with patch("telazocraft.motor.copias.crear", side_effect=OSError("disco lleno")):
            with self.assertRaises(OSError):
                h.nueva_partida()
        self.assertEqual((self.s.mundo / "level.dat").read_bytes(), b"mundo-original")
