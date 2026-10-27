import json
import os
import threading
import logging
import time
from pathlib import Path
from PySide6.QtCore import Qt, QEvent, QTimer, QLockFile, QFileSystemWatcher, QSize
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import (QApplication, QFileDialog, QLabel, QLineEdit, QListWidget, QMainWindow,
                               QMenu, QScrollArea, QSplitter, QStackedWidget, QSystemTrayIcon,
                               QVBoxLayout, QHBoxLayout, QWidget, QListWidgetItem, QProgressBar)
from . import style, icons
from .base import Bus, Comando, Log, boton, fila, titulo, confirmar
from .qt_app import crear_app
from .widgets.spin_box import ComboSinRueda
from .widgets.check_box import CheckBox
from .widgets.estado_punto import PuntoEstado
from .widgets.boton_carpeta import BotonCarpeta, abrir_carpeta
from .mods import PantallasMods
from .gestion import PantallasGestion
from .asistente import PantallaAsistente
from .. import __version__
from ..common import ajustes
from ..common import github_releases
from ..tools import actualizador
from ..common.i18n import tr
from ..motor.biblioteca import Biblioteca
from ..motor.controlador import Controlador
from ..motor.sync import GuardiaSync
from ..motor import java
from ..motor.util import leer_json, guardar_json


from .widgets.etiqueta_elidida import EtiquetaElidida
from ..motor.historial import importar


class AvisoTemporal(QLabel):
    """Línea de mensajes bajo la consola: solo ocupa sitio mientras hay algo que decir y se borra
    sola a los 8 s, salvo «Trabajando…», que dura hasta que termina la operación."""
    def __init__(self):
        super().__init__();self.setObjectName("tenue");self.setWordWrap(True);self.hide()
        self._timer=QTimer(self);self._timer.setSingleShot(True);self._timer.setInterval(8000);self._timer.timeout.connect(lambda:self.setText(""))
    def setText(self,texto):
        super().setText(texto);self.setVisible(bool(texto))
        if texto and texto!=tr("Trabajando…"):self._timer.start()
        else:self._timer.stop()

