# -*- coding: utf-8 -*-
"""Esquinas redondeadas por recorte. **Solo para el visor 3D de Volumen.**

AVISO antes de volver a usar esto en cualquier otro sitio: una mascara es de 1 bit y no tiene
suavizado, asi que la curva sale escalonada —la region de una tabla se descomponia en 18 rectangulos
y en pantalla se veian como rayas en la esquina—. Ademas hay que reaplicarla en cada resize, y si
alguien se olvida el redondeo aparece y desaparece segun el momento.

En Lectoras ya no se usa: el redondeo lo da el QSS de `style.py`, que si tiene antialias. Aqui se
conserva porque el visor de nube pinta con OpenGL sobre su propia superficie y el QSS no lo alcanza.

Original:

QSS redondea el BORDE que pinta, pero el fondo del widget y el de sus hijos se siguen dibujando
rectangulares: en la curva asoma lo que haya detras, y por eso las esquinas «no salen bonitas» en
las tablas, las areas desplazables y el log. Se nota mas cuanto mayor es el contraste entre el
panel y su fondo.

La unica forma de recortarlo de verdad es una mascara sobre la region visible, que si afecta a los
hijos —viewport, cabecera y barras de desplazamiento incluidos—. Esto ya se hacia en `tabla_datos`;
aqui esta generalizado para cualquier widget, y con la reaplicacion automatica al cambiar de tamano,
que es lo que faltaba para poder usarlo en paneles que crecen con la ventana.

**Coste**: recalcular la region en cada repintado seria caro. Se recalcula SOLO al redimensionar,
que es cuando cambia. No usarlo en el visor de imagen ni en la rejilla de camaras: ahi el tamano
cambia con el raton y el ahorro no compensa.
"""

from PySide6.QtCore import QEvent, QObject, QRect
from PySide6.QtGui import QRegion

from .. import style


def region_redondeada(ancho, alto, radio):
    """Region rectangular con las cuatro esquinas comidas. None si no cabe redondear."""
    radio = min(int(radio), ancho // 2, alto // 2)
    if radio <= 0 or ancho <= 0 or alto <= 0:
        return None
    diametro = 2 * radio
    region = QRegion(QRect(radio, 0, ancho - diametro, alto))
    region |= QRegion(QRect(0, radio, ancho, alto - diametro))
    for x, y in ((0, 0), (ancho - diametro, 0), (0, alto - diametro),
                 (ancho - diametro, alto - diametro)):
        region |= QRegion(QRect(x, y, diametro, diametro), QRegion.Ellipse)
    return region


def aplicar_mascara_redondeada(widget, radio=style.R_PANEL):
    """Recorta el widget AHORA. Para que se mantenga al crecer, usar `instalar_mascara`."""
    region = region_redondeada(widget.width(), widget.height(), radio)
    if region is None:
        widget.clearMask()
    else:
        widget.setMask(region)


class _Redondeador(QObject):
    """Reaplica la mascara cada vez que el widget cambia de tamano."""

    def __init__(self, widget, radio):
        super().__init__(widget)
        self._radio = radio
        widget.installEventFilter(self)
        aplicar_mascara_redondeada(widget, radio)

    def eventFilter(self, obj, evento):
        if evento.type() == QEvent.Resize:
            aplicar_mascara_redondeada(obj, self._radio)
        return False


def instalar_mascara(widget, radio=style.R_PANEL):
    """Redondea el widget y lo mantiene redondeado mientras viva. Devuelve el widget."""
    _Redondeador(widget, radio)
    return widget
