# -*- coding: utf-8 -*-
"""Punto de estado compartido por toda la interfaz."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .. import style

OPERATIVA = "operativa"
SIMULACION = "simulacion"
TRABAJANDO = "trabajando"
FALLO = "fallo"
INACTIVA = "inactiva"
# Desconectada a mano con el botón de la barra, o sin su SDK (decisión del usuario, 07/10/2026).
DESCONECTADA = "desconectada"


def color_estado(clave, tema=None):
    """Devuelve el color canónico sin imponer vocabulario a los consumidores."""
    tema = tema or style.tema_actual()
    return {
        OPERATIVA: tema.ok_claro,
        SIMULACION: tema.aviso,
        TRABAJANDO: tema.aviso,
        FALLO: tema.peligro_claro,
        DESCONECTADA: tema.desconectada,
        INACTIVA: "#6d7178",
    }.get(clave, "#6d7178")


def pintar_punto(painter, rect, clave, radio=5):
    """Pinta un círculo centrado en ``rect`` con el estado indicado."""
    centro = rect.center()
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color_estado(clave)))
    painter.drawEllipse(QRectF(centro.x() - radio, centro.y() - radio,
                               radio * 2, radio * 2))
    painter.restore()


class PuntoEstado(QWidget):
    """Indicador de estado de tamaño fijo y actualizable en caliente."""

    def __init__(self, clave=INACTIVA, diametro=10, parent=None):
        super().__init__(parent)
        self.clave = clave
        self._diametro = int(diametro)
        # El suavizado necesita un píxel transparente alrededor. Si la elipse toca el límite del
        # widget, Qt recorta los píxeles parciales y el círculo parece mordido en una esquina.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(self._diametro + 2, self._diametro + 2))
        style.bus().cambiado.connect(self.update)

    def set_estado(self, clave):
        self.clave = clave
        self.update()

    def paintEvent(self, _evento):
        painter = QPainter(self)
        pintar_punto(painter, self.rect(), self.clave, self._diametro / 2.0)
