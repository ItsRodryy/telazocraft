# -*- coding: utf-8 -*-
"""Indicador de «estoy comprobando»: un arco que gira con el acento del tema.

Para esperas cortas sin porcentaje (preguntar a GitHub si hay versión nueva). Solo gira mientras está
a la vista y con las animaciones activas; sin ellas se queda quieto, pero se sigue viendo.
"""

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .. import style

PASO_MS = 16          # ~60 fotogramas por segundo
GRADOS_POR_PASO = 6   # una vuelta por segundo
ARCO_GRADOS = 100


class IndicadorCarga(QWidget):
    def __init__(self, lado=16, parent=None):
        super().__init__(parent)
        self._lado = lado
        self._angulo = 0
        self.setFixedSize(QSize(lado, lado))
        self._reloj = QTimer(self)
        self._reloj.setInterval(PASO_MS)
        self._reloj.timeout.connect(self._avanzar)
        style.bus().cambiado.connect(self.update)

    def iniciar(self):
        self.setVisible(True)
        self._actualizar_reloj()

    def parar(self):
        self._reloj.stop()
        self.setVisible(False)

    def girando(self):
        return self._reloj.isActive()

    def _actualizar_reloj(self):
        if self.isVisible() and style.animaciones_activas():
            self._reloj.start()
        else:
            self._reloj.stop()

    def showEvent(self, evento):
        super().showEvent(evento)
        self._actualizar_reloj()

    def hideEvent(self, evento):
        super().hideEvent(evento)
        self._reloj.stop()

    def _avanzar(self):
        self._angulo = (self._angulo + GRADOS_POR_PASO) % 360
        self.update()

    def paintEvent(self, _evento):
        tema = style.tema_actual()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        grosor = max(2.0, self._lado / 8.0)
        caja = QRectF(grosor / 2, grosor / 2, self._lado - grosor, self._lado - grosor)
        pista = QColor(tema.borde)
        p.setPen(QPen(pista, grosor, Qt.SolidLine, Qt.RoundCap))
        p.drawEllipse(caja)
        p.setPen(QPen(QColor(tema.acento), grosor, Qt.SolidLine, Qt.RoundCap))
        # Qt mide en dieciseisavos de grado y en sentido antihorario: se gira en sentido horario.
        p.drawArc(caja, int(-self._angulo * 16), int(ARCO_GRADOS * 16))
