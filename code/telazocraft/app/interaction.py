# -*- coding: utf-8 -*-
"""Detalles comunes de interacción: posición inicial, cursores coherentes y esperas."""

import time

from PySide6.QtCore import Qt, QObject, QEvent, QRectF
from PySide6.QtGui import QCursor, QGuiApplication, QPainterPath, QRegion
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QAbstractSlider,
                               QComboBox, QHeaderView, QTabBar, QPushButton, QLineEdit,
                               QAbstractSpinBox, QMenu, QTableView, QWidget)

ALTO_CONTROL = 36

def preparar_control(widget):
    if isinstance(widget, (QAbstractButton, QComboBox, QAbstractSlider, QTabBar, QMenu)):
        widget.setCursor(Qt.PointingHandCursor)
    if isinstance(widget, QAbstractItemView) and not isinstance(widget, QHeaderView):
        widget.viewport().setCursor(Qt.PointingHandCursor)
    if isinstance(widget, (QPushButton, QComboBox, QLineEdit, QAbstractSpinBox)):
        if widget.objectName() == 'spinbtn' or isinstance(widget.parentWidget(), QAbstractSpinBox):
            return
        widget.setFixedHeight(ALTO_CONTROL)
        if isinstance(widget, QPushButton) and not widget.text():
            widget.setFixedWidth(ALTO_CONTROL)

class Interacciones(QObject):
    """Polish se entrega también a los controles creados después de abrir una ventana."""
    def eventFilter(self, objeto, evento):
        if evento.type() in (QEvent.Polish, QEvent.Show):
            preparar_control(objeto)
        if evento.type() in (QEvent.Show, QEvent.Resize) and isinstance(objeto, QWidget):
            if isinstance(objeto, (QTableView, QMenu)) or objeto.objectName() in ('QTipLabel', 'qt_tooltip_label') or objeto.metaObject().className() == 'QComboBoxPrivateContainer':
                path=QPainterPath();path.addRoundedRect(QRectF(objeto.rect()),10,10)
                objeto.setMask(QRegion(path.toFillPolygon().toPolygon()))
        return False

def instalar(app):
    if not hasattr(app, '_interacciones'):
        app._interacciones=Interacciones(app);app.installEventFilter(app._interacciones)

# Cuánto tiempo tiene sentido decir «buscando cámara» desde que abre el programa. El descubrimiento
# sondea cada 5 s y una iRayple tarda dos o tres vueltas en aparecer por unicast; 30 s cubren eso de
# sobra. Pasado ese rato sin encontrar nada, no hay nada que encontrar: el aviso se calla y el visor
# se queda limpio, porque un mensaje de error permanente hacía parecer roto un programa que solo
# estaba sin cámaras. Vive aquí para que la barra y el visor cuenten lo mismo.
BUSQUEDA_S = 30.0


def buscando_todavia(desde):
    """¿Sigue teniendo sentido decir «buscando»? `desde` es un `time.monotonic()`."""
    return (time.monotonic() - float(desde)) < BUSQUEDA_S


def suelo_ventana(ventana, ancho_pedido, alto_pedido, ancho_piso=0, alto_piso=0):
    """El mínimo que se le puede exigir a la ventana sin dejarla sin caber en la pantalla.

    El suelo pedido es alto a propósito: por debajo de él las pantallas densas se recortan en vez de
    reorganizarse. Pero exigirlo a secas dejaría la aplicación inarrancable en un monitor 1080p —la
    barra de tareas se come parte del alto— o en un equipo con pantalla menor. Se pide lo que se
    quiere y se acota a lo que hay, sin avisar a nadie: el usuario solo nota que no le deja achicar.

    El piso es el otro extremo: por debajo de él la barra superior no cabe y se recorta sola, así que
    no se cede aunque la pantalla sea todavía más pequeña. Ahí la ventana desbordará el monitor, que
    es exactamente lo que ya ocurría con el mínimo fijo anterior.
    """
    pantalla = ventana.screen() or QGuiApplication.primaryScreen()
    if pantalla is None:
        return ancho_pedido, alto_pedido
    disponible = pantalla.availableGeometry()
    return (max(ancho_piso, min(ancho_pedido, disponible.width())),
            max(alto_piso, min(alto_pedido, disponible.height())))


def centrar_ventana(ventana):
    """Centra una ventana en el monitor PRINCIPAL, esté donde esté el ratón.

    La ventana de inicio, la oferta de actualización y el programa se abren siempre ahí (petición
    del usuario, 30/09/2026). Antes se usaba el monitor del ratón y, con un monitor secundario, la
    ventana de inicio salía en él aunque el principal fuera el del portátil.
    """
    pantalla = QGuiApplication.primaryScreen()
    if pantalla is None:
        return
    ventana.adjustSize()
    marco = ventana.frameGeometry()
    marco.moveCenter(pantalla.availableGeometry().center())
    ventana.move(marco.topLeft())


def centrar_en_monitor(ventana):
    """Centra una ventana emergente en su monitor sin cambiarle el tamaño.

    Petición del usuario (06/10/2026): TODAS las ventanas emergentes en el centro del monitor,
    también cuando cambian de tamaño o de página. El monitor es el de la ventana de la que sale (el
    del programa); sin ella, el principal. Nunca más alta que el área útil.
    """
    padre = ventana.parentWidget()
    pantalla = (padre.window().screen() if padre is not None else None) or \
        QGuiApplication.primaryScreen()
    if pantalla is None:
        return
    util = pantalla.availableGeometry()
    if ventana.height() > util.height():
        ventana.resize(ventana.width(), max(ventana.minimumHeight(), util.height() - 40))
    marco = ventana.frameGeometry()
    marco.moveCenter(util.center())
    # Si el marco es más alto que el área útil, que se vea al menos la barra de título.
    ventana.move(marco.left(), max(util.top(), marco.top()))


def aplicar_cursores_interactivos(raiz):
    """Usa la mano en controles que ejecutan o seleccionan algo; conserva I-beam en textos."""
    preparar_control(raiz)
    for widget in raiz.findChildren(QWidget): preparar_control(widget)
    tipos = (QAbstractButton, QComboBox, QAbstractSlider, QTabBar, QMenu)
    for tipo in tipos:
        for widget in raiz.findChildren(tipo):
            widget.setCursor(Qt.PointingHandCursor)
            if isinstance(widget, QComboBox):
                widget.view().viewport().setCursor(Qt.PointingHandCursor)
    for vista in raiz.findChildren(QAbstractItemView):
        # OJO: QHeaderView TAMBIÉN es un QAbstractItemView. Si se le fuerza el cursor de mano en su
        # viewport, se pisa el cursor de redimensionar (SplitHCursor) que Qt pone automáticamente
        # sobre los separadores de columna. Las cabeceras se dejan con su cursor propio.
        if isinstance(vista, QHeaderView):
            continue
        vista.viewport().setCursor(Qt.PointingHandCursor)
