import hashlib
import logging
import threading
import unicodedata
import urllib.request
import urllib.parse
from pathlib import Path
from PySide6.QtCore import Qt,Signal,QObject
from PySide6.QtGui import QIcon,QPixmap,QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QFileDialog,QLabel,QLineEdit,QListWidget,QListWidgetItem,QTableWidgetItem,QMenu
from . import style,icons
from .base import Dialogo,boton,fila,titulo,confirmar,opciones_boton,vaciar_tabla
from .gestion import chip
from .widgets.tabla_datos import TablaDatos
from .widgets.boton_carpeta import BotonCarpeta
from .widgets.lista_mods import ListaMods
from ..common import ajustes
from ..common.i18n import tr
from ..motor import modrinth,exportaciones
from ..motor.util import http_json,guardar_json,leer_json


class BusMods(QObject):
    listo=Signal(str,object,object)
    iconos=Signal()


class PantallasMods:
    def progreso_mod(self,servidor):
        return lambda n,t:self.bus.evento.emit(servidor.id,'progreso',{'valor':n,'texto':t})

    def construir_mods(self):
        self.mods_datos=[];self.mods_updates={};self.mods_cargando=set();self.mods_enriquecidos=set()
        self.bus_mods=BusMods(self);self.bus_mods.listo.connect(self.mods_recibidos);self.bus_mods.iconos.connect(lambda:self.pintar_mods(self.mods_datos))
        self.tabla_mods=TablaDatos([tr(s) for s in ('Mod','Versión','Lado','Actualización','')],columnas_accion=(4,),columna_estirada=0,anchos={0:300,1:190,2:120,3:140,4:52})
        self.tabla_mods.verticalHeader().setDefaultSectionSize(48)
        self.anadir_mod_boton=boton('Añadir mod',self.anadir_mod,True);self.anadir_mod_boton.setIcon(icons.glifo('mas',16))
        self.mods_contador=QLabel()
        self.paginas['Mods'].layout().addWidget(style.tarjeta(fila(titulo('Mods'),self.mods_contador,self.anadir_mod_boton,boton('Paquete para amigos',self.zip_amigos),BotonCarpeta(lambda:str(self.biblioteca.ruta('exportaciones',self.servidor.id)) if self.servidor else '',tr('Abrir carpeta de exportaciones'))),self.tabla_mods))
        panel=self.paginas['Mods'];panel.setAcceptDrops(True)
        panel.dragEnterEvent=lambda e:e.acceptProposedAction() if e.mimeData().hasUrls() and all(u.isLocalFile() and u.toLocalFile().lower().endswith('.jar') for u in e.mimeData().urls()) else e.ignore()
        panel.dropEvent=self.soltar_jars

    def cache_mods(self,s):
        key=hashlib.sha256(str(s.ruta).encode()).hexdigest()[:20]
        return ajustes.ruta().parent/'mods'/key/'inventario.json'

    def actualizar_mods(self):
        if self.servidor:self.pintar_mods(self.mods_datos)

    def pintar_mods(self,datos):
        datos=sorted(datos,key=lambda m:(m['nombre'] or m['archivo']).casefold())
        self.mods_datos=datos;vaciar_tabla(self.tabla_mods);self.tabla_mods.setRowCount(len(datos));self.mods_contador.setText(tr('%s instalados')%len(datos))
        for r,m in enumerate(datos):
            # Sin emojis: la fuente de la interfaz los pinta como un cuadro vacío (p. ej. «Jade 🔍»).
            nombre=QTableWidgetItem(''.join(c for c in m['nombre'] if unicodedata.category(c)!='So').strip());nombre.setToolTip(m['archivo'])
            icono=ajustes.ruta().parent/'iconos_mods'/(hashlib.sha256((m.get('icon_url') or '').encode()).hexdigest()+'.png')
            nombre.setIcon(QIcon(str(icono)) if icono.exists() else icons.glifo('mods',28))
            version=QTableWidgetItem(m['version'] or tr('Manual'));version.setToolTip(m['version'] or tr('Manual'))
            self.tabla_mods.setItem(r,0,nombre);self.tabla_mods.setItem(r,1,version)
            lado=tr('Servidor') if m['lado']=='unsupported' else tr('Cliente') if m.get('server_side')=='unsupported' else tr('Ambos') if m['lado'] in ('required','optional') else tr('Desconocido')
            self.tabla_mods.setCellWidget(r,2,chip(lado))
            if m['archivo'] in self.mods_updates:estado=(tr('Disponible'),'aviso')
            elif m.get('proyecto'):estado=(tr('Al día'),'ok')
            else:estado=tr('Manual')
            self.tabla_mods.setCellWidget(r,3,chip(estado))
            b=opciones_boton(lambda checked=False,m=m:self.menu_mod(m));b.setToolTip(tr('Acciones del mod'));self.tabla_mods.setCellWidget(r,4,b)

    def enriquecer_mods(self):
        s=self.servidor
        if not s or not self.persistir:return
        firma=(str(s.ruta),tuple((p.name,p.stat().st_mtime_ns) for p in sorted((s.ruta/'mods').glob('*.jar'))))
        if firma in self.mods_enriquecidos or str(s.ruta) in self.mods_cargando:return
        self.mods_enriquecidos.add(firma);self.mods_cargando.add(str(s.ruta))
        def leer():
            try:
                datos=modrinth.inventario(s,True,self.cache_mods(s))
                updates={}
                hashes=[m['sha1'] for m in datos if m.get('proyecto')]
                if hashes:
                    remotos=http_json(modrinth.API+'/version_files/update',{'hashes':hashes,'algorithm':'sha1','loaders':[s.datos['tipo']],'game_versions':[s.datos['version_mc']]})
                    updates={m['archivo']:{'nueva':remotos[m['sha1']]} for m in datos if m['sha1'] in remotos and remotos[m['sha1']]['id']!=m['version_id']}
                self.bus_mods.listo.emit(str(s.ruta),datos,updates)
                descargados=0
                for m in datos:
                    url=m.get('icon_url')
                    if not url or urllib.parse.urlsplit(url).scheme!='https' or urllib.parse.urlsplit(url).hostname!='cdn.modrinth.com':continue
                    p=ajustes.ruta().parent/'iconos_mods'/(hashlib.sha256(url.encode()).hexdigest()+'.png')
                    if p.exists():continue
                    try:
                        with urllib.request.urlopen(url,timeout=8) as r:data=r.read(2*1024*1024)
                        # QImageReader recognises PNG/JPEG/WebP by content even if cached extension is .png.
                        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                        descargados+=1
                        if descargados%6==0:self.bus_mods.iconos.emit()
                    except OSError:pass
                self.bus_mods.iconos.emit()
            except Exception as exc:
                logging.getLogger(__name__).exception('No se pudieron consultar los mods')
                self.mods_enriquecidos.discard(firma)
                self.bus_mods.listo.emit(str(s.ruta),None,{'error':str(exc)})
        threading.Thread(target=leer,daemon=True).start()

    def mods_recibidos(self,ruta,datos,updates):
        self.mods_cargando.discard(ruta)
        if self.servidor and str(self.servidor.ruta)==ruta:
            if datos is not None:
                self.mods_updates=updates
                if self.servidor.id in self.resumenes:self.resumenes[self.servidor.id]['mods']=datos
                self.mods_datos=datos
                if self.stack.currentIndex()==2:self.pintar_mods(datos)
            else:self.aviso.setText(tr('No se pudieron consultar los mods: %s')%updates.get('error',''))

    def menu_mod(self,m):
        s=self.servidor;menu=QMenu(self)
        a=menu.addAction(tr('Actualizar'),lambda:self.actualizar_mod(m));a.setEnabled(m['archivo'] in self.mods_updates and not self.biblioteca.lock.exists())
        a=menu.addAction(tr('Retirar'),lambda:self.retirar_mod(m));a.setEnabled(not self.biblioteca.lock.exists());a.setToolTip(tr('Requiere servidor parado'))
        a=menu.addAction(tr('Abrir en Modrinth'),lambda:QDesktopServices.openUrl(QUrl('https://modrinth.com/mod/'+str(m['proyecto']))));a.setEnabled(bool(m['proyecto']))
        menu.exec(self.cursor().pos())

    def anadir_mod(self):
        d=Dialogo(self,'Añadir mod');d.resize(650,520)
        buscar=QLineEdit();buscar.setPlaceholderText(tr('Buscar mods compatibles en Modrinth'))
        lista=ListaMods();hits=[];s=self.servidor
        def pintar(datos):
            instalados={m['proyecto'] for m in self.mods_datos if m.get('proyecto')}
            datos=[{**h,'instalado':h['project_id'] in instalados} for h in datos]
            hits[:]=datos;lista.cargar(datos)
        from .busqueda_mods import BusquedaMods
        buscador=BusquedaMods(d,lambda:s);buscador.listo.connect(pintar);buscar.textChanged.connect(buscador.cambiar)
        ayuda=QLabel(tr('Resultados de Modrinth para %s %s')%(s.datos['version_mc'],s.datos['tipo']))
        estado=QLabel();estado.setWordWrap(True);buscador.estado.connect(estado.setText)
        buscar.returnPressed.connect(buscador.consultar)
        d.formulario.addWidget(buscar);d.formulario.addWidget(ayuda);d.formulario.addWidget(estado);d.formulario.addWidget(lista)
        d.formulario.addWidget(boton('Elegir archivos .jar',lambda:(d.reject(),self.agregar_jar())))
        d.terminar_botones('Instalar seleccionado')
        d.setAcceptDrops(True);d.dragEnterEvent=lambda e:e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()
        d.dropEvent=lambda e:(d.reject(),self._agregar_jars([u.toLocalFile() for u in e.mimeData().urls()]))
        if d.exec() and 0<=lista.currentRow()<len(hits):
            h=hits[lista.currentRow()]
            if h.get('instalado'):return
            def opciones(v):
                if not v:self.mostrar_error(tr('No hay una versión compatible'));return
                version=v[0]
                dependencias=[x for x in version.get('dependencies',[]) if x['dependency_type']=='required']
                if confirmar(self,tr('Se instalará el mod y sus dependencias obligatorias.'),'Instalar mod',[(h['title'],tr('No instalado'),version['version_number']),(tr('Dependencias obligatorias'),0,len(dependencias))]):self.trabajo(lambda:modrinth.instalar(s,version['id'],progreso=self.progreso_mod(s)),lambda _:self.refrescar())
            self.trabajo(lambda:modrinth.versiones(h['project_id'],s),opciones)

    def agregar_jar(self):
        archivos,_=QFileDialog.getOpenFileNames(self,tr('Añadir mods'),'',tr('Mods (*.jar)'))
        if archivos:self._agregar_jars(archivos)

    def _agregar_jars(self,archivos):
        s=self.servidor
        if s and not self.biblioteca.lock.exists() and confirmar(self,tr('Se añadirán estos JAR al servidor.'),'Añadir mods',[(Path(p).name,tr('No instalado'),tr('Instalado')) for p in archivos]):self.trabajo(lambda:[modrinth.agregar_jar(s,p) for p in archivos],lambda _:self.refrescar())

    def soltar_jars(self,e):self._agregar_jars([u.toLocalFile() for u in e.mimeData().urls()]);e.acceptProposedAction()

    def retirar_mod(self,m):
        s=self.servidor
        if s and confirmar(self,tr('Se conservará el archivo en mods_retirados.'),'Retirar mod',[(m['nombre'],m['version'] or tr('Instalado'),tr('Retirado'))],True):self.trabajo(lambda:modrinth.retirar(s,m['archivo']),lambda _:self.refrescar())

    def actualizar_mod(self,m):
        s=self.servidor;v=self.mods_updates.get(m['archivo'],{}).get('nueva')
        if v and confirmar(self,tr('Se conservará el JAR anterior.'),'Actualizar mod',[(m['nombre'],m['version'],v['version_number'])]):self.trabajo(lambda:modrinth.instalar(s,v['id'],progreso=self.progreso_mod(s)),lambda _:self.refrescar())

    def zip_amigos(self):
        s=self.servidor
        if s and confirmar(self,tr('Se incluirán mods de cliente, extras, instalador de NeoForge e instrucciones.'),'Crear paquete para amigos',[(tr('Exportación'),tr('Sin archivo nuevo'),tr('Paquete para amigos'))]):self.trabajo(lambda:exportaciones.crear(s,progreso=lambda n,t:self.bus.evento.emit(s.id,'progreso',{'valor':n,'texto':t})),lambda r:self.aviso.setText(tr('Paquete creado: %s')%r[0].name))

    def pregenerar(self):
        s, c = self.servidor, self.control
        if not s or not c or c.estado != "encendido":
            self.mostrar_error(tr("Inicia el servidor antes de pregenerar"))
            return
        if not any("chunky" in p.name.lower() for p in (s.ruta / "mods").glob("*.jar")):
            self.mostrar_error(tr("Este servidor no tiene Chunky instalado"))
            return
        radio = int(self.radio_chunky.value())
        if confirmar(self, tr("Se pregenerará un radio de %s bloques.") % radio, "Pregenerar"):
            c.comando(f"chunky radius {radio}")
            c.comando("chunky start")
            self.chunky_en_curso = True
            self.progreso_chunky.setText(tr("Chunky: tarea iniciada; progreso en la consola"))
            self.actualizar_bloqueos()

    def cancelar_chunky(self):
        if self.control and self.control.proceso.vivo:
            if not confirmar(self,tr("Se cancelará la generación de terreno pendiente."),'Cancelar tarea',[(tr('Chunky'),tr('En curso'),tr('Cancelado'))]):return
            self.control.comando("chunky cancel")
            self.chunky_en_curso = False
            self.progreso_chunky.setText(tr("Chunky: cancelación enviada"))
            self.actualizar_bloqueos()
