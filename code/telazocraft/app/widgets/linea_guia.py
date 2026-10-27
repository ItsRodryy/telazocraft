# -*- coding: utf-8 -*-
"""La línea fina que lleva la vista del rótulo hasta su valor.

En una lista de ajustes el rótulo va a la izquierda y el control a la derecha, con un hueco en medio
que crece con el ancho de la ventana. A 1920 px ese hueco son quince centímetros de nada, y la vista
se pierde por el camino: se acaba leyendo «Formato» y buscando a qué valor corresponde. Es el mismo
recurso de toda la vida de un índice o de una carta.

Es una línea **continua** de 1 px, no de puntos (decisión del usuario, 17/09/2026): los puntos
vibraban al desplazar la lista y ensuciaban más de lo que guiaban. Se dibuja, no se escribe con
caracteres: un `QWidget` de una línea que se pinta al ancho que le toque, en el color tenue del
tema, y que se recolorea solo cuando el tema cambia.
"""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget

from .. import style

# Ancho mínimo por debajo del cual la línea no se dibuja: un trazo de pocos píxeles no guía a nadie
# y lo único que hace es ensuciar una fila estrecha.
_MINIMO_UTIL = 24


class LineaGuia(QWidget):
    """La línea continua. Ocupa lo que sobre entre el rótulo y el control."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(12)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        style.bus().cambiado.connect(self.update)

    def paintEvent(self, _evento):
        if self.width() < _MINIMO_UTIL:
            return
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing, False)
        color = QColor(style.TEXTO_TENUE)
        # Tenue de verdad: la línea acompaña la lectura, no compite con el dato. Continua pesa más a
        # la vista que los puntos, así que va más transparente que ellos.
        color.setAlpha(70)
        pintor.setPen(QPen(color, 1, Qt.SolidLine))
        y = self.height() - 4        # apoyada en la línea base del texto, no centrada
        pintor.drawLine(QPointF(2, y), QPointF(self.width() - 2, y))


# Cómo se reparte el ancho sobrante entre la descripción y la línea guía. La descripción manda:
# es lo que hay que leer, y la línea solo acompaña. Con la proporción al revés —que es como estaba en
# Guardado— la línea se quedaba el hueco y la ayuda se estrujaba en una columna estrecha.
_PESO_TEXTOS = 3
_PESO_LINEA = 1


class FilaGuiada(QWidget):
    """Una fila «rótulo + descripción ───── control». La fila de ajustes de todo el programa.

    Va sobre un `QGridLayout` **a propósito**, y esto no es un detalle de estilo: Qt no propaga
    `heightForWidth` a través de un layout horizontal. Con la descripción metida en un `QVBoxLayout`
    dentro de un `QHBoxLayout` —que es como estaban Guardado y los parámetros de cámara— la fila
    calculaba su alto como si el texto ocupase una línea, y en una pantalla de portátil, donde la
    misma frase envuelve en tres o cuatro, **se veía cortada por abajo**. En una rejilla el alto sale
    del texto ya envuelto al ancho real, así que la fila crece lo que haga falta y encaja igual en un
    monitor grande que en uno de 15,6". No hay ni un ancho ni un alto fijado a mano.

    Antes esta clase existía y no la usaba nadie: cada panel repetía el patrón por su cuenta, y el
    arreglo había que hacerlo tres veces. Ahora es la única.
    """

    def __init__(self, rotulo, control, ayuda="", extra=None, margenes=(10, 7, 10, 7), parent=None):
        super().__init__(parent)
        rejilla = QGridLayout(self)
        rejilla.setContentsMargins(*margenes)
        rejilla.setHorizontalSpacing(8)
        rejilla.setVerticalSpacing(2)

        if isinstance(rotulo, str):
            etiqueta = QLabel(rotulo)
            etiqueta.setObjectName("featuretitle")
            rotulo = etiqueta
        rotulo.setWordWrap(True)
        rejilla.addWidget(rotulo, 0, 0)

        if isinstance(ayuda, str):
            self.ayuda = QLabel(ayuda) if ayuda else None
            if self.ayuda is not None:
                self.ayuda.setObjectName("tenue")
        else:
            self.ayuda = ayuda
        if self.ayuda is not None:
            # Directamente en la rejilla, sin widget intermedio: un `QWidget` contenedor volvería a
            # tragarse el `heightForWidth` y estaríamos donde estábamos.
            self.ayuda.setWordWrap(True)
            rejilla.addWidget(self.ayuda, 1, 0)

        filas = 2 if self.ayuda is not None else 1
        self.linea = LineaGuia()
        rejilla.addWidget(self.linea, 0, 1, filas, 1, Qt.AlignVCenter)
        columna = 2
        if extra is not None:
            rejilla.addWidget(extra, 0, columna, filas, 1, Qt.AlignVCenter)
            columna += 1
        rejilla.addWidget(control, 0, columna, filas, 1, Qt.AlignVCenter)

        rejilla.setColumnStretch(0, _PESO_TEXTOS)
        rejilla.setColumnStretch(1, _PESO_LINEA)
        self.rotulo = rotulo
        self.control = control
