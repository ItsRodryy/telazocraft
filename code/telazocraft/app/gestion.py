import datetime
import json
import re
from pathlib import Path
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QLabel,QLineEdit,QFormLayout,QTableWidgetItem,QScrollArea,QWidget,QTabWidget,QVBoxLayout,QHBoxLayout,QMenu,QHeaderView
from . import style,icons
from .base import boton,fila,titulo,confirmar,Dialogo,Log,opciones_boton,vaciar_tabla
from .widgets.tabla_datos import TablaDatos
from .widgets.spin_box import SpinBox,ComboSinRueda,SliderSinRueda
from .widgets.check_box import CheckBox
from .widgets.toggle import Toggle
from .widgets.boton_carpeta import BotonCarpeta,abrir_carpeta
from .widgets.etiqueta_elidida import EtiquetaElidida
from ..common import ajustes
from ..common.i18n import tr
from ..motor import jugadores,propiedades,copias,mojang,java
from ..motor.diario import Diario
from ..motor.tiempos import sesiones_jugadores,horas_encendido
from ..motor.sync import GuardiaSync
from ..motor.util import leer_json
from .. import __version__
from ..common import github_releases


def fecha_legible(valor):
    if not valor:return tr('sin uso registrado')
    try:
        d=datetime.datetime.fromisoformat(str(valor)).astimezone()
        meses=('ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic')
        return tr('%s %s %s, %s')%(d.day,tr(meses[d.month-1]),d.year,d.strftime('%H:%M'))
    except ValueError:return str(valor)


