"""Búsqueda con antirrebote y descarte de respuestas de consultas anteriores."""
import logging
import threading
from PySide6.QtCore import QObject,Signal,QTimer
from ..motor import modrinth

class BusquedaMods(QObject):
    listo=Signal(object)
    estado=Signal(str)
    respuesta=Signal(int,object,object)
    def __init__(self,padre,servidor):
        super().__init__(padre);self.servidor=servidor;self.generacion=0;self.texto=''
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(300);self.timer.timeout.connect(self.consultar)
        self.respuesta.connect(self.recibir)
    def cambiar(self,texto):
        self.texto=texto.strip();self.generacion+=1;self.timer.stop()
        if self.texto:self.timer.start()
        else:self.listo.emit([]);self.estado.emit('')
    def consultar(self):
        if not self.texto:return
        texto=self.texto;numero=self.generacion;s=self.servidor();self.estado.emit('Buscando…')
        def hacer():
            try:datos,error=modrinth.buscar(texto,s),None
            except Exception as exc:
                logging.getLogger(__name__).exception('Falló la búsqueda de mods');datos,error=[],str(exc)
            try:self.respuesta.emit(numero,datos,error)
            except RuntimeError:pass
        threading.Thread(target=hacer,daemon=True).start()
    def recibir(self,numero,datos,error):
        if numero!=self.generacion:return
        self.estado.emit('No se pudo buscar: '+error if error else '')
        if not error:self.listo.emit(datos)
