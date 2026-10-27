# -*- coding: utf-8 -*-
"""Ventanita de ayuda de un parámetro: pequeña, translúcida y fugaz.

Sustituye a la ayuda escrita debajo de cada parámetro, que convertía una lista de ajustes en una
pared de texto. Aparece a los `RETARDO_MS` de entrar el ratón en la fila, con un fundido corto, y se
va en cuanto sale. Enseña siempre el **nombre técnico original** junto a la ayuda y al rango: la
traducción al español orienta, pero lo que se toca en la cámara es el nombre técnico.

Hay **una sola instancia** para todo el programa (`instancia()`): con una por campo, cien campos
serían cien ventanas de nivel superior vivas.

Compatibilidad: `Qt.ToolTip | Qt.FramelessWindowHint` con `WA_TranslucentBackground` funciona en
Windows y en X11; en un Ubuntu sin compositor el fondo sale opaco, que es aceptable.
"""

import shiboken6
from PySide6.QtCore import QEvent, QObject, QPoint, QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .. import style
from ...common.i18n import tr

RETARDO_MS = 250
FUNDIDO_MS = 120
ANCHO_MAX = 300
# Separación respecto al puntero, para que la ventanita no tape lo que se está señalando.
_DESVIO = QPoint(14, 18)
_OPACIDAD_FONDO = 232


class AyudaFlotante(QWidget):
    def __init__(self):
        super().__init__(None, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._objetivo = None
        caja = QVBoxLayout(self)
        caja.setContentsMargins(10, 7, 10, 8)
        caja.setSpacing(2)
        self.tecnico = QLabel("")
        self.texto = QLabel("")
        self.texto.setWordWrap(True)
        self.rango = QLabel("")
        for etiqueta in (self.tecnico, self.texto, self.rango):
            etiqueta.setMaximumWidth(ANCHO_MAX)
            etiqueta.setTextInteractionFlags(Qt.NoTextInteraction)
            caja.addWidget(etiqueta)
        self._espera = QTimer(self)
        self._espera.setSingleShot(True)
        self._espera.timeout.connect(self._aparecer)
        self._fundido = QPropertyAnimation(self, b"windowOpacity", self)
        self._fundido.setDuration(FUNDIDO_MS)
        self._estilo()
        style.bus().cambiado.connect(self._estilo)

    def _estilo(self):
        tema = style.tema_actual()
        pequeña = "font-size: 11px; background: transparent;"
        self.tecnico.setStyleSheet("%s color: %s; font-family: Consolas, 'DejaVu Sans Mono', "
                                   "monospace;" % (pequeña, tema.texto_tenue))
        self.texto.setStyleSheet("%s color: %s;" % (pequeña, tema.texto))
        self.rango.setStyleSheet("%s color: %s;" % (pequeña, tema.texto_tenue))
        self.update()

    def paintEvent(self, _evento):
        tema = style.tema_actual()
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing, True)
        fondo = QColor(tema.superficie_alta)
        fondo.setAlpha(_OPACIDAD_FONDO)
        borde = QColor(tema.borde)
        camino = QPainterPath()
        camino.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5),
                              style.R_CONTROL, style.R_CONTROL)
        pintor.fillPath(camino, fondo)
        pintor.setPen(QPen(borde, 1))
        pintor.drawPath(camino)

    # ------------------------------------------------------------------ ciclo
    def programar(self, objetivo):
        """El ratón entró en `objetivo`: se enseña su ayuda si sigue dentro a los `RETARDO_MS`."""
        if objetivo is not self._objetivo:
            self.ocultar()
        self._objetivo = objetivo
        if not self.isVisible():
            self._espera.start(RETARDO_MS)

    def ocultar(self, objetivo=None):
        """Se va al momento. Con `objetivo`, solo si la ayuda visible o pendiente es la suya."""
        if objetivo is not None and objetivo is not self._objetivo:
            return
        self._espera.stop()
        self._fundido.stop()
        self._objetivo = None
        self.hide()

    def objetivo(self):
        return self._objetivo

    def _aparecer(self):
        objetivo = self._objetivo
        if objetivo is None or not shiboken6.isValid(objetivo) or not objetivo.isVisible():
            self.ocultar()
            return
        proveedor = getattr(objetivo, "_ayuda_proveedor", None)
        datos = proveedor() if callable(proveedor) else None
        if not datos:
            return
        tecnico, ayuda, rango = (tuple(datos) + ("", "", ""))[:3]
        self.tecnico.setText(str(tecnico or ""))
        self.tecnico.setVisible(bool(tecnico))
        self.texto.setText(str(ayuda or ""))
        self.texto.setVisible(bool(ayuda))
        self.rango.setText(tr("Rango: %s") % rango if rango else "")
        self.rango.setVisible(bool(rango))
        self.adjustSize()
        self.move(self._posicion(QCursor.pos() + _DESVIO))
        if style.animaciones_activas():
            self.setWindowOpacity(0.0)
            self.show()
            self._fundido.setStartValue(0.0)
            self._fundido.setEndValue(1.0)
            self._fundido.start()
        else:
            self.setWindowOpacity(1.0)
            self.show()

    def _posicion(self, punto):
        """Dentro de la pantalla del puntero: cerca del borde se da la vuelta en vez de salirse."""
        pantalla = QGuiApplication.screenAt(punto) or QGuiApplication.primaryScreen()
        if pantalla is None:
            return punto
        zona = pantalla.availableGeometry()
        x, y = punto.x(), punto.y()
        if x + self.width() > zona.right():
            x = max(zona.left(), punto.x() - 2 * _DESVIO.x() - self.width())
        if y + self.height() > zona.bottom():
            y = max(zona.top(), punto.y() - 2 * _DESVIO.y() - self.height())
        return QPoint(x, y)


class _Vigilante(QObject):
    """Filtro de eventos compartido: entrar programa la ayuda; salir, pulsar u ocultar la quita."""

    _SALIDAS = (QEvent.Leave, QEvent.Hide, QEvent.MouseButtonPress, QEvent.Wheel,
                QEvent.WindowDeactivate)

    def eventFilter(self, objeto, evento):
        tipo = evento.type()
        if tipo == QEvent.Enter:
            instancia().programar(objeto)
        elif tipo in self._SALIDAS:
            instancia().ocultar(objeto)
        return False


_instancia = None
_vigilante = None


def instancia():
    global _instancia
    if _instancia is None or not shiboken6.isValid(_instancia):
        _instancia = AyudaFlotante()
    return _instancia


def instalar(widget, proveedor):
    """Da a `widget` una ayuda flotante. `proveedor()` devuelve `(técnico, ayuda, rango)`.

    Se pregunta al proveedor al aparecer, no al instalar: así el rango es el que la cámara publica
    en ese momento y no el de cuando se montó el campo.
    """
    global _vigilante
    if _vigilante is None or not shiboken6.isValid(_vigilante):
        _vigilante = _Vigilante()
    widget._ayuda_proveedor = proveedor
    widget.installEventFilter(_vigilante)
    return widget
