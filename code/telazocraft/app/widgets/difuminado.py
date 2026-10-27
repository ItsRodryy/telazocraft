# -*- coding: utf-8 -*-
"""Degradado sobre el borde inferior de una zona con scroll.

Cuando una lista desplazable termina encima de otro bloque, la última tarjeta visible queda cortada
en seco por la mitad y parece un fallo de dibujo. Este widget pinta, pegado al borde de abajo del
viewport, un degradado del fondo de la página hacia arriba: el contenido se difumina en vez de
cortarse. Solo aparece mientras queda contenido por debajo; al llegar al final desaparece para no
tapar la última tarjeta.

Es un hijo del `QScrollArea`, no del viewport: así no se desplaza con el contenido. Deja pasar el
ratón, de modo que lo que haya debajo se sigue pudiendo pulsar.
"""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget

from .. import style

ALTO_DIFUMINADO = 36


class DifuminadoInferior(QWidget):
    """Degradado fijo en la parte baja del viewport de `area`."""

    def __init__(self, area, alto=ALTO_DIFUMINADO):
        super().__init__(area)
        self._area = area
        self._alto = int(alto)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        barra = area.verticalScrollBar()
        barra.rangeChanged.connect(lambda _a, _b: self._actualizar())
        barra.valueChanged.connect(lambda _v: self._actualizar())
        self._filtro = _AlCambiarTamano(self._colocar)
        area.installEventFilter(self._filtro)
        style.bus().cambiado.connect(self.update)
        self._colocar()
        self._actualizar()

    def _colocar(self):
        """Ocupa el ancho del viewport, no el del área: la barra de scroll queda fuera."""
        visor = self._area.viewport().geometry()
        self.setGeometry(visor.left(), visor.bottom() - self._alto + 1, visor.width(), self._alto)
        self.raise_()

    def _actualizar(self):
        barra = self._area.verticalScrollBar()
        self.setVisible(barra.maximum() > 0 and barra.value() < barra.maximum())

    def paintEvent(self, _evento):
        # El color se lee en cada pintado: si el tema cambia, el degradado lo sigue sin rehacerlo.
        fondo = QColor(style.FONDO)
        transparente = QColor(fondo)
        transparente.setAlpha(0)
        degradado = QLinearGradient(0, 0, 0, self.height())
        degradado.setColorAt(0.0, transparente)
        degradado.setColorAt(1.0, fondo)
        painter = QPainter(self)
        painter.fillRect(self.rect(), degradado)
        painter.end()


class _AlCambiarTamano(QObject):
    """Recoloca el degradado cada vez que el área cambia de tamaño o se muestra."""

    def __init__(self, llamada):
        super().__init__()
        self._llamada = llamada

    def eventFilter(self, _objeto, evento):
        if evento.type() in (QEvent.Resize, QEvent.Show, QEvent.LayoutRequest):
            self._llamada()
        return False
