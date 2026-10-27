# -*- coding: utf-8 -*-
"""Caja numerica con botones de incremento propios: redondeados, compactos y minimalistas.

Las flechas que trae Qt de serie no se pueden redondear: `QSpinBox::up-button` acepta un
`border-radius` pero la flecha de dentro es una imagen del estilo nativo, y para cambiarla hay que
darle un `image: url(...)`, o sea un PNG por tema, por tamano y por estado. Eso es justo lo que este
proyecto no quiere: ficheros de imagen que mantener y que se ven mal al escalar.

Asi que los botones son nuestros: `setButtonSymbols(NoButtons)` apaga los de Qt y al lado se ponen
dos botones con la punta de flecha dibujada con QPainterPath (ver `icons.py`). Vectorial, nitido a
cualquier escalado, y se recolorea solo al cambiar de tema.

La FUNCIONALIDAD no cambia: mismo rango, mismo paso, mismas senales. Solo cambia el aspecto.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QHBoxLayout, QSizePolicy, QSlider,
                               QVBoxLayout, QWidget)

from .. import icons, style
from .icon_button import IconButton
from ...common.i18n import tr

ALTO_BOTON = 18
ANCHO_BOTON = 18
SEPARACION_BOTONES = 6      # aire entre la caja y las flechas; con 4 se veian pegadas
ANCHO_MINIMO_CAJA = 64      # por debajo de esto la cifra y su sufijo dejan de caber
ANCHO_CAJA_COMPACTA = 88    # para valores cortos: «30 ×» y parecidos


class _SpinSinRueda(QDoubleSpinBox):
    """La rueda desplaza la página; nunca modifica un número por accidente."""

    def wheelEvent(self, evento):
        evento.ignore()

    def _ajustar_editor(self):
        # Algunos estilos de Qt sin pantalla devuelven un editor de un solo píxel.
        if self.lineEdit().width() < ANCHO_MINIMO_CAJA // 2 and self.width() >= ANCHO_MINIMO_CAJA:
            self.lineEdit().setGeometry(self.contentsRect().adjusted(10, 0, -10, 0))

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._ajustar_editor()

    def showEvent(self, evento):
        super().showEvent(evento)
        self._ajustar_editor()


class SliderSinRueda(QSlider):
    """Slider arrastrable y accesible por teclado, pero inmune a la rueda."""

    def wheelEvent(self, evento):
        evento.ignore()


class ComboSinRueda(QComboBox):
    """Desplegable minimalista: su punta de flecha es la del programa, no la de Windows.

    La flecha nativa vive dentro de `::drop-down` y solo se cambia con `image: url(...)`, o sea un
    PNG por tema, tamano y estado —justo lo que este modulo evita—. Asi que el QSS la deja sin ancho
    y aqui se traza el mismo chevron que usan los botones de incremento. Ademas nunca cambia de valor
    con la rueda: eso modificaba parametros sin querer al desplazar un panel.
    """

    def wheelEvent(self, evento):
        evento.ignore()

    def paintEvent(self, evento):
        super().paintEvent(evento)
        caja = self.rect()
        lado = min(style.LADO_CHEVRON, caja.height())
        x = caja.right() - style.ANCHO_CHEVRON + (style.ANCHO_CHEVRON - lado) / 2.0
        y = caja.center().y() - lado / 2.0 + 1
        color = style.TEXTO if self.isEnabled() else style.TEXTO_TENUE
        painter = QPainter(self)
        icons.dibujar_glifo(painter, "abajo", QRectF(x, y, lado, lado), color=color)
        painter.end()


class SpinBox(QWidget):
    """Un QDoubleSpinBox con sus dos botones al lado. Delega todo lo demas en `self.spin`."""

    def __init__(self, decimales=0):
        super().__init__()
        self.spin = _SpinSinRueda()
        self.spin.setDecimals(decimales)
        self.spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.spin.setKeyboardTracking(False)
        self.spin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        botones = QVBoxLayout()
        botones.setContentsMargins(0, 0, 0, 0)
        botones.setSpacing(2)
        self.b_mas = IconButton("arriba", tr("Aumentar"), size=8, objeto="spinbtn")
        self.b_menos = IconButton("abajo", tr("Disminuir"), size=8, objeto="spinbtn")
        for b in (self.b_mas, self.b_menos):
            b.setFixedSize(ANCHO_BOTON, ALTO_BOTON)
            b.setFocusPolicy(Qt.NoFocus)        # tabular no debe caer en las flechas
            b.setAutoRepeat(True)               # mantener pulsado incrementa, como el de Qt
            botones.addWidget(b)
        self.b_mas.clicked.connect(self.spin.stepUp)
        self.b_menos.clicked.connect(self.spin.stepDown)

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(SEPARACION_BOTONES)
        h.addWidget(self.spin, 1)
        h.addLayout(botones)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # La caja del numero cede ancho, pero solo hasta aqui. Sin este suelo, un panel estrecho la
        # comprimia por debajo de su minimo y las flechas acababan dibujadas ENCIMA de la cifra.
        self.spin.setMinimumWidth(ANCHO_MINIMO_CAJA)
        self.setMinimumWidth(ANCHO_MINIMO_CAJA + SEPARACION_BOTONES + ANCHO_BOTON)

    def compactar(self, ancho=ANCHO_CAJA_COMPACTA):
        """Deja la caja del numero en lo justo para su cifra, en vez de estirarse por la fila.

        Para valores cortos —un zoom maximo, un numero de divisiones— una caja a todo lo ancho no
        aporta nada y ademas aprieta a las flechas. Con esto el numero ocupa lo suyo y el resto de
        la fila queda libre.
        """
        ancho = max(int(ancho), ANCHO_MINIMO_CAJA)
        # El estilo global impone `min-width: 120px` a toda caja numerica, y ese minimo gana sobre
        # el layout: sin levantarlo, la caja no encoge y las flechas terminan encima de la cifra.
        # La regla `[compacto="true"]` de `style.py` lo anula solo para estas.
        self.spin.setProperty("compacto", "true")
        self.spin.style().unpolish(self.spin)
        self.spin.style().polish(self.spin)
        self.spin.setFixedWidth(ancho)
        # Tambien el conjunto: si solo se fija la caja, un panel estrecho sigue comprimiendo el
        # widget entero y las flechas vuelven a montarse encima. Antes de que eso pase, que el
        # panel muestre su barra de desplazamiento.
        self.setFixedWidth(ancho + SEPARACION_BOTONES + ANCHO_BOTON)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    # --- lo que usa el resto del codigo, para que sustituir un QDoubleSpinBox sea un cambio de tipo
    def value(self):
        return self.spin.value()

    def setValue(self, v):
        self.spin.setValue(v)

    def setRange(self, minimo, maximo):
        self.spin.setRange(minimo, maximo)

    def minimum(self):
        return self.spin.minimum()

    def maximum(self):
        return self.spin.maximum()

    def setMinimum(self, minimo):
        self.spin.setMinimum(minimo)

    def setMaximum(self, maximo):
        self.spin.setMaximum(maximo)

    def setDecimals(self, n):
        self.spin.setDecimals(n)

    def setSingleStep(self, paso):
        self.spin.setSingleStep(paso)

    def setSuffix(self, texto):
        self.spin.setSuffix(texto)

    def setSpecialValueText(self, texto):
        self.spin.setSpecialValueText(texto)

    def setKeyboardTracking(self, activo):
        self.spin.setKeyboardTracking(activo)

    def tiene_foco(self):
        return self.spin.hasFocus()

    def setEnabled(self, activo):
        super().setEnabled(activo)
        self.spin.setEnabled(activo)
        self.b_mas.setEnabled(activo)
        self.b_menos.setEnabled(activo)

    @property
    def editingFinished(self):
        return self.spin.editingFinished

    @property
    def valueChanged(self):
        return self.spin.valueChanged
