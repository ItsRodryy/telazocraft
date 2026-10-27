import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from telazocraft.motor.biblioteca import Biblioteca
from telazocraft.motor.util import guardar_json
from telazocraft.motor import exportaciones,historial
from telazocraft.motor.tiempos import sesiones_jugadores,horas_encendido
from telazocraft.motor.controlador import Controlador

class Version030Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.b=Biblioteca(self.temp.name,crear=True)
        guardar_json(self.b.raiz/'servidores/ejemplo/servidor.json',{'schema':1,'nombre':'Ejemplo','tipo':'vanilla','version_mc':'1.21.1','version_loader':'','java_mayor':21,'ram_mb':1024,'acceso':'abierto','extras_cliente':[],'hardcore':None})
        self.s=self.b.servidor('ejemplo')

    def test_horas_globales_solapadas_y_sesion_viva(self):
        registros=[{'tipo':'salida','jugador':'Alex','fecha':'2026-01-01T02:00:00+00:00','duracion_seg':7200},
                   {'tipo':'salida','jugador':'alex','fecha':'2026-01-01T02:00:00+00:00','duracion_seg':3600}]
        ahora=dt.datetime(2026,1,1,3,tzinfo=dt.timezone.utc).timestamp()
        horas,vivas=sesiones_jugadores(registros,['Alex'],{'Alex':ahora-1800},ahora)
        self.assertEqual(horas['alex'],2.5);self.assertEqual(vivas[0]['duracion_seg'],1800)

    def test_encendido_diario_logs_sin_duplicar_y_actual(self):
        r=[{'tipo':'arranque','fecha':'2026-01-01T00:00:00+00:00'},
           {'tipo':'encendido_log','fecha':'2026-01-01T02:00:00+00:00','duracion_seg':7200},
           {'tipo':'parada','fecha':'2026-01-01T02:00:00+00:00'},
           {'tipo':'arranque','fecha':'2026-01-01T03:00:00+00:00'}]
        self.assertEqual(horas_encendido(r,True,dt.datetime(2026,1,1,4,tzinfo=dt.timezone.utc).timestamp()),3)

    def test_importacion_encendido_idempotente_y_latest_abierto(self):
        logs=self.s.ruta/'logs';logs.mkdir()
        (logs/'2026-01-01-1.log').write_text('[10:00:00] [Server thread/INFO]: Starting minecraft server\n[11:00:00] [Server thread/INFO]: Stopping server\n',encoding='utf-8')
        (logs/'latest.log').write_text('[10:00:00] [Server thread/INFO]: Alex joined the game\n[11:00:00] [Server thread/INFO]: Tick\n',encoding='utf-8')
        historial.importar(self.s);antes=(self.s.ruta/'sesiones.jsonl').read_bytes();historial.importar(self.s)
        self.assertEqual(antes,(self.s.ruta/'sesiones.jsonl').read_bytes())
        rows=[json.loads(l) for l in antes.splitlines()]
        self.assertEqual([r['duracion_seg'] for r in rows if r['tipo']=='encendido_log'],[3600])
        self.assertFalse(any(r['tipo']=='salida' for r in rows))

    def test_progreso_arranque_procede_del_log(self):
        eventos=[];c=Controlador(self.s,lambda t,d:eventos.append((t,d)));c._estado('arrancando')
        c._linea('[Server thread/INFO]: Preparing level "world"')
        self.assertEqual([d['valor'] for t,d in eventos if t=='progreso'],[5,65])
        self.assertIsNone(c.proceso.proc)

    def test_paquete_vanilla_con_bloqueo_no_modifica_servidor(self):
        self.b.lock.write_text('otra sesion',encoding='utf-8')
        antes={p.name:p.read_bytes() for p in self.s.ruta.iterdir() if p.is_file()};progreso=[]
        p,_=exportaciones.crear(self.s,lambda n,t:progreso.append(n))
        with zipfile.ZipFile(p) as z:
            self.assertIsNone(z.testzip());self.assertIn('Instalar.bat',z.namelist())
            self.assertFalse(any(n.endswith('.jar') for n in z.namelist()))
        self.assertEqual(antes,{p.name:p.read_bytes() for p in self.s.ruta.iterdir() if p.is_file()})
        self.assertEqual(progreso[-1],100)

    def test_paquete_neoforge_filtra_mods_y_verifica_instalador(self):
        self.s.datos.update(tipo='neoforge',version_loader='21.1.233');mods=self.s.ruta/'mods';mods.mkdir()
        for n in ('cliente.jar','servidor.jar'):(mods/n).write_bytes(n.encode())
        inventario=[{'archivo':'cliente.jar','lado':'required','proyecto':'a'},{'archivo':'servidor.jar','lado':'unsupported','proyecto':'b'}]
        jar=self.b.raiz/'neoforge-21.1.233-installer.jar';jar.write_bytes(b'instalador')
        with patch.object(exportaciones.modrinth,'inventario',return_value=inventario),patch.object(exportaciones.neoforge,'instalador',return_value=jar):
            p,datos=exportaciones.crear(self.s)
        with zipfile.ZipFile(p) as z:
            self.assertIn('mods/cliente.jar',z.namelist());self.assertNotIn('mods/servidor.jar',z.namelist())
            meta=json.loads(z.read('paquete.json'));self.assertEqual(meta['sha256_instalador'],hashlib.sha256(b'instalador').hexdigest())
        self.assertEqual(datos['excluidos'],1)

    def test_rotacion_conserva_tres_y_archiva_el_resto(self):
        for _ in range(4):exportaciones.crear(self.s)
        self.assertEqual(len(list(self.b.ruta('exportaciones',self.s.id).glob('Paquete_*.zip'))),3)
        self.assertEqual(len(list(self.b.ruta('archivo','exportaciones',self.s.id).glob('*.zip'))),1)

    @unittest.skipUnless(os.name=='nt','Instalador Windows')
    def test_bat_appdata_falso_preserva_mods_mundos_y_rechaza_corrupcion(self):
        self.s.datos.update(tipo='neoforge',version_loader='21.1.233')
        mods=self.s.ruta/'mods';mods.mkdir();(mods/'nuevo.jar').write_bytes(b'mod nuevo')
        with patch.object(exportaciones.modrinth,'inventario',return_value=[{'archivo':'nuevo.jar','lado':'required','proyecto':'a'}]),patch.object(exportaciones.neoforge,'instalador',return_value=None):
            p,_=exportaciones.crear(self.s)
        extraido=self.b.raiz/'paquete con espacios'
        with zipfile.ZipFile(p) as z:z.extractall(extraido)
        appdata=self.b.raiz/'appdata falso';juego=appdata/'.minecraft';(juego/'mods').mkdir(parents=True)
        (juego/'mods/anterior.jar').write_bytes(b'anterior');(juego/'saves').mkdir();(juego/'saves/mundo').write_bytes(b'mundo')
        env={**os.environ,'APPDATA':str(appdata),'TELAZOCRAFT_SIN_PAUSA':'1','PSModulePath':str(self.b.raiz/'sin modulos')}
        r=subprocess.run(['cmd.exe','/d','/c',str(extraido/'Instalar.bat')],cwd=extraido,env=env,capture_output=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stdout.decode(errors='replace'))
        self.assertEqual((juego/'mods/nuevo.jar').read_bytes(),b'mod nuevo')
        self.assertEqual(len(list(juego.glob('mods_anterior_*/anterior.jar'))),1)
        self.assertEqual((juego/'saves/mundo').read_bytes(),b'mundo')
        (extraido/'mods/nuevo.jar').write_bytes(b'corrupto')
        r=subprocess.run(['cmd.exe','/d','/c',str(extraido/'Instalar.bat')],cwd=extraido,env=env,capture_output=True,timeout=30)
        self.assertEqual(r.returncode,1);self.assertEqual((juego/'mods/nuevo.jar').read_bytes(),b'mod nuevo')
