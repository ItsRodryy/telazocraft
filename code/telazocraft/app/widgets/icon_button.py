# -*- coding: utf-8 -*-
"""Boton con un glifo vectorial que se recolorea solo al cambiar de tema.

Existe por un motivo concreto: un QIcon es un mapa de bits YA PINTADO. Si se genera con el color del
tema oscuro y el usuario se pasa al claro, el icono se queda gris sobre blanco y nadie lo vuelve a
mirar. Aqui el glifo se redibuja al vuelo cuando `style.bus()` avisa del cambio.
"""

from PySide6.QtCore import QElapsedTimer, QSize, QTimer
from .. import icons, style
from .animated_button import AnimatedButton


class IconButton(AnimatedButton):
    """Botón con glifo. `color_tema` dice de qué color se pinta ese glifo.

    Por defecto va en el color de texto normal, que es lo que quiere un botón normal. Dentro de un
    botón de acción —fondo de acento— hay que pasarle `"SOBRE_ACENTO"`: si no, el glifo sale blanco
    sobre el color del botón y se ve como una pieza pegada de otro sitio. Se nombra el ROL y no el
    color, porque el color cambia con el tema y el glifo se repinta solo cuando eso pasa.
    """

    def __init__(self, glifo, tooltip="", size=16, objeto="iconbtn", texto="",
                 color_tema="TEXTO"):
        super().__init__(texto)
        self.setObjectName(objeto)
        self._glifo = glifo
        self._color_tema = str(color_tema or "TEXTO")
        self._size = size
        self._angulo = 0.0
        self._girando = False
        self._reloj_giro = QElapsedTimer()
        self._timer_giro = QTimer(self)
        self._timer_giro.setInterval(16)
        self._timer_giro.timeout.connect(self._avanzar_giro)
        if tooltip:
            self.setToolTip(tooltip)
        self.setIconSize(QSize(size, size))
        self._repintar()
        style.bus().cambiado.connect(self._repintar)

    def _repintar(self):
        # El color se lee del módulo en CADA repintado, no se guarda: `style` lo republica al
        # cambiar de tema y este método es justo lo que se llama entonces.
        color = getattr(style, self._color_tema, None)
        self.setIcon(icons.glifo(self._glifo, self._size, color=color, angulo=self._angulo))

    def set_glifo(self, glifo):
        self._glifo = str(glifo)
        self._repintar()

    def set_girando(self, girando):
        """Gira el glifo de forma continua; se usa para la recarga de camara."""
        girando = bool(girando)
        if girando == self._girando:
            return
        self._girando = girando
        if girando:
            self._reloj_giro.restart()
            self._timer_giro.start()
        else:
            self._timer_giro.stop()
            self._angulo = 0.0
            self._repintar()

    def esta_girando(self):
        return self._girando

    def _avanzar_giro(self):
        # Una vuelta cada 800 ms, en sentido HORARIO (ángulo positivo con Y hacia abajo), igual que
        # apuntan las dos flechas del glifo. El tiempo real evita saltos si Qt retrasa algún tick.
        self._angulo = (self._reloj_giro.elapsed() % 800) * 360.0 / 800.0
        self._repintar()
