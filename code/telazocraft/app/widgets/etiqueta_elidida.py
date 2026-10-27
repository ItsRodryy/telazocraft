# -*- coding: utf-8 -*-
"""Etiqueta que se recorta con puntos suspensivos en vez de estirar la ventana.

Un `QLabel` normal reclama el ancho de todo su texto. Si además vive en la barra de estado con
`addPermanentWidget`, ese ancho entra en el mínimo de la ventana entera: al usuario le parece que
el programa «no le deja achicar», y el culpable es un texto que ni siquiera está mirando.

El patrón —elidir, dejar el texto entero en la ayuda emergente y rehacerlo al cambiar de tamaño—
ya estaba resuelto en `camera_selector.py` y en `stats_panel.py`, cada uno por su cuenta. Esto es
ese mismo patrón, una sola vez y para quien lo necesite.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QLabel, QSizePolicy


class EtiquetaElidida(QLabel):
    """Muestra lo que quepa y guarda el texto completo en el tooltip."""

    def __init__(self, texto="", modo=Qt.ElideRight, ancho_minimo=60, parent=None):
        super().__init__(parent)
        self._completo = ""
        self._modo = modo
        self._ancho_minimo = int(ancho_minimo)
        # `Ignored` en horizontal es lo que impide que el texto empuje el mínimo de la ventana.
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self.setText(texto)

    def setText(self, texto):
        self._completo = str(texto or "")
        self.setToolTip(self._completo)
        self._repintar()

    def text(self):
        """El texto REAL, no el recortado: quien pregunte quiere el contenido, no lo que se ve."""
        return self._completo

    def _repintar(self):
        ancho = max(self._ancho_minimo, self.width())
        super().setText(QFontMetrics(self.font()).elidedText(self._completo, self._modo, ancho))

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._repintar()
