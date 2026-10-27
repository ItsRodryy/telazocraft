import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QSpinBox, QComboBox, QCheckBox, QSlider
from telazocraft.app.qt_app import crear_app
from telazocraft.app.principal import MainWindow
from telazocraft.app import style, icons
from telazocraft.app.base import Dialogo
from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QFontDatabase
from telazocraft.motor.biblioteca import Biblioteca
from telazocraft.motor.util import guardar_json


class DisenoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = crear_app()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.b = Biblioteca(self.temp.name, crear=True)
        guardar_json(self.b.raiz / "servidores/ejemplo/servidor.json", {"schema": 1, "nombre": "Servidor de ejemplo",
                     "tipo": "neoforge", "version_mc": "1.21.1", "version_loader": "21.1.233", "java_mayor": 21,
                     "ram_mb": 1024, "acceso": "abierto", "hardcore": None})
        self.w = MainWindow(self.b, persistir=False)
        self.w.resize(1080, 720)
        self.w.show()
        self.app.processEvents()
        self.esperar_resumen()
        self.w.cargar_ajustes()

    def esperar_resumen(self):
        from PySide6.QtTest import QTest
        for _ in range(200):
            QTest.qWait(10)
            if not self.w.resumen_cargando:break
        self.assertFalse(self.w.resumen_cargando)

    def tearDown(self):
        self.w._salir = True
        self.w.close()
        self.w.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_paginas_sin_agrupadores_opacos(self):
        # Adaptación de _con_fondo de test_agrupadores de vision_driver.
        for indice in range(self.w.nav.count()):
            self.w.nav.setCurrentRow(indice)
            self.app.processEvents()
            for widget in self.w.findChildren(QWidget):
                if type(widget) is not QWidget or not widget.isVisible() or widget.objectName().startswith("qt_"):
                    continue
                padre = widget.parentWidget()
                while padre:
                    if isinstance(padre, QFrame) and padre.objectName() in ("panel", "panelSuave", "params", "topbar"):
                        self.assertIn(widget.objectName(), style.AGRUPADORES)
                        break
                    padre = padre.parentWidget()

    def test_controles_propios(self):
        for clase in (QPushButton, QSpinBox, QComboBox, QCheckBox, QSlider):
            for w in self.w.findChildren(clase):
                self.assertNotEqual(type(w), clase, f"Control sin adaptar: {clase.__name__}")

    def test_barra_estable_y_sin_recortes(self):
        anterior = self.w.selector.width()
        for texto in ("Apagado", "Arrancando", "Copiando", "Encendido"):
            self.w.estado.setText(texto)
            self.app.processEvents()
            self.assertEqual(self.w.selector.width(), anterior)
        for b in (self.w.iniciar_boton, self.w.parar_boton, self.w.reiniciar_boton):
            self.assertGreaterEqual(b.width(), b.minimumSizeHint().width())
            self.assertGreaterEqual(b.height(), b.minimumSizeHint().height())

    def test_logo_vectorial_y_contraste(self):
        self.assertTrue(QFontDatabase.families(), "No hay fuentes disponibles para la interfaz")
        self.assertFalse(icons.app_icon().isNull())
        t = style.tema_actual()
        self.assertGreater(style.contraste(t.texto, t.fondo), 4.5)

    def test_editor_numerico_visible_y_sondeo_solo_en_su_pantalla(self):
        self.w.nav.setCurrentRow(self.w.VISTAS.index("Ajustes"))
        self.app.processEvents()
        # El editor de Chunky está dentro del scroll de Mundo.
        self.assertGreater(self.w.radio_chunky.width(), 100)
        c = Mock()
        c.estado = 'encendido'
        c.consola.lista_numero = 0
        c.consola.jugadores=set();c.consola.entradas={}
        self.w.controles[self.w.selector.currentData()] = c
        self.w.nav.setCurrentRow(self.w.VISTAS.index("Inicio"))
        self.app.processEvents()
        self.assertTrue(self.w.timer_metricas.isActive())
        self.w.nav.setCurrentRow(self.w.VISTAS.index("Mods"))
        self.app.processEvents()
        self.assertFalse(self.w.timer_metricas.isActive())

    def test_log_acotado_y_comandos_con_historial(self):
        self.w.mini_comando.setText("list")
        self.assertEqual(self.w.mini_comando.recordar(), "list")
        self.assertEqual(self.w.mini_comando.historial, ["list"])
        self.w.log.setPlainText("\n".join(str(i) for i in range(5100)))
        self.assertEqual(self.w.log.document().blockCount(), 5000)

    def test_segundo_arranque_conserva_control_de_la_sesion(self):
        control = Mock()
        control.hilo.is_alive.return_value = True
        id = self.w.selector.currentData()
        self.w.controles[id] = control
        self.w.iniciar()
        self.assertIs(self.w.controles[id], control)
        self.assertEqual(self.w.trabajos, 0)

    def test_dialogo_cierra_sin_dependencias_de_otra_aplicacion(self):
        d = Dialogo(self.w, "Confirmación")
        d.show()
        self.app.processEvents()
        d.done(QDialog.Accepted)
        self.assertEqual(d.result(), QDialog.Accepted)
        self.assertFalse(d.isVisible())

    def test_ajustes_pendientes_se_conservan_al_cambiar_de_pantalla(self):
        self.w.nav.setCurrentRow(self.w.VISTAS.index("Ajustes"))
        self.w.ajustes_campos["ram_mb"].setValue(2048)
        self.w.nav.setCurrentRow(self.w.VISTAS.index("Inicio"))
        self.w.nav.setCurrentRow(self.w.VISTAS.index("Ajustes"))
        self.assertEqual(self.w.ajustes_campos["ram_mb"].value(), 2048)
        self.w.restablecer_ajustes()
        self.assertEqual(self.w.ajustes_campos["ram_mb"].value(), 1024)
        self.assertFalse(self.w.borradores)

    def test_navegacion_compacta_cinco_pantallas_y_engranaje(self):
        self.assertEqual(self.w.nav.count(), 5)
        self.assertEqual(self.w.VISTAS[:5], ('Inicio','Jugadores','Mods','Copias','Ajustes'))
        self.w.resize(1000,700)
        self.app.processEvents()
        self.assertLess(self.w.lateral.width(),100)
        for i in range(5):
            self.assertEqual(self.w.nav.item(i).text(),'')
            self.assertTrue(self.w.nav.item(i).toolTip())
        self.w.resize(1400,900)
        self.app.processEvents()
        self.assertEqual(self.w.nav.item(0).text(),'Inicio')

    def test_mods_y_jugadores_cargan_solos_y_watcher_se_rearma(self):
        import zipfile
        s=self.w.servidor
        (s.ruta/'mods').mkdir()
        with zipfile.ZipFile(s.ruta/'mods/ejemplo.jar','w') as z:z.writestr('mod.txt','ejemplo')
        guardar_json(s.ruta/'whitelist.json',[{'name':'Alex','uuid':'ejemplo'}])
        self.w.refrescar()
        self.esperar_resumen()
        self.w.nav.setCurrentRow(2)
        self.assertEqual(self.w.tabla_mods.rowCount(),1)
        self.w.nav.setCurrentRow(1)
        self.assertEqual(self.w.tabla_jugadores.rowCount(),1)
        self.assertIn(str(s.ruta/'mods'),self.w.watcher.directories())
        self.assertFalse(self.w.controles)

    def test_cancelar_mod_ajustes_jugador_y_copia_no_escribe(self):
        s=self.w.servidor
        guardar_json(s.ruta/'whitelist.json',[])
        antes={str(p.relative_to(s.ruta)):p.read_bytes() for p in s.ruta.rglob('*') if p.is_file()}
        with patch('telazocraft.app.gestion.confirmar',return_value=False) as confirmar, patch('telazocraft.app.mods.confirmar',return_value=False):
            self.w.ajustes_campos['ram_mb'].setValue(2048)
            self.w.aplicar_ajustes()
            self.assertTrue(confirmar.call_args.args[3])
            self.w.accion_jugador('whitelist add','Alex')
            self.w.restaurar_copia(Path(self.temp.name)/'ejemplo.zip')
            self.w._agregar_jars([Path(self.temp.name)/'mod.jar'])
        despues={str(p.relative_to(s.ruta)):p.read_bytes() for p in s.ruta.rglob('*') if p.is_file()}
        self.assertEqual(antes,despues)

    def test_consola_recuerda_estado_y_altura(self):
        self.w.persistir=True
        with patch('telazocraft.app.principal.ajustes.guardar') as guardar:
            self.w.alternar_consola(True)
            self.app.processEvents()
            self.w.guardar_ventana()
            prefs=guardar.call_args.args[0]
            self.assertTrue(prefs['consola_abierta'])
            self.assertGreater(prefs['consola_alto'],100)
            self.w.alternar_consola(False)
            self.w.guardar_ventana()
            self.assertFalse(guardar.call_args.args[0]['consola_abierta'])
        self.w.persistir=False

    def test_pestana_consola_responde_al_clic_y_engrane_permite_volver(self):
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        self.assertFalse(self.w.plegar.isChecked())
        QTest.mouseClick(self.w.plegar,Qt.LeftButton)
        self.assertTrue(self.w.plegar.isChecked())
        self.assertTrue(self.w.mini_contenido.isVisible())
        with patch.object(self.w,'refrescar_sistema'):
            self.w.gear.click()
        self.assertEqual(self.w.stack.currentIndex(),0)
        self.assertTrue(self.w.sistema_dialogo.isVisible())
        self.w.sistema_dialogo.reject()
        self.w.nav.setCurrentRow(0)
        self.assertEqual(self.w.stack.currentIndex(),0)

    def test_consola_plegada_reserva_espacio_para_el_ultimo_mensaje(self):
        self.w.alternar_consola(False)
        self.w.ultimo_log.setText('Mensaje de prueba '*40)
        self.app.processEvents()
        self.assertTrue(self.w.ultimo_log.isVisible())
        self.assertGreater(self.w.ultimo_log.width(),300)
        self.assertIn('Mensaje de prueba',self.w.ultimo_log.toolTip())

    def test_watcher_refresca_un_jar_sin_accion_manual(self):
        import zipfile
        from PySide6.QtTest import QTest
        s=self.w.servidor
        (s.ruta/'mods').mkdir()
        self.w.vigilar()
        with zipfile.ZipFile(s.ruta/'mods/nuevo.jar','w') as z:z.writestr('info','nuevo')
        QTest.qWait(750)
        self.esperar_resumen()
        self.w.nav.setCurrentRow(2)
        self.assertEqual(self.w.tabla_mods.rowCount(),1)

    def test_confirmacion_muestra_diferencias_y_cancelar_es_predeterminado(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication,QLabel
        from telazocraft.app.base import confirmar
        vistos=[]
        def cancelar():
            d=QApplication.activeModalWidget()
            textos=[w.text() for w in d.findChildren(QLabel)]
            vistos.append(any('1024 → 2048' in t for t in textos))
            vistos.append(any(b.isDefault() and b.text()=='Cancelar' for b in d.findChildren(QPushButton)))
            d.reject()
        QTimer.singleShot(10,cancelar)
        self.assertFalse(confirmar(self.w,'Cambio de memoria','Aplicar',[('RAM',1024,2048)],True))
        self.assertEqual(vistos,[True,True])

    def test_aplicar_ajustes_confirmados_guarda_valores_y_limpia_borrador(self):
        from PySide6.QtTest import QTest
        s=self.w.servidor
        self.w.ajustes_campos['ram_mb'].setValue(2048)
        self.w.ajustes_campos['nombre'].setText('Nombre cambiado')
        with patch('telazocraft.app.gestion.confirmar',return_value=True):self.w.aplicar_ajustes()
        for _ in range(100):
            if not self.w.trabajos:break
            QTest.qWait(20)
        s.recargar()
        self.assertEqual(s.nombre,'Nombre cambiado')
        self.assertEqual(s.datos['ram_mb'],2048)
        self.assertFalse(self.w.borradores)
        self.assertFalse((s.ruta/'server.properties').read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_asistente_cinco_pasos_cancelar_no_crea_servidor(self):
        from telazocraft.app.asistente import NuevoServidor
        d=NuevoServidor(self.w,red=False)
        self.assertEqual(d.stack.count(),5)
        d.tipo.setCurrentIndex(1)
        d.mover(1); d.mover(1)
        d.nombre.setText('Mundo de ejemplo')
        d.mover(1); d.mover(1)
        self.assertEqual(d.indice,4)
        d.reject()
        self.assertEqual(len(self.b.servidores()),1)

    def test_copiar_plantilla_muestra_sus_versiones_reales(self):
        from telazocraft.app.asistente import NuevoServidor
        d=NuevoServidor(self.w,red=False)
        d.tipo.setCurrentIndex(2)
        self.assertEqual(d.version.currentText(),'1.21.1')
        self.assertEqual(d.loader.currentText(),'21.1.233')
        self.assertFalse(d.version.isEnabled())
        d.reject()


if __name__ == "__main__":
    unittest.main()
