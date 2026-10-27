# -*- coding: utf-8 -*-
"""Envolver un panel en un área desplazable, siempre igual.

Sin esto, un panel más alto que la ventana no se recorta limpiamente: Qt lo comprime **por debajo de
su tamaño natural**, y lo primero que se pierde son las descripciones con varias líneas, que se
quedan cortadas por abajo sin puntos suspensivos ni aviso. Con scroll, lo que no cabe se alcanza
bajando, que es lo que espera cualquiera.

`setWidgetResizable(True)` es la parte que importa: el contenido sigue estirándose a lo ancho para
llenar el hueco y solo aparece la barra cuando el mínimo real no cabe.
"""

from PySide6.QtWidgets import QFrame, QScrollArea

from .. import style


def desplazable(widget, paso=24, tarjeta=False):
    """`tarjeta=True` mete el contenido en un panel redondeado: para páginas sin paneles propios."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setWidget(style.tarjeta(widget) if tarjeta else widget)
    area.verticalScrollBar().setSingleStep(paso)
    return area
