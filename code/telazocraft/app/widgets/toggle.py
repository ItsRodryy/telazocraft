# -*- coding: utf-8 -*-
"""Interruptor animado estilo Windows 11 (Fluent).

Por que un widget y no una regla de QSS: **Qt no soporta `transition` en QSS**. Con hoja de estilos
se puede colorear el indicador de un QCheckBox, pero no MOVER nada. Lo que habia antes
(`QCheckBox#toggle::indicator`) era solo una pastilla que se rellenaba de color: sin pulgar, sin
movimiento, muerta. Un interruptor de verdad tiene que pintarse a mano.

Hereda de QCheckBox a proposito: asi `toggled`, `setChecked`, `blockSignals`, la barra espaciadora y
el foco siguen funcionando igual y los llamadores no cambian. Lo unico que se sustituye es el
pintado (no se llama a `super().paintEvent`, asi que el indicador del QSS deja de existir).

Reglas que respeta, heredadas de `anim.py`:

  - Nunca QGraphicsOpacityEffect ni QGraphicsDropShadowEffect: fuerzan un render offscreen del
    subarbol entero, y dentro esta el visor de camara.
  - Nunca anima si `style.animaciones_activas()` es False. La UI las apaga durante el barrido del
    autotune: una animacion a 60 Hz peleando con el hilo de camara es exactamente lo que se percibe
    como "la aplicacion va lenta".
"""

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox

from .. import style

# Geometria de la pista y del pulgar (pixeles).
PISTA_W = 40
PISTA_H = 20
BORDE_PISTA = 1.4
MARGEN_X = 1                 # respiro para el suavizado del borde de la pista

# El centro del pulgar va en el centro del extremo redondeado de la pista (a PISTA_H/2 del borde).
# Asi el pulgar queda dentro pase lo que pase mientras su radio no supere PISTA_H/2 - BORDE_PISTA.
RADIO_REPOSO = 6.0
RADIO_HOVER = 7.0            # 7 < 20/2 - 1.4 = 8.6, luego al crecer en hover sigue sin salirse
ESTIRA_PULSADO = 4.0         # cuanto se alarga el pulgar al mantener pulsado (ovalo)

HUECO_TEXTO = 9              # entre la pista y la etiqueta
DURACION_MS = 140            # deslizamiento del pulgar + fundido de la pista


