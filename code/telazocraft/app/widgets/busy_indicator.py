# -*- coding: utf-8 -*-
"""Indicador de "estoy en ello", en la barra superior.

Un arco girando y un texto. Existe porque hay cosas que tardan y que la interfaz no puede acelerar
-abrir la camara, reconectarla, leer el catalogo GenICam (~1,5 s), volcar el diagnostico, comprobar
los requisitos del equipo-, y sin una senal el programa parece colgado justo cuando lo que esta es
trabajando.

Nada de esto bloquea el hilo de Qt: el trabajo lento ya vive en el hilo de camara o en hilos
sueltos. Esto solo lo CUENTA.

Vectorial, dibujado con QPainter: nitido a cualquier escalado y sin un GIF que mantener. Cuando no
hay nada en marcha, el temporizador se para: un widget invisible repintandose a 60 Hz es una forma
tonta de gastar bateria.
"""

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .. import style

_PASO_MS = 33               # ~30 Hz: mas no se nota, y esto compite con el visor
_GRADOS_POR_PASO = 12
_DIAMETRO = 14


class BusyIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self._angulo = 0
        self._tareas = {}                       # clave -> texto visible
        self.setVisible(False)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._girar)

    # ------------------------------------------------------------------ API
    def set_tarea(self, clave, texto=""):
        """Enciende (con texto) o apaga (sin texto) una tarea. Se pueden solapar varias."""
        if texto:
            self._tareas[clave] = texto
        else:
            self._tareas.pop(clave, None)
        activo = bool(self._tareas)
        self.setVisible(activo)
        if activo and not self._timer.isActive():
            self._timer.start(_PASO_MS)
        elif not activo and self._timer.isActive():
            self._timer.stop()
        self.updateGeometry()
        self.update()

    def _texto(self):
        # Si se solapan varias, manda la ultima que ha entrado: es la que el usuario acaba de pedir.
        return list(self._tareas.values())[-1] if self._tareas else ""

    # ------------------------------------------------------------------ pintado
    def _girar(self):
        self._angulo = (self._angulo + _GRADOS_POR_PASO) % 360
        self.update()

    def sizeHint(self):
        from PySide6.QtCore import QSize
        ancho = QFontMetrics(self.font()).horizontalAdvance(self._texto())
        return QSize(_DIAMETRO + 8 + ancho, max(_DIAMETRO, self.fontMetrics().height()))

    def paintEvent(self, _e):
        texto = self._texto()
        if not texto:
            return
        tema = style.tema_actual()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # El arco: 270 grados de circulo, girando. Los 90 que faltan son los que hacen que se vea
        # que gira; un circulo entero girando no se distingue de uno quieto.
        y = (self.height() - _DIAMETRO) / 2.0
        caja = QRectF(0, y, _DIAMETRO, _DIAMETRO).adjusted(1.5, 1.5, -1.5, -1.5)
        pen = QPen(QColor(tema.acento_claro))
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(caja, int(-self._angulo * 16), 270 * 16)

        p.setPen(QColor(tema.texto_tenue))
        p.drawText(QRectF(_DIAMETRO + 8, 0, self.width() - _DIAMETRO - 8, self.height()),
                   Qt.AlignLeft | Qt.AlignVCenter, texto)
        p.end()
