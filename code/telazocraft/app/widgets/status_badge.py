# -*- coding: utf-8 -*-
"""Indicador de estado con un punto (o glifo) de color y texto.

Por defecto pinta un punto. Si se le pasa `icono` (nombre de un glifo de `icons`), pinta ese glifo
recoloreado con el estado: es lo que usa el servidor (glifo `servidor`) en vez del punto suelto.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

from .. import style
from .. import icons
from .estado_punto import (FALLO, INACTIVA, OPERATIVA, TRABAJANDO,
                           color_estado, pintar_punto)


def _color(clave):
    canonica = {
        "parado": INACTIVA, "arrancando": TRABAJANDO, "escuchando": OPERATIVA,
        "error": FALLO, "conectada": OPERATIVA, "desconectada": INACTIVA,
    }.get(clave, INACTIVA)
    return color_estado(canonica)


class _Indicador(QWidget):
    """Punto de color, o glifo recoloreado si se indica `icono`."""

    def __init__(self, icono=None):
        super().__init__()
        self.clave = "parado"
        self.icono = icono
        self.setFixedSize(QSize(16, 16) if icono else QSize(10, 10))
        style.bus().cambiado.connect(self.update)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        color = _color(self.clave)
        if self.icono:
            pm = icons.glifo_pixmap(self.icono, min(self.width(), self.height()), color=color)
            p.drawPixmap(0, 0, pm)
        else:
            canonica = {
                "parado": INACTIVA, "arrancando": TRABAJANDO, "escuchando": OPERATIVA,
                "error": FALLO, "conectada": OPERATIVA, "desconectada": INACTIVA,
            }.get(self.clave, INACTIVA)
            pintar_punto(p, self.rect(), canonica, 5)


class StatusBadge(QWidget):
    def __init__(self, texto="", icono=None):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(7)
        self._punto = _Indicador(icono)
        self._label = QLabel(texto)
        h.addWidget(self._punto)
        h.addWidget(self._label)
        h.addStretch(1)

    def set_estado(self, clave, texto=None):
        self._punto.clave = clave
        self._punto.update()
        if texto is not None:
            self._label.setText(texto)
