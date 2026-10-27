import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel,QPushButton
from telazocraft.app.qt_app import crear_app
from telazocraft.app.principal import MainWindow
from telazocraft.app.base import Dialogo,boton
from telazocraft.app.asistente import NuevoServidor
from telazocraft.app.busqueda_mods import BusquedaMods
from telazocraft.app.widgets.spin_box import ComboSinRueda
from telazocraft.app.marca import guardar_icono
from telazocraft.motor.biblioteca import Biblioteca
from telazocraft.motor.util import guardar_json

class Interfaz030Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=crear_app()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.b=Biblioteca(self.temp.name,crear=True)
        guardar_json(self.b.raiz/'servidores/ejemplo/servidor.json',{'schema':1,'nombre':'Ejemplo','tipo':'neoforge','version_mc':'1.21.1','version_loader':'21.1.233','java_mayor':21,'ram_mb':1024,'acceso':'abierto','hardcore':None})
        self.w=MainWindow(self.b,persistir=False);self.w.show();self.esperar()
    def esperar(self):
        for _ in range(100):
            QTest.qWait(10)
            if not self.w.resumen_cargando:break
    def hasta(self,predicado):
        for _ in range(200):
            self.app.processEvents();time.sleep(.005)
            if predicado():return
        self.fail('El trabajador no respondió')
    def tearDown(self):
        self.w._salir=True;self.w.close();self.w.deleteLater();self.app.processEvents();self.temp.cleanup()

    def test_icono_multirresolucion_y_appid(self):
        p=self.b.raiz/'app.ico';guardar_icono(p);data=p.read_bytes()
        self.assertEqual(struct.unpack_from('<HHH',data),(0,1,7))
        self.assertEqual([data[6+i*16] or 256 for i in range(7)],[16,24,32,48,64,128,256])
        raiz=Path(__file__).parents[2]
        self.assertIn('ItsRodryy.Telazocraft',(raiz/'installer/telazocraft.iss').read_text(encoding='utf-8'))
        if os.name=='nt':
            import ctypes
            valor=ctypes.c_wchar_p();self.assertEqual(ctypes.windll.shell32.GetCurrentProcessExplicitAppUserModelID(ctypes.byref(valor)),0)
            self.assertEqual(valor.value,'ItsRodryy.Telazocraft');ctypes.windll.ole32.CoTaskMemFree(valor)

    def test_controles_dinamicos_alturas_cursores_y_esquinas(self):
        d=Dialogo(self.w,'Prueba');combo=ComboSinRueda();combo.addItem('Ejemplo')
        b=boton('Nuevo',lambda:None);d.formulario.addWidget(combo);d.formulario.addWidget(b);d.show();QTest.qWait(30)
        self.assertEqual(b.height(),36);self.assertEqual(combo.height(),36)
        self.assertEqual(combo.cursor().shape(),Qt.PointingHandCursor)
        self.assertEqual(combo.view().viewport().cursor().shape(),Qt.PointingHandCursor)
        self.w.nav.setCurrentRow(2);self.app.processEvents();self.assertFalse(self.w.tabla_mods.mask().isEmpty())
        qss=self.app.styleSheet()
        for selector in ('QTabWidget::pane','QTableCornerButton::section','QToolTip','QComboBox QAbstractItemView'):
            bloque=qss.split(selector,1)[1].split('}',1)[0];self.assertIn('radius:',bloque)
        d.reject()

    def test_engrane_emergente_y_graficas_a_tres_partes(self):
        with patch.object(self.w,'refrescar_sistema'):self.w.gear.click()
        self.assertEqual(self.w.stack.count(),5);self.assertTrue(self.w.sistema_dialogo.isVisible());self.w.sistema_dialogo.reject()
        self.w.graficas_panel.show();self.app.processEvents()
        anchos=[g.width() for g in self.w.graficas]
        self.assertLessEqual(max(anchos)-min(anchos),2);self.assertGreater(min(anchos),150)

    def test_refresco_lento_no_bloquea_interfaz_y_no_repinta_otras_vistas(self):
        from telazocraft.app import resumen
        original=resumen.leer
        def lento(*args,**kwargs):time.sleep(.2);return original(*args,**kwargs)
        with patch.object(resumen,'leer',side_effect=lento),patch.object(self.w,'actualizar_mods') as mods:
            inicio=time.perf_counter();self.w.refrescar();duracion=time.perf_counter()-inicio
            self.assertLess(duracion,.08);self.assertTrue(self.w.resumen_cargando);mods.assert_not_called();self.esperar()

    def test_watcher_no_vigila_latest_y_progreso_verde(self):
        logs=self.w.servidor.ruta/'logs';logs.mkdir();(logs/'latest.log').write_text('log',encoding='utf-8');self.w.vigilar()
        self.assertNotIn(str(logs),self.w.watcher.directories());self.assertNotIn(str(logs/'latest.log'),self.w.watcher.files())
        self.w.evento(self.w.servidor.id,'progreso',{'valor':60,'texto':'Preparando mundo'})
        self.assertEqual(self.w.progreso_operacion.value(),60)
        from telazocraft.app import style
        bloque=self.app.styleSheet().split('QProgressBar::chunk',1)[1].split('}',1)[0]
        self.assertIn(style.tema_actual().ok,bloque)

    def test_asistente_red_simulada_error_visible_reintento_y_mas_nuevo(self):
        with patch('telazocraft.app.asistente.vanilla.versiones',side_effect=OSError('sin conexion')),patch('telazocraft.app.asistente.neoforge.versiones',return_value=['21.1.9','21.1.233']):
            d=NuevoServidor(self.w);d.show();self.hasta(lambda:bool(d.error_red.text()))
        self.assertIn('sin conexion',d.error_red.text());self.assertTrue(d.reintentar.isVisible())
        with patch('telazocraft.app.asistente.vanilla.versiones',return_value=[{'id':'1.21.1','type':'release'}]),patch('telazocraft.app.asistente.neoforge.versiones',return_value=['21.1.9','21.1.233','26.3.0.99']):
            d.reintentar.click();self.hasta(lambda:d.loader.currentData()=='21.1.233' and d.version.currentData()=='1.21.1')
        self.assertEqual(d.loader.currentData(),'21.1.233');self.assertFalse(d.version.isEditable());self.assertFalse(d.loader.isEditable())
        self.assertEqual(d.datos()['acceso'],'abierto');d.reject()

    def test_busqueda_antirrebote_descarta_consulta_anterior(self):
        buscador=BusquedaMods(self.w,lambda:self.w.servidor);datos=[];buscador.listo.connect(datos.append)
        with patch('telazocraft.app.busqueda_mods.modrinth.buscar',return_value=[{'title':'Ejemplo'}]) as buscar:
            buscador.cambiar('j');QTest.qWait(100);buscador.cambiar('ja');QTest.qWait(100);buscador.cambiar('jade');self.hasta(lambda:bool(datos))
        self.assertEqual(buscar.call_count,1);self.assertEqual(buscar.call_args.args[0],'jade');self.assertEqual(datos,[[{'title':'Ejemplo'}]])
        buscador.cambiar('otra');buscador.recibir(1,[{'title':'antigua'}],None);self.assertEqual(len(datos),1);buscador.timer.stop()

    def test_biblioteca_existente_no_ofrece_servidor_de_prueba(self):
        with patch('telazocraft.app.principal.confirmar') as confirmar:self.w.ofrecer_prueba()
        confirmar.assert_not_called()