def _mezcla(c1, c2, t):
    """Interpola dos colores. `t`=0 -> c1, `t`=1 -> c2."""
    t = max(0.0, min(1.0, t))
    return QColor(
        round(c1.red() + (c2.red() - c1.red()) * t),
        round(c1.green() + (c2.green() - c1.green()) * t),
        round(c1.blue() + (c2.blue() - c1.blue()) * t),
        round(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
    )


def _atenua(color, alpha):
    c = QColor(color)
    c.setAlphaF(alpha)
    return c


class Toggle(QCheckBox):
    """Interruptor Fluent: pista hueca + pulgar que se desliza al encender."""

    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)     # sin esto no llegan los eventos de hover

        self._progreso = 1.0 if self.isChecked() else 0.0
        self._radio = RADIO_REPOSO
        self._pulsado = False

        self._anim_pos = QPropertyAnimation(self, b"progreso", self)
        self._anim_pos.setDuration(DURACION_MS)
        self._anim_pos.setEasingCurve(QEasingCurve.OutCubic)   # arranca rapido, frena al llegar

        self._anim_radio = QPropertyAnimation(self, b"radio", self)
        self._anim_radio.setDuration(style.DURACION_HOVER_MS)
        self._anim_radio.setEasingCurve(QEasingCurve.OutCubic)

        # Los colores se leen en cada pintado (`style.tema_actual()`), nunca se cachean: si no, un
        # cambio de tema en caliente no se veria. Igual que en `status_badge.py`.
        style.bus().cambiado.connect(self.update)

    # ------------------------------------------------------------------ sincronizacion
    def checkStateSet(self):
        """Qt llama a esto SIEMPRE que cambia el estado, tambien con las senales bloqueadas.

        Aqui estaba el fallo: el pulgar se movia enganchado a la senal `toggled`, asi que el patron
        normal para cargar un valor sin disparar handlers

            t.blockSignals(True); t.setChecked(True); t.blockSignals(False)

        dejaba el interruptor ENCENDIDO por dentro y APAGADO por fuera. La interfaz mentia sobre su
        propio estado, y encima solo al cargar preferencias, que es justo cuando nadie mira.
        `checkStateSet` es el gancho que no se puede silenciar.
        """
        super().checkStateSet()
        self._animar_a(self.isChecked())

    def nextCheckState(self):
        """Sincroniza también los cambios iniciados por clic o teclado.

        Qt no pasa esos cambios por ``checkStateSet``: usa directamente este gancho. Por eso el
        estado lógico cambiaba pero la pista seguía apagada al pulsar el interruptor.
        """
        super().nextCheckState()
        self._animar_a(self.isChecked())

    # ------------------------------------------------------------------ propiedades animables
    def _get_progreso(self):
        return self._progreso

    def _set_progreso(self, valor):
        self._progreso = float(valor)
        self.update()

    progreso = Property(float, _get_progreso, _set_progreso)

    def _get_radio(self):
        return self._radio

    def _set_radio(self, valor):
        self._radio = float(valor)
        self.update()

    radio = Property(float, _get_radio, _set_radio)

    # ------------------------------------------------------------------ animacion
    def _lanzar(self, anim, actual, destino, salto):
        """Anima de `actual` a `destino`, o salta con `salto` si las animaciones estan apagadas."""
        anim.stop()
        if not style.animaciones_activas():
            salto(destino)
            return
        anim.setStartValue(actual)
        anim.setEndValue(destino)
        anim.start()

    def _animar_a(self, activo):
        self._lanzar(self._anim_pos, self._progreso, 1.0 if activo else 0.0, self._set_progreso)

    def _animar_radio(self, destino):
        self._lanzar(self._anim_radio, self._radio, destino, self._set_radio)

    def _radio_objetivo(self):
        """El pulgar crece si el raton esta encima o si el interruptor tiene el foco del teclado.

        El foco se señala ASI, engordando el pulgar, y no con un anillo alrededor: un anillo hay que
        pintarlo FUERA de la pista, y ahi Qt lo recorta contra el borde del widget y se ve partido.
        """
        if not self.isEnabled():
            return RADIO_REPOSO
        return RADIO_HOVER if (self.underMouse() or self.hasFocus()) else RADIO_REPOSO

    # ------------------------------------------------------------------ eventos
    def enterEvent(self, ev):
        super().enterEvent(ev)
        self._animar_radio(self._radio_objetivo())

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        self._animar_radio(self._radio_objetivo())

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self._animar_radio(self._radio_objetivo())

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        self._animar_radio(self._radio_objetivo())

    def mousePressEvent(self, ev):
        self._pulsado = True
        self.update()
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._pulsado = False
        self.update()
        super().mouseReleaseEvent(ev)

    # ------------------------------------------------------------------ tamano
    def sizeHint(self):
        alto = max(PISTA_H + 4, self.fontMetrics().height() + 4)
        ancho = MARGEN_X * 2 + PISTA_W
        if self.text():
            ancho += HUECO_TEXTO + self.fontMetrics().horizontalAdvance(self.text())
        return QSize(ancho, alto)

    def minimumSizeHint(self):
        return self.sizeHint()

    # ------------------------------------------------------------------ pintado
    def paintEvent(self, ev):
        t = style.tema_actual()
        activo = self.isEnabled()
        p = self.progreso

        # El margen deja sitio al suavizado del borde: pegada al x=0 la pista se veria mordida.
        pista = QRectF(MARGEN_X, (self.height() - PISTA_H) / 2.0, PISTA_W, PISTA_H)

        # Apagado: pista hueca (solo borde). Encendido: pista rellena de acento. Entre medias se
        # mezclan, asi que el color aparece a la vez que el pulgar se desliza.
        relleno_off = QColor(t.superficie_alta) if self.underMouse() else QColor(0, 0, 0, 0)
        # Todos los controles interactivos comparten el mismo acento de marca.
        relleno_on = QColor(t.acento_hover if self.underMouse() else t.acento)
        borde_off = QColor(t.texto_tenue)
        borde_on = relleno_on

        relleno = _mezcla(relleno_off, relleno_on, p)
        borde = _mezcla(borde_off, borde_on, p)
        pulgar = _mezcla(QColor(t.texto_tenue), QColor("#ffffff"), p)

        if not activo:                       # deshabilitado: todo atenuado, pero se sigue leyendo
            relleno = _atenua(relleno, relleno.alphaF() * 0.35)
            borde = _atenua(borde, 0.35)
            pulgar = _atenua(pulgar, 0.45)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setBrush(relleno)
        painter.setPen(QPen(borde, BORDE_PISTA))
        radio_pista = PISTA_H / 2.0
        painter.drawRoundedRect(pista.adjusted(BORDE_PISTA / 2, BORDE_PISTA / 2,
                                               -BORDE_PISTA / 2, -BORDE_PISTA / 2),
                                radio_pista, radio_pista)

        # Pulgar. Al mantener pulsado se ESTIRA en ovalo (como el de Windows 11), creciendo hacia el
        # lado al que va a ir: es lo que da la sensacion de que el interruptor "cede".
        r = self._radio
        estira = ESTIRA_PULSADO if (self._pulsado and activo) else 0.0
        x_izq = pista.left() + PISTA_H / 2.0        # centro del extremo redondeado izquierdo
        x_der = pista.right() - PISTA_H / 2.0       # ... y del derecho
        cx = x_izq + (x_der - x_izq) * p
        cy = pista.center().y()

        # El ovalo del pulsado crece a los lados, pero nunca se sale de la pista.
        limite_izq = pista.left() + BORDE_PISTA + 1.0
        limite_der = pista.right() - BORDE_PISTA - 1.0
        izq = max(cx - r - estira / 2.0, limite_izq)
        der = min(cx + r + estira / 2.0, limite_der)
        pulgar_rect = QRectF(izq, cy - r, der - izq, 2 * r)

        painter.setPen(Qt.NoPen)
        painter.setBrush(pulgar)
        painter.drawRoundedRect(pulgar_rect, r, r)

        if self.text():
            color_texto = QColor(t.texto) if activo else _atenua(QColor(t.texto), 0.4)
            painter.setPen(color_texto)
            x = pista.right() + HUECO_TEXTO
            painter.drawText(QRectF(x, 0, self.width() - x, self.height()),
                             Qt.AlignVCenter | Qt.AlignLeft, self.text())
        painter.end()
