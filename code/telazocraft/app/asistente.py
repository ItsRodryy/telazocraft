import re
import threading
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout,QLabel,QLineEdit,QStackedWidget,QListWidget,QListWidgetItem,QTableWidgetItem
from .base import boton,fila,titulo
from .widgets.dialogo_proceso import DialogoProceso
from .widgets.spin_box import ComboSinRueda
from .widgets.check_box import CheckBox
from .widgets.tabla_datos import TablaDatos
from .widgets.lista_mods import ListaMods
from . import style,icons
from ..common.i18n import tr
from ..motor import asistente,vanilla,modrinth,neoforge


class NuevoServidor(DialogoProceso):
    progreso=Signal(str)
    resultado=Signal(object,object)
    versiones_listas=Signal(object)
    loaders_listos=Signal(object)
    busqueda_lista=Signal(object)
    compatibilidad_lista=Signal(object)

    def __init__(self,padre,red=True):
        super().__init__(tr('Nuevo servidor'),parent=padre)
        self.resize(720,650);self.terminado=True;self.creado=None;self.indice=0;self.en_curso=False
        self.resultado.connect(self.finalizar);self.progreso.connect(self.anadir_linea)
        self.stack=QStackedWidget();self.layout().insertWidget(1,self.stack,1)
        self.titulo_paso=titulo('1 de 5 · Tipo y versión');self.layout().insertWidget(1,self.titulo_paso)
        self.tipo=ComboSinRueda()
        for n,v in (('NeoForge','neoforge'),('Vanilla','vanilla'),('Copiar otro sin mundo','copia')):self.tipo.addItem(tr(n),v)
        self.plantilla=ComboSinRueda();self.whitelist=ComboSinRueda();self.whitelist.addItem(tr('Vacía'),None)
        for s in padre.biblioteca.servidores():self.plantilla.addItem(s.nombre,s.id);self.whitelist.addItem(s.nombre,s.id)
        self.version=ComboSinRueda();self.version.setEditable(True);self.version.addItem('26.3')
        self.loader=ComboSinRueda();self.loader.setEditable(True);self.loader.addItem('26.3.0.99');self.loaders=[];self.nombre=QLineEdit();self.id=QLineEdit()
        self.nombre.textChanged.connect(lambda t:self.id.setText(re.sub(r'[^a-z0-9_-]','_',t.lower())[:64]))
        self.semilla=QLineEdit();self.semilla.setPlaceholderText(tr('Aleatoria'));self.hardcore=CheckBox(tr('Hardcore'))
        self.acceso=ComboSinRueda();self.acceso.addItems([tr('abierto'),tr('premium')])
        self.mods=QLineEdit();self.mods.setReadOnly(True);self.mods.setPlaceholderText(tr('Mods seleccionados'))
        self.buscar=QLineEdit();self.buscar.setPlaceholderText(tr('Buscar mods compatibles en Modrinth'));self.resultados=ListaMods();self.hits=[];self.slugs=[]
        self.instalar_java=CheckBox(tr('Instalar Java con winget si falta'));self.eula=CheckBox(tr('Acepto la EULA de Minecraft'));self.eula.setToolTip('https://www.minecraft.net/eula')
        self.tabla=TablaDatos([tr('Minecraft'),tr('Mods compatibles'),tr('Total')]);self.tabla.setMaximumHeight(120)
        def pagina(campos,extras=()):
            grupo=style.agrupador();form=QFormLayout(grupo)
            for texto,w in campos:form.addRow(tr(texto),w)
            panel=style.tarjeta(grupo,*extras);self.stack.addWidget(panel)
        pagina((('Tipo',self.tipo),('Minecraft',self.version),('NeoForge',self.loader),('Copiar desde',self.plantilla)))
        pagina((),(fila(self.buscar,boton('Buscar',self.buscar_mods)),self.resultados,boton('Añadir seleccionado',self.elegir_mod),self.mods,boton('Comparar compatibilidad',self.comparar),self.tabla))
        pagina((('Nombre',self.nombre),('Identificador',self.id),('Semilla',self.semilla)),(self.hardcore,))
        pagina((('Acceso',self.acceso),('Whitelist inicial',self.whitelist)),(QLabel(tr('Abierto admite jugadores offline y premium; solo premium verifica la cuenta.')),))
        self.resumen=QLabel();self.resumen.setWordWrap(True)
        pagina((),(self.resumen,self.instalar_java,self.eula))
        self.atras=boton('Atrás',lambda:self.mover(-1));self.siguiente=boton('Siguiente',lambda:self.mover(1),True);self.cancelar=boton('Cancelar',self.reject)
        self.layout().addWidget(fila(self.atras,self.cancelar,self.siguiente))
        self.btn_detalle.hide();self.btn_cerrar.hide();self.barra.hide();self.estado.hide();self.mensaje.hide()
        self.tipo.currentIndexChanged.connect(self.actualizar_tipo);self.plantilla.currentIndexChanged.connect(self.actualizar_tipo);self.buscar.returnPressed.connect(self.buscar_mods)
        self.versiones_listas.connect(self.pintar_versiones);self.busqueda_lista.connect(self.pintar_busqueda);self.compatibilidad_lista.connect(self.pintar_comparacion)
        self.actualizar_tipo();self.mostrar_paso()
        self.loaders_listos.connect(self.pintar_loaders)
        self.version.currentTextChanged.connect(self.filtrar_loaders)
        if red:
            self.lanzar(vanilla.versiones,self.versiones_listas)
            self.lanzar(neoforge.versiones,self.loaders_listos)

    def lanzar(self,fn,signal):
        def hacer():
            try:signal.emit(fn())
            except Exception as e:self.progreso.emit(tr('Sin red: %s')%e)
        threading.Thread(target=hacer,daemon=True).start()

    def pintar_loaders(self,datos):
        self.loaders=datos;self.filtrar_loaders()

    def filtrar_loaders(self,*_):
        if not self.loaders:return
        version=self.version.currentText();partes=version.split('.')
        prefijo='.'.join(partes[1:] if partes[0]=='1' else partes)+'.'
        opciones=[v for v in self.loaders if v.startswith(prefijo)]
        anterior=self.loader.currentText();self.loader.clear();self.loader.addItems(list(reversed(opciones)))
        if anterior in opciones:self.loader.setCurrentText(anterior)

    def pintar_versiones(self,datos):
        actual=self.version.currentText();self.version.clear();self.version.addItems([v['id'] for v in datos if v['type']=='release']);self.version.setCurrentText(actual)

    def actualizar_tipo(self):
        copia=self.tipo.currentData()=='copia';self.plantilla.setEnabled(copia);self.loader.setEnabled(self.tipo.currentData()=='neoforge');self.version.setEnabled(not copia)
        self.buscar.setEnabled(self.tipo.currentData()!='vanilla')
        if copia and self.plantilla.currentData():
            s=self.parent().biblioteca.servidor(self.plantilla.currentData())
            self.version.setCurrentText(s.datos['version_mc']);self.loader.setCurrentText(s.datos.get('version_loader',''))

    def mostrar_paso(self):
        nombres=('Tipo y versión','Mods','Mundo','Jugadores y acceso','Resumen')
        self.titulo_paso.setText(tr('%s de 5 · %s')%(self.indice+1,tr(nombres[self.indice])));self.stack.setCurrentIndex(self.indice)
        self.atras.setEnabled(self.indice>0);self.siguiente.setText(tr('Crear') if self.indice==4 else tr('Siguiente'))
        if self.indice==4:
            d=self.datos();self.resumen.setText(tr('Se creará %s (%s).\nMinecraft: %s\nMundo: %s · Semilla: %s\nAcceso: %s\nMods adicionales: %s\nWhitelist: %s')%(d['nombre'],d['id'],d['version_mc'],tr('Hardcore') if d['hardcore'] else tr('Normal'),d['semilla'] or tr('Aleatoria'),d['acceso'],', '.join(d['mods']) or tr('Ninguno'),self.whitelist.currentText()))

    def mover(self,delta):
        if self.en_curso:return
        if delta>0 and self.indice==0 and (not self.version.currentText().strip() or self.tipo.currentData()=='copia' and not self.plantilla.currentData()):return
        if delta>0 and self.indice==2 and (not self.nombre.text().strip() or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',self.id.text())):
            self.estado.show();self.estado.setText(tr('Escribe un nombre y un identificador válido'));return
        if delta>0 and self.indice==4:self.crear();return
        self.indice=max(0,min(4,self.indice+delta));self.mostrar_paso()

    def simulado(self):
        s=object.__new__(__import__('telazocraft.motor.servidor',fromlist=['Servidor']).Servidor)
        s.datos={'tipo':self.tipo.currentData(),'version_mc':self.version.currentText()}
        if self.tipo.currentData()=='copia':s=self.parent().biblioteca.servidor(self.plantilla.currentData())
        return s

    def buscar_mods(self):
        if self.buscar.text().strip() and self.tipo.currentData()!='vanilla':
            texto=self.buscar.text().strip();s=self.simulado();self.lanzar(lambda:modrinth.buscar(texto,s),self.busqueda_lista)

    def pintar_busqueda(self,hits):
        self.hits=hits;self.resultados.cargar(hits)

    def elegir_mod(self):
        i=self.resultados.currentRow()
        if 0<=i<len(self.hits):
            slug=self.hits[i]['slug']
            if slug not in self.slugs:self.slugs.append(slug)
            self.mods.setText(', '.join(self.slugs))

    def comparar(self):
        s=self.parent().biblioteca.servidor(self.plantilla.currentData()) if self.plantilla.currentData() else None
        if s:
            version=self.version.currentText();self.lanzar(lambda:asistente.compatibilidad(s,[version]),self.compatibilidad_lista)

    def pintar_comparacion(self,datos):
        self.tabla.setRowCount(len(datos))
        for r,d in enumerate(datos):
            for c,v in enumerate((d['version'],d['compatibles'],d['total'])):self.tabla.setItem(r,c,QTableWidgetItem(str(v)))

    def datos(self):
        copia=self.tipo.currentData()=='copia';s=self.parent().biblioteca.servidor(self.plantilla.currentData()) if copia and self.plantilla.currentData() else None
        return {'id':self.id.text(),'nombre':self.nombre.text(),'tipo':s.datos['tipo'] if s else self.tipo.currentData(),
                'version_mc':s.datos['version_mc'] if s else self.version.currentText().strip(),'version_loader':s.datos.get('version_loader','') if s else self.loader.currentText().strip(),
                'plantilla':self.plantilla.currentData() if copia else None,'hardcore':self.hardcore.isChecked(),'acceso':self.acceso.currentText(),
                'whitelist_de':self.whitelist.currentData(),'mods':list(self.slugs),'semilla':self.semilla.text(),'instalar_java':self.instalar_java.isChecked()}

    def crear(self):
        if not self.eula.isChecked():self.estado.show();self.estado.setText(tr('Debes aceptar la EULA de Minecraft'));return
        datos=self.datos();self.en_curso=True;self.terminado=False;self.stack.hide();self.atras.hide();self.siguiente.hide();self.cancelar.hide()
        self.barra.show();self.estado.show();self.btn_detalle.show();self.btn_cerrar.show();self.mensaje.show();self.titulo_paso.setText(tr('Creando servidor'))
        biblioteca=self.parent().biblioteca
        def hacer():
            try:self.resultado.emit(asistente.crear(biblioteca,**datos,progreso=self.progreso.emit),None)
            except Exception as e:self.resultado.emit(None,str(e))
        self.hilo=threading.Thread(target=hacer,daemon=False);self.hilo.start()

    def finalizar(self,s,error):
        self.en_curso=False;self.creado=s;self.terminar(not error,error or tr('Servidor creado. Ya puedes elegirlo en Telazocraft.'))
        if s:self.parent().recargar_servidores()


class PantallaAsistente:
    def nuevo_servidor(self):
        d=NuevoServidor(self);d.exec()
