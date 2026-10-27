"""Recursos de Windows fabricados desde el mismo contorno de la interfaz."""
import struct
from pathlib import Path
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QPainter, QColor, QPixmap
from .icons import logo_pixmap
from . import style

def guardar_icono(ruta):
    imagenes=[]
    for size in (16,24,32,48,64,128,256):
        buffer=QBuffer();buffer.open(QIODevice.WriteOnly)
        logo_pixmap(size).save(buffer,'PNG');imagenes.append((size,bytes(buffer.data())))
    offset=6+16*len(imagenes);salida=struct.pack('<HHH',0,1,len(imagenes))
    for size,data in imagenes:
        salida+=struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(data),offset);offset+=len(data)
    Path(ruta).write_bytes(salida+b''.join(data for _,data in imagenes))

def imagenes_instalador(ruta):
    carpeta=Path(ruta).parent
    for nombre,ancho,alto,size in (('Wizard',164,314,110),('WizardSmall',55,55,48)):
        pm=QPixmap(ancho,alto);pm.fill(QColor(style.tema_actual().superficie_opaca))
        p=QPainter(pm);p.drawPixmap((ancho-size)//2,(alto-size)//2,logo_pixmap(size));p.end()
        pm.save(str(carpeta/(nombre+'.bmp')),'BMP')