class MainWindow(PantallasMods, PantallasGestion, PantallaAsistente, QMainWindow):
    VISTAS = ("Inicio", "Jugadores", "Mods", "Copias", "Ajustes")

    def __init__(self, biblioteca, persistir=True):
        super().__init__()
        self.biblioteca, self.persistir = biblioteca, persistir
        self.prefs = ajustes.cargar() if persistir else {}
        self.controles, self.paginas = {}, {}
        self.trabajos = 0
        self.resumenes={};self.resumen_cargando=set();self.resumen_pendiente=set();self.logs_importados=set();self.lectores=[]
        self._salir = False
        self.bus = Bus(self)
        self.bus.evento.connect(self.evento)
        self.bus.resultado.connect(self._resultado)
        self.bus.resumen.connect(self.recibir_resumen)
        self.setWindowTitle(tr("Telazocraft"))
        self.setWindowIcon(icons.app_icon())
        self.setMinimumSize(900, 600)
        self.resize(self.prefs.get("ancho", 1400), self.prefs.get("alto", 900))
        contenedor = style.agrupador(); contenedor.setObjectName("central")
        self.setCentralWidget(contenedor)
        caja = QVBoxLayout(contenedor)
        caja.setContentsMargins(12, 12, 12, 12)
        caja.setSpacing(style.SEPARACION_PANELES)
        self.selector = ComboSinRueda(); self.selector.setFixedWidth(230)
        self.selector.currentIndexChanged.connect(self.cambiar_servidor)
        self.estado = QLabel(tr("Apagado")); self.estado.setFixedWidth(95)
        self.punto_estado=PuntoEstado()
        self.iniciar_boton = boton("Iniciar", self.iniciar, rol="ok")
        self.parar_boton = boton("Parar", self.parar, rol="peligro")
        self.reiniciar_boton = boton("Reiniciar", self.reiniciar, rol="aviso")
        logo = QLabel(); logo.setPixmap(icons.logo_pixmap(36))
        nuevo = boton("", self.nuevo_servidor); nuevo.setIcon(icons.glifo("mas",18)); nuevo.setToolTip(tr("Nuevo servidor")); nuevo.setAccessibleName(tr("Nuevo servidor")); nuevo.setFixedWidth(40)
        barra = fila(logo, self.selector, nuevo, self.punto_estado, self.estado, self.iniciar_boton, self.parar_boton, self.reiniciar_boton)
        caja.addWidget(style.tarjeta(barra))
        self.splitter = QSplitter(Qt.Vertical)
        cuerpo = style.agrupador(); h = QHBoxLayout(cuerpo); h.setContentsMargins(0,0,0,0); h.setSpacing(style.SEPARACION_PANELES)
        self.nav = QListWidget(); self.nav.setIconSize(QSize(22,22)); self.nav.setSpacing(5)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav.setFrameShape(QListWidget.NoFrame)
        for nombre in self.VISTAS[:5]:
            item = QListWidgetItem(icons.glifo(nombre.lower(),22), tr(nombre)); item.setToolTip(tr(nombre)); item.setSizeHint(QSize(140,48)); self.nav.addItem(item)
        self.nav.currentRowChanged.connect(self.cambiar_vista)
        self.gear = boton("Telazocraft", self.abrir_sistema); self.gear.setIcon(icons.glifo("engranaje",22)); self.gear.setToolTip(tr("Telazocraft"))
        self.lateral = style.tarjeta(self.nav, self.gear)
        self.stack = QStackedWidget(); self.stack.setObjectName("stack")
        h.addWidget(self.lateral); h.addWidget(self.stack,1)
        for nombre in self.VISTAS:
            pagina = style.agrupador(); layout=QVBoxLayout(pagina);layout.setContentsMargins(0,0,0,0);layout.setSpacing(style.SEPARACION_PANELES)
            self.stack.addWidget(pagina); self.paginas[nombre]=pagina
        self.splitter.addWidget(cuerpo)
        self.construir_consola()
        self.splitter.addWidget(self.consola_panel); self.splitter.setStretchFactor(0,1)
        self.splitter.splitterMoved.connect(self.recordar_altura_consola)
        caja.addWidget(self.splitter,1)
        self.aviso=AvisoTemporal();caja.addWidget(self.aviso)
        self.progreso_operacion=QProgressBar();self.progreso_operacion.hide();caja.addWidget(self.progreso_operacion)
        self.ocultar_progreso=QTimer(self);self.ocultar_progreso.setSingleShot(True);self.ocultar_progreso.timeout.connect(self.progreso_operacion.hide)
        self.construir_gestion(); self.construir_mods(); self.construir_sistema(); self.crear_bandeja()
        self.watcher = QFileSystemWatcher(self)
        self.debounce = QTimer(self); self.debounce.setSingleShot(True); self.debounce.setInterval(350); self.debounce.timeout.connect(self.refrescar)
        self.watcher.directoryChanged.connect(self.cambio_archivo)
        self.watcher.fileChanged.connect(self.cambio_archivo)
        self.timer_estado=QTimer(self);self.timer_estado.setInterval(1000);self.timer_estado.timeout.connect(self.actualizar_estado);self.timer_estado.start()
        self.recargar_servidores();self.nav.setCurrentRow(0);self.ajustar_lateral()
        from .interaction import aplicar_cursores_interactivos
        aplicar_cursores_interactivos(self)
        QApplication.instance().commitDataRequest.connect(self.apagado_windows)

    @property
    def servidor(self):
        id = self.selector.currentData()
        return self.biblioteca.servidor(id) if id else None

    @property
    def control(self):
        return self.controles.get(self.selector.currentData())

    def recargar_servidores(self):
        anterior=self.selector.currentData() or self.prefs.get("ultimo_servidor")
        self.selector.blockSignals(True);self.selector.clear()
        for s in self.biblioteca.servidores():self.selector.addItem(icons.glifo("servidor",18),s.nombre,s.id)
        i=self.selector.findData(anterior)
        if i>=0:self.selector.setCurrentIndex(i)
        self.selector.blockSignals(False);self.cambiar_servidor()

    def vigilar(self):
        paths=[str(self.biblioteca.raiz/'servidores')]
        if self.servidor:
            s=self.servidor
            paths += [str(s.ruta),str(s.ruta/'mods'),str(s.ruta/'sesiones.jsonl')]
            carpeta=self.biblioteca.ruta('copias',s.id)
            if carpeta.exists():paths += [str(carpeta)]+[str(p) for p in carpeta.iterdir() if p.is_dir()]
        actuales=self.watcher.directories()+self.watcher.files()
        if actuales:self.watcher.removePaths(actuales)
        self.watcher.addPaths([p for p in paths if Path(p).exists()])

    def cambiar_servidor(self,*_):
        if not hasattr(self,'borradores'):return
        self.log.clear()
        if self.control:
            for linea in self.control.consola.lineas:self.log.agregar(linea)
        self.ultimo_log.setText(tr("Sin mensajes de esta sesión"))
        self.mods_updates={};self.mods_datos=[]
        if self.servidor:
            self.prefs['ultimo_servidor']=self.servidor.id
        self.refrescar()

    def refrescar(self):
        if self.trabajos:
            self.debounce.start();return
        ids=[s.id for s in self.biblioteca.servidores()]
        if ids != [self.selector.itemData(i) for i in range(self.selector.count())]:
            self.recargar_servidores();return
        self.pintar_visible();self.vigilar();self.actualizar_estado();self.pedir_resumen()

    def cambio_archivo(self,*_):
        self.debounce.start()

    def pedir_resumen(self):
        from .resumen import leer
        s=self.servidor
        if not s:return
        if s.id in self.resumen_cargando:self.resumen_pendiente.add(s.id);return
        id=s.id;cache=self.cache_mods(s);anterior=self.resumenes.get(id)
        clave=str(s.biblioteca.raiz)+'|'+id
        importar_logs=id not in self.logs_importados
        self.resumen_cargando.add(id)
        def hacer():
            try:self.bus.resumen.emit(clave,leer(s,cache,anterior,importar_logs),None)
            except Exception as exc:
                logging.getLogger(__name__).exception('No se pudo leer el resumen')
                try:self.bus.resumen.emit(clave,None,str(exc))
                except RuntimeError:pass
        hilo=threading.Thread(target=hacer,daemon=True);self.lectores=[h for h in self.lectores if h.is_alive()];self.lectores.append(hilo);hilo.start()

    def recibir_resumen(self,clave,datos,error):
        origen,id=clave.rsplit('|',1)
        if origen!=str(self.biblioteca.raiz):return
        self.resumen_cargando.discard(id)
        if error:self.mostrar_error(error);return
        self.resumenes[id]=datos;self.logs_importados.add(id)
        if id==self.selector.currentData():self.pintar_visible();self.vigilar()
        if id in self.resumen_pendiente:
            self.resumen_pendiente.discard(id)
            if id==self.selector.currentData():self.pedir_resumen()

    def pintar_visible(self):
        s=self.servidor
        if not s:return
        datos=self.resumenes.get(s.id,{})
        self.mods_datos=datos.get('mods',[]);self.copias_datos=datos.get('copias',[])
        self.datos_jugadores=self.jugadores_actuales()
        indice=self.stack.currentIndex()
        if indice==0:self.actualizar_inicio()
        elif indice==1:self.actualizar_jugadores();self.actualizar_diario()
        elif indice==2:self.actualizar_mods()
        elif indice==3:self.actualizar_copias()
        elif indice==4:self.cargar_ajustes()

    def registros(self):
        return self.resumenes.get(self.selector.currentData(),{}).get('diario',[])

    def jugadores_actuales(self):
        from ..motor.tiempos import sesiones_jugadores
        c=self.control;conectados=c.consola.jugadores if c else ()
        horas,_=sesiones_jugadores(self.registros(),conectados,c.consola.entradas if c else {})
        datos=[dict(j) for j in self.resumenes.get(self.selector.currentData(),{}).get('jugadores',[])]
        for nick in conectados:
            if not any(j['nick'].casefold()==nick.casefold() for j in datos):datos.append({'nick':nick,'uuid':'','ultima':'','horas':0})
        for j in datos:j['horas']=horas.get(j['nick'].casefold(),0);j['conectado']=j['nick'].casefold() in {n.casefold() for n in conectados}
        return sorted(datos,key=lambda j:(not j['conectado'],j['nick'].casefold()))

    def actualizar_estado(self):
        if not hasattr(self,'bandeja'):return
        c=self.control; estado=c.estado if c else 'apagado'
        self.estado.setText(tr(estado.capitalize()))
        self.punto_estado.set_estado("operativa" if estado=="encendido" else "fallo" if estado=="error" else "inactiva" if estado=="apagado" else "trabajando")
        vivo=any(c.hilo and c.hilo.is_alive() for c in self.controles.values()) or self.biblioteca.lock.exists()
        self.iniciar_boton.setEnabled(bool(self.servidor) and not vivo and not self.trabajos)
        self.iniciar_boton.setToolTip(tr("Detén el servidor activo antes de iniciar otro") if vivo else tr("Iniciar el servidor elegido"))
        self.parar_boton.setEnabled(bool(c and c.hilo and c.hilo.is_alive()))
        self.reiniciar_boton.setEnabled(bool(c and c.estado=='encendido'))
        if estado!=getattr(self,'ultimo_icono',None):self.bandeja.setIcon(icons.app_icon(estado));self.ultimo_icono=estado
        n=c.consola.lista_numero if c else 0
        self.bandeja.setToolTip(tr("Telazocraft · %s · %s jugadores")%(estado,n));self.accion_estado.setText(tr("%s · %s jugadores")%(estado,n))
        activo=bool(c and c.estado=='encendido' and self.stack.currentWidget() is self.paginas['Inicio'] and self.isVisible())
        if activo and not self.timer_metricas.isActive():self.timer_metricas.start()
        elif not activo:self.timer_metricas.stop()
        self.graficas_panel.setVisible(bool(c and c.estado=='encendido'))
        estados=tuple((self.selector.itemData(i),self.controles[self.selector.itemData(i)].estado if self.selector.itemData(i) in self.controles else 'apagado') for i in range(self.selector.count()))
        if estados!=getattr(self,'ultimos_estados',None):
            for i,(_,est) in enumerate(estados):self.selector.setItemIcon(i,icons.estado_icon(est))
            self.ultimos_estados=estados
        self.actualizar_bloqueos()
        if c and c.estado=='encendido' and self.isVisible() and int(time.time())//60!=getattr(self,'minuto_vivo',None):
            self.minuto_vivo=int(time.time())//60;self.pintar_visible()

    def cambiar_vista(self,indice):
        if indice<0:return
        self.stack.setCurrentIndex(indice)
        self.pintar_visible()
        if indice==2:self.enriquecer_mods()
        if indice==1:self.cargar_cabezas_automaticas()
        self.actualizar_estado()

    def ajustar_lateral(self):
        compacto=self.width()<1080
        self.lateral.setFixedWidth(72 if compacto else 186)
        self.gear.setText('' if compacto else tr('Telazocraft'))
        for i,nombre in enumerate(self.VISTAS[:5]):
            item=self.nav.item(i);item.setText('' if compacto else tr(nombre));item.setSizeHint(QSize(38 if compacto else 148,48))

    def resizeEvent(self,e):
        super().resizeEvent(e)
        if hasattr(self,'lateral'):self.ajustar_lateral()

    def parar(self):
        c=self.control
        if c:
            if c.consola.lista_numero and not confirmar(self,tr("Se guardará el mundo y se creará una copia de sesión."),'Parar servidor',[(tr('Estado'),tr('Jugando'),tr('Apagado'))],True):return
            c.parar()

    def reiniciar(self):
        if self.control and confirmar(self,tr("Se guardará el mundo antes de reiniciar."),'Reiniciar servidor',[(tr('Estado'),tr('Encendido'),tr('Reinicio con copia'))]):
            try:self.control.reiniciar()
            except Exception as exc:self.mostrar_error(str(exc))

    def evento(self,id,tipo,dato):
        if tipo=='log' and id==self.selector.currentData():
            self.log.agregar(dato);self.ultimo_log.setText(str(dato));self.ultimo_log.setToolTip(str(dato))
            self.ultimo_log.setProperty('nivel','error' if 'ERROR' in dato else 'aviso' if 'WARN' in dato else 'normal')
            self.ultimo_log.style().unpolish(self.ultimo_log);self.ultimo_log.style().polish(self.ultimo_log)
            if 'chunky' in dato.lower() and '%' in dato:self.progreso_chunky.setText(dato.split(']: ')[-1])
            if 'chunky' in dato.lower() and any(p in dato.lower() for p in ('finished','cancelled','canceled','stopped')):
                self.chunky_en_curso=False;self.progreso_chunky.setText(dato.split(']: ')[-1]);self.actualizar_bloqueos()
        elif tipo in ('error','aviso'):self.aviso.setText(str(dato));self.notificar(tr('Telazocraft'),dato)
        elif tipo=='cabezas' and id==self.selector.currentData():self.actualizar_jugadores()
        elif tipo=='copia':self.aviso.setText(tr('Copia creada: %s')%Path(dato).name)
        elif tipo=='jugadores':
            evento=dato['evento']
            if id in self.resumenes and evento.get('fecha'):
                self.resumenes[id]['diario'].append(evento)
            if id==self.selector.currentData():self.pintar_visible()
            if evento['tipo'] in ('entrada','salida'):self.notificar(tr('Jugadores'),tr('%s: %s')%(evento['jugador'],evento['tipo']))
        elif tipo=='progreso' and id==self.selector.currentData():
            self.ocultar_progreso.stop()
            self.progreso_operacion.show();self.progreso_operacion.setRange(0,100)
            self.progreso_operacion.setValue(dato['valor']);self.progreso_operacion.setFormat(str(dato.get('texto',''))+' · %p%')
            if dato['valor']>=100:self.ocultar_progreso.start(1500)
        if tipo not in ('log','progreso'):self.debounce.start();self.actualizar_estado()

    def construir_consola(self):
        self.log=Log();self.mini_log=self.log
        self.buscar_log=QLineEdit();self.buscar_log.setPlaceholderText(tr('Buscar en la consola'));self.buscar_log.returnPressed.connect(lambda:self.log.find(self.buscar_log.text()))
        self.seguir=CheckBox(tr('Seguir'));self.seguir.setChecked(True);self.seguir.toggled.connect(lambda v:setattr(self.log,'seguir',v))
        self.mini_comando=Comando();self.mini_comando.returnPressed.connect(lambda:self.enviar(self.mini_comando))
        self.mini_contenido=style.agrupador();v=QVBoxLayout(self.mini_contenido);v.setContentsMargins(0,0,0,0)
        v.addWidget(fila(self.buscar_log,self.seguir));v.addWidget(self.log,1);v.addWidget(fila(self.mini_comando,boton('Enviar',lambda:self.enviar(self.mini_comando))))
        self.plegar=boton('Consola ▴',lambda:self.alternar_consola(self.plegar.isChecked()));self.plegar.setCheckable(True)
        self.ultimo_log=EtiquetaElidida(tr('Sin mensajes de esta sesión'))
        pestana=fila(self.plegar,self.ultimo_log)
        pestana.layout().setStretch(1,1)
        pestana.layout().setStretch(2,0)
        self.consola_panel=style.tarjeta(pestana,self.mini_contenido)
        self.alternar_consola(self.prefs.get('consola_abierta',False))

    def alternar_consola(self,abierta):
        self.plegar.setChecked(abierta);self.plegar.setText(tr('Consola ▾') if abierta else tr('Consola ▴'))
        self.mini_contenido.setVisible(abierta);self.ultimo_log.setVisible(not abierta)
        self.consola_panel.setMaximumHeight(16777215 if abierta else 62)
        QTimer.singleShot(0,lambda:self.splitter.setSizes([max(200,self.height()-self.prefs.get('consola_alto',240)-130),self.prefs.get('consola_alto',240) if abierta else 62]))

    def recordar_altura_consola(self,*_):
        if self.plegar.isChecked():self.prefs['consola_alto']=self.splitter.sizes()[-1]

    def guardar_ventana(self):
        if self.persistir:
            self.prefs.update(biblioteca=str(self.biblioteca.raiz),ultimo_servidor=self.selector.currentData(),ancho=self.normalGeometry().width(),alto=self.normalGeometry().height(),consola_abierta=self.plegar.isChecked())
            if self.plegar.isChecked():self.prefs['consola_alto']=self.splitter.sizes()[-1]
            ajustes.guardar(self.prefs)

    def closeEvent(self,e):
        if self._salir:
            self.bandeja.hide();self.timer_estado.stop();self.timer_metricas.stop();self.debounce.stop()
            for hilo in self.lectores:hilo.join(5)
            e.accept()
        elif self.bandeja.isVisible():self.hide();e.ignore();self.guardar_ventana()
        else:e.ignore();self.salir()

    def copiar_direccion(self):
        QApplication.clipboard().setText(self.direccion.text().strip())

    def trabajo(self, funcion, final=lambda resultado: None):
        if self.trabajos:
            self.aviso.setText(tr("Espera a que termine la operación en curso"))
            return
        self.trabajos += 1
        self.selector.setEnabled(False)
        self.aviso.setText(tr("Trabajando…"))
        self.progreso_operacion.setRange(0,0);self.progreso_operacion.show()
        def ejecutar():
            try:
                self.bus.resultado.emit(final, funcion(), None)
            except Exception as exc:
                logging.getLogger(__name__).exception('Falló la operación')
                self.bus.resultado.emit(final, None, str(exc))
        threading.Thread(target=ejecutar, daemon=False).start()

    def _resultado(self, final, resultado, error):
        self.trabajos -= 1
        self.progreso_operacion.setRange(0,100);self.progreso_operacion.setValue(100 if not error else 0)
        self.ocultar_progreso.start(1500)
        self.selector.setEnabled(not self.trabajos)
        if error:
            self.mostrar_error(error)
        else:
            self.aviso.setText("")
            try:
                final(resultado)
            except Exception as exc:
                self.mostrar_error(str(exc))
        self.actualizar_estado()

    def mostrar_error(self, texto):
        logging.getLogger(__name__).error('%s',texto)
        self.aviso.setText(tr("Error: %s") % texto)
        self.notificar(tr("Error"), texto)

    def notificar(self, titulo_aviso, texto):
        if self.bandeja.isVisible():
            self.bandeja.showMessage(titulo_aviso, str(texto), QSystemTrayIcon.Information, 5000)

    def iniciar(self):
        if not self.servidor:
            return
        if self.trabajos or any(c.hilo and c.hilo.is_alive() for c in self.controles.values()):
            self.mostrar_error(tr("Ya hay un servidor u operación en curso"))
            return
        s = self.servidor
        try:
            control = Controlador(s, lambda t, d: self.bus.evento.emit(s.id, t, d))
            self.controles[s.id] = control
            self.trabajo(control.iniciar)
            self.actualizar_estado()
        except Exception as exc:
            self.mostrar_error(str(exc))

    def enviar(self, caja):
        texto = caja.recordar()
        if texto:
            try:
                if not self.control:
                    raise RuntimeError(tr("El servidor está apagado"))
                self.control.comando(texto)
            except Exception as exc:
                self.mostrar_error(str(exc))

    def buscar_actualizacion(self):
        def pintar(datos):
            self.actualizacion = datos
            self.actualizar_app_boton.setEnabled(datos["nueva"])
            self.aviso.setText(tr("Última versión publicada: %s") % datos["version"])
            if datos["nueva"]:
                self.notificar(tr("Actualización de Telazocraft"), tr("Está disponible la versión %s") % datos["version"])
        self.trabajo(github_releases.ultima, pintar)

    def instalar_actualizacion(self):
        if not self.actualizacion or not self.actualizacion["nueva"]:
            return
        if not confirmar(self, "Se descargará el instalador verificado y se cerrará Telazocraft después de guardar el servidor.", "Actualizar Telazocraft"):
            return
        datos = dict(self.actualizacion)
        servidor_id=self.selector.currentData() or ''
        activos = [c for c in self.controles.values() if c.hilo and c.hilo.is_alive()]
        def preparar():
            instalador = actualizador.preparar(datos,lambda n,total:self.bus.evento.emit(servidor_id,'progreso',{'valor':int(100*n/total) if total else 0,'texto':tr('Descargando actualización')}))
            for c in activos:
                c.parar(esperar=True)
            if any(c.proceso.vivo for c in activos):
                raise RuntimeError(tr("No se pudo detener el servidor"))
            return instalador
        def instalar(instalador):
            self.guardar_ventana()
            actualizador.ejecutar(instalador)
            self._salir = True
            self.close()
            QApplication.instance().quit()
        self.trabajo(preparar, instalar)

    def crear_bandeja(self):
        self.bandeja = QSystemTrayIcon(icons.app_icon(), self)
        menu = QMenu(self)
        self.accion_estado = menu.addAction(tr("Apagado"))
        self.accion_estado.setEnabled(False)
        menu.addSeparator()
        for texto, accion in (("Abrir Telazocraft", self.mostrar), ("Iniciar", self.iniciar), ("Parar", self.parar),
                              ("Copiar dirección", self.copiar_direccion), ("Paquete para amigos", self.zip_amigos), ("Abrir exportaciones", self.abrir_exportaciones), ("Salir", self.salir)):
            a = menu.addAction(tr(texto))
            a.triggered.connect(accion)
        self.bandeja.setContextMenu(menu)
        self.bandeja.activated.connect(lambda razon: self.mostrar() if razon in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.bandeja.show()

    def abrir_exportaciones(self):
        if self.servidor:
            ruta = self.biblioteca.ruta("exportaciones", self.servidor.id)
            ruta.mkdir(exist_ok=True)
            abrir_carpeta(str(ruta))

    def ofrecer_prueba(self):
        if self.biblioteca.servidores():return
        if not confirmar(self,tr('¿Crear Servidor de prueba con la última versión estable de Minecraft vanilla? Se descargará ahora, sin mods. Al continuar aceptas la EULA: https://www.minecraft.net/eula'),'Crear servidor de prueba'):return
        from ..motor import asistente,vanilla
        biblioteca=self.biblioteca
        def crear():
            version=next(v['id'] for v in vanilla.versiones() if v['type']=='release')
            return asistente.crear(biblioteca,id='prueba',nombre='Servidor de prueba',tipo='vanilla',version_mc=version,progreso=lambda t:self.bus.evento.emit('prueba','aviso',t))
        self.trabajo(crear,lambda _:self.recargar_servidores())

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_centrada", False):
            self._centrada = True
            self.centrar_en_principal()

    def centrar_en_principal(self):
        """Abre siempre en ventana y centrada en el monitor principal; nunca más grande que su área útil."""
        pantalla = QGuiApplication.primaryScreen()
        if pantalla is None:
            return
        util = pantalla.availableGeometry()
        self.resize(min(self.width(), util.width() - 40), min(self.height(), util.height() - 40))
        marco = self.frameGeometry()
        marco.moveCenter(util.center())
        self.move(marco.left(), max(util.top(), marco.top()))

    def changeEvent(self, e):
        super().changeEvent(e)
        # Sin pantalla completa: si algo la pide (Windows, un atajo), queda maximizada en ventana.
        if e.type() == QEvent.WindowStateChange and self.windowState() & Qt.WindowFullScreen:
            QTimer.singleShot(0, lambda: self.setWindowState((self.windowState() & ~Qt.WindowFullScreen) | Qt.WindowMaximized))

    def mostrar(self):
        # Desde la bandeja: vuelve como estaba (en ventana o maximizada), solo deja de estar minimizada.
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.show()
        self.raise_()
        self.activateWindow()

    def salir(self):
        if self.trabajos:
            self.aviso.setText(tr("Espera a que termine la operación en curso"))
            return
        activos = [c for c in self.controles.values() if c.hilo and c.hilo.is_alive()]
        pendientes = bool(self.borradores)
        mensaje = tr("Se detendrá el servidor y se creará una copia de sesión.") if activos else ""
        if pendientes:
            mensaje += " " + tr("Se descartarán los ajustes sin aplicar.")
        if (activos or pendientes) and not confirmar(self, mensaje.strip(), "Guardar y salir" if activos else "Descartar y salir"):
            return
        def terminar(_=None):
            if any(c.proceso.vivo for c in activos):
                self.mostrar_error(tr("Java sigue activo; no se puede cerrar"))
                return
            self.guardar_ventana()
            self._salir = True
            self.close()
            QApplication.instance().quit()
        if activos:
            self.trabajo(lambda: [c.parar(esperar=True) for c in activos], terminar)
        else:
            terminar()

    def apagado_windows(self, manager):
        for c in self.controles.values():
            if c.hilo and c.hilo.is_alive():
                try:
                    c.parar(esperar=True)
                except Exception:
                    logging.getLogger(__name__).exception('No se pudo guardar al apagar Windows')
                    manager.cancel()
                    return
        self.guardar_ventana()


def ejecutar(ruta=None, smoke=False):
    app = crear_app()
    nueva=False
    if not ruta:
        ruta = QFileDialog.getExistingDirectory(None, tr("Elige una biblioteca o una carpeta vacía para crearla"))
        if not ruta:
            return 0
        if not (Path(ruta) / "telazocraft.json").exists():
            nueva=not any(Path(ruta).iterdir())
            if not confirmar(None, "Se creará una biblioteca de Telazocraft en la carpeta elegida.", "Crear biblioteca"):
                return 0
            Biblioteca(ruta, crear=True)
    biblioteca = Biblioteca(ruta)
    lock = QLockFile(str(ajustes.ruta().with_suffix(".app.lock")))
    lock.setStaleLockTime(0)
    ajustes.ruta().parent.mkdir(parents=True, exist_ok=True)
    if not smoke and not lock.tryLock(100):
        return 0
    ventana = MainWindow(biblioteca, persistir=not smoke)
    ventana.show()
    if nueva and not smoke:ventana.ofrecer_prueba()
    if smoke:
        def cerrar():
            ventana._salir = True
            ventana.close()
            app.quit()
        QTimer.singleShot(800, cerrar)
    resultado = app.exec()
    lock.unlock()
    return resultado
