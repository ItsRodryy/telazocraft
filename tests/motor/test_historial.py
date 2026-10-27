import gzip
import tempfile
import unittest
from pathlib import Path
from telazocraft.motor.biblioteca import Biblioteca
from telazocraft.motor.util import guardar_json
from telazocraft.motor.historial import importar
from telazocraft.motor.diario import Diario
from telazocraft.motor.jugadores import conocidos


class HistorialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.b = Biblioteca(self.tmp.name, crear=True)
        guardar_json(self.b.ruta('servidores','ejemplo','servidor.json'),
                     {'schema':1,'nombre':'Ejemplo','tipo':'vanilla','version_mc':'26.3','ram_mb':1024,'acceso':'abierto'})
        self.s = self.b.servidor('ejemplo')
        (self.s.ruta/'logs').mkdir()

    def test_neoforge_gzip_y_union_de_nick_idempotente(self):
        with gzip.open(self.s.ruta/'logs/2026-07-06-1.log.gz','wt',encoding='utf-8') as f:
            f.write('[06jul2026 20:10:00.123] [Server thread/INFO] [server/]: Alex joined the game\n'
                    '[06jul2026 22:10:00.555] [Server thread/INFO] [server/]: Alex left the game\n')
        guardar_json(self.s.ruta/'whitelist.json',[{'name':'Alex','uuid':'nuevo'}])
        guardar_json(self.s.ruta/'usercache.json',[{'name':'alex','uuid':'antiguo'}])
        self.assertEqual(importar(self.s),1)
        antes=(self.s.ruta/'sesiones.jsonl').read_bytes()
        self.assertEqual(importar(self.s),0)
        self.assertEqual(antes,(self.s.ruta/'sesiones.jsonl').read_bytes())
        datos=conocidos(self.s)
        self.assertEqual(len(datos),1)
        self.assertEqual(datos[0]['horas'],2)

    def test_vanilla_sin_salida_cierra_en_parada_y_cruza_medianoche(self):
        (self.s.ruta/'logs/2026-10-26-1.log').write_text(
            '[23:30:00] [Server thread/INFO]: Sam joined the game\n'
            '[00:30:00] [Server thread/INFO]: Stopping server\n',encoding='utf-8')
        self.assertEqual(importar(self.s),1)
        self.assertEqual(Diario(self.s).leer()[-1]['duracion_seg'],3600)

    def test_sesion_abierta_cierra_en_fin_del_log_y_copias_no_duplican(self):
        texto=('[20:00:00] [Server thread/INFO]: Sam joined the game\n'
               '[21:15:00] [Server thread/INFO]: Saving chunks\n')
        for name in ('2026-10-26-1.log','2026-10-26-2.log'):
            (self.s.ruta/'logs'/name).write_text(texto,encoding='utf-8')
        self.assertEqual(importar(self.s),1)
        self.assertEqual(Diario(self.s).leer()[-1]['duracion_seg'],4500)

    def test_no_reimporta_entrada_registrada_por_la_app(self):
        (self.s.ruta/'logs/2026-10-26-1.log').write_text(
            '[20:00:00] [Server thread/INFO]: Sam joined the game\n'
            '[21:00:00] [Server thread/INFO]: Sam left the game\n',encoding='utf-8')
        from telazocraft.motor.historial import zona_local
        import datetime as dt,json
        fecha=dt.datetime(2026,10,26,20,tzinfo=zona_local()).astimezone(dt.timezone.utc).isoformat()
        (self.s.ruta/'sesiones.jsonl').write_text(json.dumps({'tipo':'entrada','jugador':'Sam','fecha':fecha})+'\n',encoding='utf-8')
        self.assertEqual(importar(self.s),0)