def hace(marca):
    minutos=max(0,int((datetime.datetime.now().timestamp()-marca)//60))
    if minutos<60:return tr('hace %s min')%minutos
    if minutos<48*60:return tr('hace %s h')%(minutos//60)
    return tr('hace %s días')%(minutos//1440)


def duracion_legible(horas):
    minutos=round(horas*60)
    if minutos<1:return tr('<1 min')
    if minutos<60:return tr('%s min')%minutos
    return tr('%s h %02d min')%(minutos//60,minutos%60) if minutos%60 else tr('%s h')%(minutos//60)


def chip(*pares):
    """Una o varias pastillas alineadas a la izquierda: chip('Ambos') o chip(('Al día','ok'),...)."""
    caja=style.agrupador();h=QHBoxLayout(caja);h.setContentsMargins(4,0,4,0);h.setSpacing(6)
    for par in pares:
        texto,tono=(par,'') if isinstance(par,str) else par
        w=QLabel(tr(texto));w.setProperty('chip',True);w.setProperty('tono',tono);h.addWidget(w,0,Qt.AlignVCenter)
    h.addStretch();return caja


def limpiar(layout):
    while layout.count():
        item=layout.takeAt(0)
        # Ocultar antes de deleteLater: si no, el widget viejo se pinta un instante encima del nuevo.
        if item.widget():item.widget().hide();item.widget().deleteLater()


class Grafica(QWidget):
    def __init__(self,nombre,clave,maximo):
        super().__init__();self.nombre,self.clave,self.maximo=nombre,clave,maximo;self.muestras=[];self.setFixedHeight(130)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);t=style.tema_actual();p.setPen(QColor(t.texto_tenue))
        datos=[d[self.clave] for d in self.muestras[-120:] if d.get(self.clave) is not None]
        p.drawText(12,22,tr('%s · %s')%(self.nombre,f'{datos[-1]:.1f}' if datos else tr('sin datos')))
        techo=self.maximo or max([1]+datos);p.setPen(QPen(QColor(t.borde),1))
        p.drawLine(34,36,34,self.height()-24);p.drawLine(34,self.height()-24,self.width()-12,self.height()-24)
        p.setPen(QColor(t.texto_tenue))
        p.drawText(2,42,f'{techo:.0f}');p.drawText(12,self.height()-24,'0');p.drawText(34,self.height()-5,tr('Sesión'));p.drawText(self.width()-55,self.height()-5,tr('Ahora'))
        if len(datos)>1:
            techo=self.maximo or max(1,max(datos));p.setPen(QPen(QColor(t.acento_claro),2))
            p.drawPolyline(QPolygonF([QPointF(34+i*(self.width()-46)/(len(datos)-1),self.height()-24-min(techo,max(0,v))/techo*(self.height()-62)) for i,v in enumerate(datos)]))
        p.end()


class PantallasGestion:
    def construir_gestion(self):
        self.inicio_nombre=titulo('Servidor');self.inicio_detalle=QLabel();self.inicio_detalle.setWordWrap(True)
        self.inicio_uso=QLabel();self.inicio_uso.setWordWrap(True);self.inicio_uso.setObjectName('tenue')
        self.inicio_direccion=QLineEdit();self.inicio_direccion.setReadOnly(True);self.inicio_direccion.setPlaceholderText(tr('Dirección de Playit sin configurar'))
        self.paginas['Inicio'].layout().addWidget(style.tarjeta(self.inicio_nombre,self.inicio_detalle,fila(self.inicio_direccion,boton('Copiar',self.copiar_direccion)),self.inicio_uso))
        self.conectados_caja=style.agrupador();self.conectados_caja.setLayout(QHBoxLayout());self.conectados_caja.layout().setContentsMargins(0,0,0,0)
        self.paginas['Inicio'].layout().addWidget(style.tarjeta(titulo('Conectados'),self.conectados_caja))
        self.resumen_valores={};resumen=style.agrupador();h=QHBoxLayout(resumen);h.setContentsMargins(0,0,0,0);h.setSpacing(style.SEPARACION_PANELES)
        for clave,etiqueta in (('jugadores','Jugadores'),('horas','Horas jugadas'),('encendido','Horas encendido'),('mods','Mods'),('copia','Última copia')):
            valor=QLabel('—');valor.setObjectName('cifra');rotulo=QLabel(tr(etiqueta));rotulo.setObjectName('tenue')
            self.resumen_valores[clave]=valor;h.addWidget(style.tarjeta(valor,rotulo),1)
        self.paginas['Inicio'].layout().addWidget(resumen)
        self.partidas_caja=style.agrupador();self.partidas_caja.setLayout(QVBoxLayout());self.partidas_caja.layout().setContentsMargins(0,0,0,0);self.partidas_caja.layout().setSpacing(4)
        self.paginas['Inicio'].layout().addWidget(style.tarjeta(titulo('Últimas partidas'),self.partidas_caja))
        self.graficas=[Grafica(tr('CPU (%)'),'cpu_pct',100),Grafica(tr('Java (MB)'),'ram_mb',None),Grafica(tr('TPS'),'tps',20)]
        self.graficas_panel=style.agrupador();graficas_layout=QHBoxLayout(self.graficas_panel);graficas_layout.setContentsMargins(0,0,0,0)
        for g in self.graficas:graficas_layout.addWidget(style.tarjeta(g),1)
        self.paginas['Inicio'].layout().addWidget(self.graficas_panel);self.paginas['Inicio'].layout().addStretch()
        self.timer_metricas=QTimer(self);self.timer_metricas.setInterval(5000);self.timer_metricas.timeout.connect(self.medir)
        self.datos_jugadores=[]
        self.tabla_jugadores=TablaDatos([tr(s) for s in ('Jugador','Estado','Horas','Última conexión','Permisos','')],columnas_accion=(5,),columna_estirada=0,anchos={0:200,1:140,2:110,3:180,4:220,5:52})
        self.tabla_jugadores.verticalHeader().setDefaultSectionSize(46)
        self.tabs_jugadores=QTabWidget();self.tabs_jugadores.addTab(self.tabla_jugadores,tr('Lista'))
        actividad=style.agrupador();v=QVBoxLayout(actividad);v.setContentsMargins(0,0,0,0)
        self.filtro_diario=QLineEdit();self.filtro_diario.setPlaceholderText(tr('Filtrar por jugador'));self.filtro_diario.textChanged.connect(self.actualizar_diario);v.addWidget(self.filtro_diario)
        self.tabla_diario=TablaDatos([tr(s) for s in ('Fecha','Evento','Jugador','Detalle')],columna_estirada=3,anchos={0:170,1:110,2:150,3:280});v.addWidget(self.tabla_diario)
        self.tabs_jugadores.addTab(actividad,tr('Actividad'))
        anadir=boton('Añadir a la whitelist',self.anadir_whitelist,True);anadir.setIcon(icons.glifo('mas',16))
        self.paginas['Jugadores'].layout().addWidget(style.tarjeta(fila(titulo('Jugadores'),anadir),self.tabs_jugadores))
        self.copias_datos=[];self.copias_contenido=style.agrupador();self.copias_layout=QVBoxLayout(self.copias_contenido);self.copias_layout.setContentsMargins(0,0,0,0)
        self.crear_copia_boton=boton('Copia ahora',self.copia_ahora,True)
        self.paginas['Copias'].layout().addWidget(style.tarjeta(fila(titulo('Copias'),self.crear_copia_boton)))
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);scroll.setWidget(self.copias_contenido);self.paginas['Copias'].layout().addWidget(scroll,1)
        self.construir_ajustes()
        pagina=self.paginas['Inicio'];contenido=style.agrupador();interior=QVBoxLayout(contenido);interior.setContentsMargins(0,0,0,0);interior.setSpacing(style.SEPARACION_PANELES)
        while pagina.layout().count():
            item=pagina.layout().takeAt(0)
            if item.widget():interior.addWidget(item.widget())
            else:interior.addItem(item)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);scroll.setWidget(contenido);pagina.layout().addWidget(scroll)

    def actualizar_inicio(self):
        s=self.servidor
        if not s:return
        self.inicio_nombre.setText(s.nombre)
        d=s.datos;estado=self.control.estado if self.control else tr('apagado')
        tipo={'neoforge':'NeoForge','vanilla':'Vanilla'}.get(d['tipo'],d['tipo'])
        self.inicio_detalle.setText(tr('%s · %s · Minecraft %s · %s · %.1f GB de RAM')%(tr(estado.capitalize()),tipo,d['version_mc'],tr('Solo premium') if d['acceso']=='premium' else tr('Acceso abierto'),d['ram_mb']/1024))
        diario=self.registros()
        registros=[r for r in diario if r.get('tipo') in ('arranque','entrada')];ultimo=max(registros,key=lambda r:r.get('fecha',''),default={})
        self.resumen_valores['jugadores'].setText(str(len(self.datos_jugadores)))
        self.resumen_valores['horas'].setText(duracion_legible(sum(j['horas'] for j in self.datos_jugadores)))
        self.resumen_valores['encendido'].setText(duracion_legible(horas_encendido(diario,bool(self.control and self.control.estado=='encendido'))))
        self.resumen_valores['mods'].setText(str(len(self.mods_datos)))
        self.resumen_valores['copia'].setText(hace(self.copias_datos[0].stat().st_mtime) if self.copias_datos else tr('Ninguna'))
        limpiar(self.partidas_caja.layout())
        partidas=sorted((r for r in diario if r.get('tipo')=='salida' and r.get('jugador')),key=lambda r:r.get('fecha',''),reverse=True)[:6]
        _,vivas=sesiones_jugadores(diario,self.control.consola.jugadores if self.control else (),self.control.consola.entradas if self.control else {})
        partidas=(vivas+partidas)[:6]
        if not partidas:self.partidas_caja.layout().addWidget(QLabel(tr('Todavía no ha jugado nadie')))
        for r in partidas:
            cara=QLabel();cara.setPixmap(self.cabeza(r['jugador']).pixmap(20,20))
            cuando=QLabel(tr('jugando') if r.get('en_curso') else fecha_legible(r.get('fecha')));cuando.setObjectName('tenue')
            linea=fila(cara,QLabel(r['jugador']),cuando)
            if 'duracion_seg' in r:linea.layout().addWidget(QLabel(duracion_legible(r['duracion_seg']/3600)))
            self.partidas_caja.layout().addWidget(linea)
        total=self.resumenes.get(s.id,{}).get('tamano',0)
        self.inicio_uso.setText(tr('Último uso: %s · %s · %.2f GB')%(fecha_legible(ultimo.get('fecha')),ultimo.get('equipo',tr('equipo sin registrar')),total/2**30))
        self.inicio_direccion.setText(self.direccion.text())
        limpiar(self.conectados_caja.layout());conectados=list(self.control.consola.jugadores) if self.control else []
        if not conectados:self.conectados_caja.layout().addWidget(QLabel(tr('Nadie conectado')))
        for nick in conectados:
            cara=QLabel();cara.setPixmap(self.cabeza(nick).pixmap(28,28));self.conectados_caja.layout().addWidget(fila(cara,QLabel(nick)))
        self.conectados_caja.layout().addStretch()

    def cargar_cabezas_automaticas(self):
        import threading,urllib.request
        if not self.persistir:return
        if not hasattr(self,'cabezas_pedidas'):self.cabezas_pedidas=set()
        nombres=[d['nick'] for d in self.datos_jugadores if d['nick'] not in self.cabezas_pedidas]
        self.cabezas_pedidas.update(nombres)
        if not nombres:return
        id=self.selector.currentData()
        def descargar():
            for nick in nombres:
                if not re.fullmatch(r'[A-Za-z0-9_]{1,16}',nick):continue
                p=ajustes.ruta().parent/'cabezas'/(nick+'.png')
                if p.exists():continue
                try:
                    with urllib.request.urlopen('https://mc-heads.net/avatar/'+nick+'/64',timeout=5) as r:data=r.read(1024*1024)
                    if data.startswith(b'\x89PNG\r\n\x1a\n'):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                except OSError:pass
            self.bus.evento.emit(id,'cabezas',None)
        threading.Thread(target=descargar,daemon=True).start()

    def actualizar_jugadores(self):
        if self.servidor:self.pintar_jugadores(self.jugadores_actuales())

    def pintar_jugadores(self,datos):
        self.datos_jugadores=datos;vaciar_tabla(self.tabla_jugadores);self.tabla_jugadores.setRowCount(len(datos))
        for r,d in enumerate(datos):
            for col,v in enumerate((d['nick'],None,duracion_legible(d['horas']) if d['horas'] else '—',fecha_legible(d['ultima']))):
                if v is None:continue
                item=QTableWidgetItem(str(v));item.setToolTip(str(v))
                if col==0:item.setIcon(self.cabeza(d['nick']))
                self.tabla_jugadores.setItem(r,col,item)
            self.tabla_jugadores.setCellWidget(r,1,chip((tr('Conectado'),'ok') if d['conectado'] else tr('Desconectado')))
            etiquetas=[(tr(label),tono) for key,label,tono in (('whitelist.json','Whitelist',''),('ops.json','OP','aviso'),('banned-players.json','Baneado','peligro')) if d.get(key)]
            self.tabla_jugadores.setCellWidget(r,4,chip(*etiquetas) if etiquetas else chip(tr('Sin permisos')))
            b=opciones_boton(lambda checked=False,d=d:self.menu_jugador(d));b.setToolTip(tr('Acciones del jugador'));self.tabla_jugadores.setCellWidget(r,5,b)

    def menu_jugador(self,d):
        menu=QMenu(self)
        opciones=[('Expulsar','kick'),('Desbanear' if d.get('banned-players.json') else 'Banear','pardon' if d.get('banned-players.json') else 'ban'),('Quitar de la whitelist' if d.get('whitelist.json') else 'Añadir a la whitelist','whitelist remove' if d.get('whitelist.json') else 'whitelist add'),('Quitar OP' if d.get('ops.json') else 'Dar OP','deop' if d.get('ops.json') else 'op')]
        for label,accion in opciones:
            a=menu.addAction(tr(label));a.triggered.connect(lambda checked=False,a=accion:self.accion_jugador(a,d['nick']))
            if accion=='kick' and not d['conectado']:a.setEnabled(False);a.setToolTip(tr('El jugador no está conectado'))
        menu.exec(self.cursor().pos())

    def anadir_whitelist(self):
        d=Dialogo(self,'Añadir a la whitelist');nick=QLineEdit();nick.setPlaceholderText(tr('Nombre de jugador'));d.formulario.addWidget(nick);d.terminar_botones('Continuar')
        if d.exec():self.accion_jugador('whitelist add',nick.text().strip())

    def accion_jugador(self,accion,nick):
        if not self.servidor or not re.fullmatch(r'[A-Za-z0-9_]{1,16}',nick):self.mostrar_error(tr('Nombre de jugador no válido'));return
        s,c=self.servidor,self.control;antes=next((d for d in self.datos_jugadores if d['nick'].casefold()==nick.casefold()),{})
        lista='whitelist' if accion.startswith('whitelist') else 'ops' if accion in ('op','deop') else 'banned-players'
        agregar=accion not in ('deop','whitelist remove','pardon')
        if not confirmar(self,tr('Cambio de permisos para %s')%nick,'Aplicar acción',[(tr('Acción'),tr('Sin cambio'),accion),(lista,bool(antes.get(lista+'.json')),agregar)],accion in ('ban','op','kick')):return
        if c and c.proceso.vivo:c.comando(accion+' '+nick)
        elif accion=='kick':self.mostrar_error(tr('El servidor está apagado'))
        else:self.trabajo(lambda:jugadores.modificar_lista(s,nick,lista,agregar),lambda _:self.refrescar())

    def medir(self):
        if not self.control or self.control.estado!='encendido' or self.stack.currentWidget() is not self.paginas['Inicio'] or not self.isVisible():return
        try:
            for g in self.graficas:g.muestras=list(self.control.rendimiento.muestras);g.update()
        except Exception as exc:self.mostrar_error(str(exc))

    def actualizar_diario(self,*_):
        if not self.servidor:return
        filtro=self.filtro_diario.text().casefold();datos=sorted(self.registros(),key=lambda r:r.get('fecha',''),reverse=True)
        datos=[d for d in datos if not filtro or filtro in d.get('jugador','').casefold()]
        self.tabla_diario.setRowCount(len(datos))
        for r,d in enumerate(datos):
            detalle=duracion_legible(d['duracion_seg']/3600) if 'duracion_seg' in d else str(d.get('detalle',d.get('copia',d.get('semilla',''))))
            if d.get('origen')=='logs':detalle=(detalle+' · '+tr('Importado de logs')).strip(' ·')
            for c,v in enumerate((fecha_legible(d.get('fecha')),tr(d.get('tipo','').capitalize()),d.get('jugador',''),detalle)):self.tabla_diario.setItem(r,c,QTableWidgetItem(v))

    def construir_ajustes(self):
        self.ajustes_campos={};self.rotulos_ajustes={};self.borradores={};self.cargando_ajustes=False;self.id_editando=None;self.ajustes_aplicados={}
        contenido=style.agrupador();v=QVBoxLayout(contenido);v.setContentsMargins(0,0,0,0);v.setSpacing(style.SEPARACION_PANELES)
        secciones=[('General',[('nombre','Nombre','texto',None),('motd','MOTD','texto',None),('ram_mb','RAM','slider',(512,65536,4096)),('reinicio_h','Reinicio cada N h (0 desactiva)','numero',(0,168,2)),('apagar_si_vacio_min','Apagar si vacío (min)','numero',(0,1440,10))]),('Mundo',[('difficulty','Dificultad','combo',('peaceful','easy','normal','hard')),('pvp','PvP','toggle',None),('max-players','Máximo de jugadores','numero',(1,1000,20)),('view-distance','Distancia de visión','numero',(2,32,10)),('simulation-distance','Distancia de simulación','numero',(2,32,10))]),('Acceso',[('acceso','Acceso','combo',('abierto','premium')),('white-list','Whitelist activa','toggle',None)]),('Copias',[('locales','Locales','numero',(1,100,4)),('sesion','Sesión','numero',(1,100,3)),('diarias','Diarias','numero',(1,100,5))]),('Hardcore',[('hardcore','Hardcore','toggle',None),('gracia_seg','Gracia (segundos)','numero',(0,3600,30)),('partidas_guardadas','Partidas guardadas','numero',(1,100,3)),('freno_reinicios','Freno de reinicios','numero',(0,100,0))]),('Extras de cliente',[('extras_cliente','Mods del ZIP (separados por comas)','texto',None)])]
        for nombre,campos in secciones:
            form=QFormLayout();form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);form.setLabelAlignment(Qt.AlignLeft);interior=style.agrupador();interior.setLayout(form)
            panel=style.tarjeta(titulo(nombre),interior);v.addWidget(panel)
            if nombre=='Hardcore':self.hardcore_panel=panel
            for key,label,tipo,lim in campos:
                if tipo=='numero':w=SpinBox();w.setRange(*lim[:2]);w.setValue(lim[2]);w.valueChanged.connect(self.marcar_ajustes)
                elif tipo=='slider':
                    w=SliderSinRueda(Qt.Horizontal);w.setRange(*lim[:2]);w.setSingleStep(512);w.setValue(lim[2]);w.valueChanged.connect(self.marcar_ajustes)
                elif tipo=='combo':
                    w=ComboSinRueda()
                    etiquetas={'peaceful':tr('Pacífico'),'easy':tr('Fácil'),'normal':tr('Normal'),'hard':tr('Difícil'),'abierto':tr('Abierto'),'premium':tr('Solo premium')}
                    for valor in lim:w.addItem(etiquetas[valor],valor)
                    w.currentIndexChanged.connect(self.marcar_ajustes)
                elif tipo=='toggle':w=Toggle();w.toggled.connect(self.marcar_ajustes)
                else:w=QLineEdit();w.textChanged.connect(self.marcar_ajustes)
                rotulo=QLabel(tr(label));rotulo.setObjectName('rotuloParametro');self.rotulos_ajustes[key]=label;self.ajustes_campos[key]=w
                if tipo=='slider':
                    valor=QLabel();w.valueChanged.connect(lambda n,l=valor:l.setText(tr('%.1f GB')%(n/1024)));valor.setText(tr('4.0 GB'));form.addRow(rotulo,fila(w,valor))
                else:form.addRow(rotulo,w)
            if nombre=='Acceso':
                ayuda=QLabel(tr('Abierto admite acceso offline y premium. Solo premium verifica la cuenta. Cambiar el acceso crea una copia y migra los personajes.'));ayuda.setWordWrap(True);ayuda.setObjectName('tenue');panel.layout().addWidget(ayuda)
            if nombre=='Mundo':
                self.radio_chunky=SpinBox();self.radio_chunky.setRange(32,30000);self.radio_chunky.setValue(1000);self.radio_chunky.setSuffix(tr(' bloques'))
                detalle=QLabel(tr('Genera el terreno por adelantado para que explorar no dé tirones.'));detalle.setWordWrap(True);panel.layout().addWidget(titulo('Pregenerar mundo'));panel.layout().addWidget(detalle)
                self.chunky_en_curso=False;self.pregenerar_boton=boton('Pregenerar',self.pregenerar);self.cancelar_chunky_boton=boton('Cancelar',self.cancelar_chunky)
                panel.layout().addWidget(fila(self.radio_chunky,self.pregenerar_boton,self.cancelar_chunky_boton))
                self.progreso_chunky=QLabel(tr('Chunky: sin tarea'));panel.layout().addWidget(self.progreso_chunky)
        v.addStretch();scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);scroll.setWidget(contenido);self.paginas['Ajustes'].layout().addWidget(scroll,1)
        self.aplicar_ajustes_boton=boton('Aplicar',self.aplicar_ajustes,True)
        self.pendientes_barra=style.tarjeta(fila(QLabel(tr('Cambios sin aplicar')),boton('Descartar',self.restablecer_ajustes),self.aplicar_ajustes_boton));self.paginas['Ajustes'].layout().addWidget(self.pendientes_barra);self.pendientes_barra.hide()

    def valor_campo(self,w):
        return int(w.value()) if isinstance(w,(SpinBox,SliderSinRueda)) else (w.currentData() or w.currentText()) if isinstance(w,ComboSinRueda) else w.isChecked() if isinstance(w,(Toggle,CheckBox)) else w.text()

    def valores_ajustes(self):return {k:self.valor_campo(w) for k,w in self.ajustes_campos.items()}

    def marcar_ajustes(self,*_):
        if self.cargando_ajustes or not self.id_editando:return
        valores=self.valores_ajustes()
        if valores==self.ajustes_aplicados:self.borradores.pop(self.id_editando,None)
        else:self.borradores[self.id_editando]=valores
        pendiente=self.id_editando in self.borradores;self.pendientes_barra.setVisible(pendiente);self.aplicar_ajustes_boton.setProperty('pendiente',pendiente)

    def actualizar_copias(self):
        if not self.servidor:return
        limpiar(self.copias_layout)
        if not self.copias_datos:self.copias_layout.addWidget(style.tarjeta(QLabel(tr('Todavía no hay copias'))))
        for p in self.copias_datos:
            tipo=(tr('Partida'),'peligro') if p.parent.name=='partidas' else (tr('Diaria'),'ok') if 'diaria' in p.name else tr('Sesión') if 'sesion' in p.name else tr('Local')
            fecha=fecha_legible(datetime.datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat());b=opciones_boton(lambda checked=False,p=p:self.menu_copia(p));b.setToolTip(tr('Acciones de la copia'))
            tamano=QLabel(tr('%.1f MB')%(p.stat().st_size/2**20));tamano.setObjectName('tenue')
            tarjeta=fila(titulo(fecha),chip(tipo));tarjeta.layout().addWidget(tamano);tarjeta.layout().addWidget(b)
            self.copias_layout.addWidget(style.tarjeta(tarjeta))
        self.copias_layout.addStretch()

    def menu_copia(self,p):
        menu=QMenu(self);a=menu.addAction(tr('Restaurar'),lambda:self.restaurar_copia(p));a.setEnabled(not self.biblioteca.lock.exists());a.setToolTip(tr('Requiere servidor parado'));menu.addAction(tr('Abrir carpeta'),lambda:abrir_carpeta(str(p.parent)));menu.exec(self.cursor().pos())

    def copia_ahora(self):
        s=self.servidor
        if s and confirmar(self,tr('Se creará una copia del mundo del servidor parado.'),'Crear copia',[(tr('Copias'),len(self.copias_datos),len(self.copias_datos)+1)]):self.trabajo(lambda:copias.crear(s,progreso=lambda n,t:self.bus.evento.emit(s.id,'progreso',{'valor':n,'texto':t})),lambda _:self.refrescar())

    def restaurar_copia(self,p):
        s=self.servidor
        if s and confirmar(self,tr('El mundo actual se apartará en archivo. Se perderá el progreso posterior a esta copia en el mundo activo.'),'Restaurar copia',[(tr('Mundo activo'),tr('Actual'),p.name)],True):self.trabajo(lambda:copias.restaurar(s,p),lambda _:self.refrescar())

    def construir_sistema(self):
        self.sistema_dialogo=Dialogo(self,'Telazocraft');self.sistema_dialogo.resize(660,500)
        contenedor=style.agrupador();contenedor.setLayout(QVBoxLayout());self.sistema_dialogo.formulario.addWidget(contenedor)
        self.sistema_contenido=contenedor
        self.direccion=QLineEdit(leer_json(self.biblioteca.raiz/'telazocraft.json').get('direccion',''));self.direccion.setReadOnly(True)
        self.actualizacion=None;self.actualizar_app_boton=boton('Instalar actualización',self.instalar_actualizacion,True);self.actualizar_app_boton.setEnabled(False)
        self.sistema_texto=QLabel(tr('Consultando el estado…'));self.sistema_texto.setWordWrap(True)
        version=QLabel(tr('Versión %s')%__version__);version.setObjectName('tenue')
        contenedor.layout().addWidget(style.tarjeta(titulo('Telazocraft'),version,fila(boton('Buscar actualizaciones',self.buscar_actualizacion),self.actualizar_app_boton)))
        contenedor.layout().addWidget(style.tarjeta(titulo('Estado del equipo'),self.sistema_texto))
        self.biblioteca_etiqueta=EtiquetaElidida(str(self.biblioteca.raiz))
        contenedor.layout().addWidget(style.tarjeta(titulo('Biblioteca'),self.biblioteca_etiqueta,fila(BotonCarpeta(lambda:str(self.biblioteca.raiz),tr('Abrir biblioteca')),boton('Cambiar biblioteca',self.cambiar_biblioteca))))
        contenedor.layout().addStretch()

    def abrir_sistema(self):
        self.refrescar_sistema();self.sistema_dialogo.show();self.sistema_dialogo.raise_();self.sistema_dialogo.activateWindow()

    def cambiar_biblioteca(self):
        from PySide6.QtWidgets import QFileDialog
        if self.biblioteca.lock.exists():self.mostrar_error(tr('Detén el servidor antes de cambiar de biblioteca'));return
        ruta=QFileDialog.getExistingDirectory(self,tr('Elige una biblioteca'))
        if not ruta:return
        from ..motor.biblioteca import Biblioteca
        nueva=Biblioteca(ruta)
        if confirmar(self,tr('Se cambiará la biblioteca de esta aplicación.'),'Cambiar biblioteca',[(tr('Biblioteca'),str(self.biblioteca.raiz),str(nueva.raiz))]):
            for hilo in self.lectores:hilo.join(5)
            self.biblioteca=nueva;self.resumenes.clear();self.logs_importados.clear();self.resumen_cargando.clear();self.mods_enriquecidos.clear();self.biblioteca_etiqueta.setText(str(nueva.raiz));self.recargar_servidores()

    def refrescar_sistema(self):
        control=self.control;biblioteca=self.biblioteca
        def leer():
            try:sync=GuardiaSync(biblioteca).estado();estado=tr('Al día') if sync.get('state')=='idle' and not sync.get('needFiles') else tr('Sincronizando') if sync.get('disponible') else tr('No configurado')
            except OSError:estado=tr('Sin conexión')
            versiones=sorted({int(j['mayor']) for j in java.detectar()})
            return tr('Playit: %s\nSyncthing: %s\nJava: %s')%(tr('Activo') if control and control.playit.vivo else tr('Apagado'),estado,', '.join(map(str,versiones)) or tr('no encontrado'))
        self.trabajo(leer,self.sistema_texto.setText)

    def actualizar_bloqueos(self):
        parado=not self.biblioteca.lock.exists() and not self.trabajos
        self.aplicar_ajustes_boton.setEnabled(parado);self.aplicar_ajustes_boton.setToolTip('' if parado else tr('Detén el servidor para aplicar cambios'))
        self.crear_copia_boton.setEnabled(parado);self.crear_copia_boton.setToolTip('' if parado else tr('Detén el servidor para crear la copia'))
        encendido=bool(self.control and self.control.estado=='encendido')
        if not encendido:self.chunky_en_curso=False
        self.pregenerar_boton.setEnabled(encendido and not self.chunky_en_curso);self.pregenerar_boton.setToolTip('' if encendido else tr('Inicia el servidor para pregenerar'))
        self.cancelar_chunky_boton.setEnabled(self.chunky_en_curso);self.cancelar_chunky_boton.setToolTip('' if self.chunky_en_curso else tr('No hay ninguna pregeneración en curso'))
        if hasattr(self,'anadir_mod_boton'):
            self.anadir_mod_boton.setEnabled(parado);self.anadir_mod_boton.setToolTip('' if parado else tr('Detén el servidor para cambiar mods'))
    def cabeza(self, nick):
        avatar=ajustes.ruta().parent/'cabezas'/(nick+'.png')
        if avatar.exists():
            icono=QIcon(str(avatar))
            if not icono.isNull():return icono
        cache = ajustes.ruta().parent / "skins" / (nick + ".png")
        imagen = QImage(str(cache)) if cache.exists() else QImage()
        if not imagen.isNull() and imagen.width() >= 64 and imagen.height() >= 32:
            cara = imagen.copy(8, 8, 8, 8).scaled(32, 32)
            p = QPainter(cara)
            p.drawImage(cara.rect(), imagen.copy(40, 8, 8, 8))
            p.end()
            return QIcon(QPixmap.fromImage(cara))
        mapa = QPixmap(32, 32)
        mapa.fill(QColor(style.tema_actual().acento))
        p = QPainter(mapa)
        p.setPen(QColor(style.tema_actual().sobre_acento))
        p.fillRect(6, 10, 6, 5, QColor(style.tema_actual().sobre_acento))
        p.fillRect(20, 10, 6, 5, QColor(style.tema_actual().sobre_acento))
        p.drawLine(10, 24, 22, 24)
        p.end()
        return QIcon(mapa)

    def cargar_skins(self):
        nombres = [d["nick"] for d in self.datos_jugadores]
        def cargar():
            carpeta = ajustes.ruta().parent / "skins"
            carpeta.mkdir(parents=True, exist_ok=True)
            fallos = 0
            for nick in nombres:
                if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", nick):
                    continue
                if not (carpeta / (nick + ".png")).exists():
                    try:
                        (carpeta / (nick + ".png")).write_bytes(jugadores.textura(nick))
                    except (OSError, ValueError, KeyError, StopIteration):
                        fallos += 1
            return fallos
        self.trabajo(cargar, lambda fallos: (self.pintar_jugadores(self.datos_jugadores), self.aviso.setText(tr("Skins no disponibles: %s") % fallos)))

    def restablecer_ajustes(self):
        if self.servidor:
            self.borradores.pop(self.servidor.id, None)
            self.cargar_ajustes()

    def cargar_ajustes(self):
        s=self.servidor
        if not s:return
        self.cargando_ajustes=True;self.id_editando=s.id
        d={**propiedades.leer(s.ruta/'server.properties'),**s.datos,**s.datos.get('copias',{}),**(s.datos.get('hardcore') or {})}
        d['hardcore']=bool(s.datos.get('hardcore'));d['extras_cliente']=','.join(s.datos.get('extras_cliente',[]))
        def poner(w,v):
            if isinstance(w,(SpinBox,SliderSinRueda)):
                if v is not None:w.setValue(int(float(v)))
            elif isinstance(w,ComboSinRueda):
                if v is not None:w.setCurrentIndex(max(0,w.findData(str(v))))
            elif isinstance(w,(CheckBox,Toggle)):w.setChecked(v is True or str(v).lower()=='true')
            else:w.setText(str(v or ''))
        for k,w in self.ajustes_campos.items():poner(w,d.get(k))
        self.ajustes_aplicados=self.valores_ajustes()
        for k,v in self.borradores.get(s.id,{}).items():poner(self.ajustes_campos[k],v)
        self.cargando_ajustes=False;pendiente=s.id in self.borradores
        self.pendientes_barra.setVisible(pendiente);self.hardcore_panel.setVisible(bool(s.datos.get('hardcore')))
        self.aplicar_ajustes_boton.setProperty('pendiente',pendiente)
        self.aplicar_ajustes_boton.style().unpolish(self.aplicar_ajustes_boton);self.aplicar_ajustes_boton.style().polish(self.aplicar_ajustes_boton)

    def aplicar_ajustes(self):
        s = self.servidor
        if not s:
            return
        valores = {}
        for k, w in self.ajustes_campos.items():
            valores[k] = int(w.value()) if isinstance(w, (SpinBox, SliderSinRueda)) else (w.currentData() or w.currentText()) if isinstance(w, ComboSinRueda) else w.isChecked() if isinstance(w, (CheckBox, Toggle)) else w.text()
        anteriores = self.ajustes_aplicados
        cambios = [(self.rotulos_ajustes[k], anteriores.get(k,""), v) for k,v in valores.items() if v != anteriores.get(k)]
        if not cambios or not confirmar(self, tr("Estos cambios se aplicarán al servidor parado."), "Aplicar cambios", cambios):
            return
        cambio_acceso = valores["acceso"] != s.datos["acceso"]
        def aplicar():
            s.exigir_parado()
            avisos = mojang.migrar(s, valores["acceso"]) if cambio_acceso else []
            for k in ("nombre", "ram_mb", "reinicio_h", "apagar_si_vacio_min"):
                s.datos[k] = valores[k]
            s.datos["copias"] = {k: valores[k] for k in ("locales", "sesion", "diarias")}
            s.datos["extras_cliente"] = [x.strip() for x in valores["extras_cliente"].split(",") if x.strip()]
            s.datos["hardcore"] = {k: valores[k] for k in ("gracia_seg", "partidas_guardadas", "freno_reinicios")} if valores["hardcore"] else None
            propiedades.escribir(s.ruta / "server.properties", {k: valores[k] for k in ("max-players", "view-distance", "simulation-distance", "motd", "difficulty", "pvp", "white-list", "hardcore")})
            args = s.ruta / "user_jvm_args.txt"
            texto = args.read_text(encoding="utf-8") if args.exists() else "-Xms1024M\n-Xmx4096M\n"
            texto = re.sub(r"(?m)^-Xms\S+", f"-Xms{valores['ram_mb']}M", texto)
            texto = re.sub(r"(?m)^-Xmx\S+", f"-Xmx{valores['ram_mb']}M", texto)
            args.write_text(texto, encoding="utf-8")
            s.guardar()
            return avisos
        def aplicado(avisos):
            self.borradores.pop(s.id, None)
            self.cargar_ajustes()
            self.aviso.setText(tr("Ajustes guardados. %s") % "; ".join(avisos))
        self.trabajo(aplicar, aplicado)

