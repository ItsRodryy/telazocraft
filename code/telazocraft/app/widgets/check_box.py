# -*- coding: utf-8 -*-
"""Casilla común con tic vectorial, sin depender del indicador nativo de cada sistema."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox

from .. import icons, style

LADO = 18
MARGEN = 2
HUECO = 8


class CheckBox(QCheckBox):
    """Conserva el contrato de QCheckBox y pinta una casilla coherente en Windows y Ubuntu."""

    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        style.bus().cambiado.connect(self.update)

    def sizeHint(self):
        ancho = MARGEN * 2 + LADO
        if self.text():
            ancho += HUECO + self.fontMetrics().horizontalAdvance(self.text())
        return QSize(ancho, max(LADO + MARGEN * 2, self.fontMetrics().height() + 6))

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, _evento):
        tema = style.tema_actual()
        activo = self.isEnabled()
        rect = QRectF(MARGEN, (self.height() - LADO) / 2.0, LADO, LADO)
        borde = QColor(tema.acento if self.hasFocus() else tema.texto_tenue)
        fondo = QColor(tema.acento if self.isChecked() else tema.superficie_alta)
        if not activo:
            borde.setAlphaF(0.35)
            fondo.setAlphaF(0.35)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(borde, 1.2))
        painter.setBrush(fondo)
        painter.drawRoundedRect(rect.adjusted(0.6, 0.6, -0.6, -0.6),
                                style.R_INDICADOR, style.R_INDICADOR)
        if self.isChecked():
            color = QColor(tema.sobre_acento)
            if not activo:
                color.setAlphaF(0.5)
            icons.pintar_tic(painter, rect, color)
        if self.text():
            color = QColor(tema.texto_tenue if self.property("tenue") else tema.texto)
            if not activo:
                color.setAlphaF(0.4)
            painter.setPen(color)
            x = rect.right() + HUECO
            painter.drawText(QRectF(x, 0, max(0.0, self.width() - x), self.height()),
                             Qt.AlignLeft | Qt.AlignVCenter, self.text())
        painter.end()
