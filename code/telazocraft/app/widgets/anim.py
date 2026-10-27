# -*- coding: utf-8 -*-
"""Animaciones baratas.

Qt no soporta `transition` en QSS, asi que el fundido se hace interpolando una
propiedad. Reglas:

  - Nunca con QGraphicsOpacityEffect ni QGraphicsDropShadowEffect: fuerzan un
    render offscreen del subarbol entero. Con el visor de camara dentro, eso
    cuesta mas que la propia animacion.
  - Nunca mientras el autotune barre o el servidor recibe: `style.animaciones_activas()`.
    Una animacion a 60 Hz peleando con el hilo de camara es exactamente lo que se
    percibe como "la app va lenta".
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation

from .. import style


def fundido_opacidad(widget, desde, hasta, ms=None, al_terminar=None):
    """Anima windowOpacity de una ventana (no de un widget hijo: eso necesitaria efectos)."""
    if not style.animaciones_activas():
        widget.setWindowOpacity(hasta)
        if al_terminar:
            al_terminar()
        return None
    anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(ms or style.DURACION_FUNDIDO_MS)
    anim.setStartValue(desde)
    anim.setEndValue(hasta)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    if al_terminar:
        anim.finished.connect(al_terminar)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim
