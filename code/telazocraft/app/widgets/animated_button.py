# -*- coding: utf-8 -*-
"""Botón común con una confirmación visual breve y barata al pulsar."""

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QStyle, QStyleOptionButton, QStylePainter

from .. import style


class AnimatedButton(QPushButton):
    """QPushButton compatible que añade pulso de acento y hundimiento de un píxel."""

    DURACION_MS = 140

    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._feedback = 0.0
        self._anim_feedback = QPropertyAnimation(self, b"feedback", self)
        self._anim_feedback.setDuration(self.DURACION_MS)
        self._anim_feedback.setEasingCurve(QEasingCurve.OutCubic)
        style.bus().cambiado.connect(self.update)

    def _get_feedback(self):
        return self._feedback

    def _set_feedback(self, valor):
        self._feedback = max(0.0, min(1.0, float(valor)))
        self.update()

    feedback = Property(float, _get_feedback, _set_feedback)

    def _pulsar_visual(self):
        if not self.isEnabled():
            return
        self._anim_feedback.stop()
        self._set_feedback(1.0)

    def _soltar_visual(self):
        if self._feedback <= 0.0:
            return
        self._anim_feedback.stop()
        self._anim_feedback.setStartValue(self._feedback)
        self._anim_feedback.setEndValue(0.0)
        self._anim_feedback.start()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._pulsar_visual()
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        if ev.button() == Qt.LeftButton:
            self._soltar_visual()

    def leaveEvent(self, ev):
        if self.isDown():
            self._soltar_visual()
        super().leaveEvent(ev)

    def keyPressEvent(self, ev):
        if not ev.isAutoRepeat() and ev.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._pulsar_visual()
        super().keyPressEvent(ev)

    def keyReleaseEvent(self, ev):
        super().keyReleaseEvent(ev)
        if not ev.isAutoRepeat() and ev.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._soltar_visual()

    def changeEvent(self, ev):
        if not self.isEnabled():
            self._anim_feedback.stop()
            self._set_feedback(0.0)
        super().changeEvent(ev)

    def paintEvent(self, _ev):
        opcion = QStyleOptionButton()
        self.initStyleOption(opcion)
        painter = QStylePainter(self)
        painter.drawControl(QStyle.CE_PushButtonBevel, opcion)

        if self._feedback > 0.0 and self.isEnabled():
            color = QColor(style.tema_actual().acento_claro)
            color.setAlphaF(0.24 * self._feedback)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            caja = self.rect().adjusted(2, 2, -2, -2)
            radio = max(2, style.R_CONTROL - 2)
            painter.drawRoundedRect(caja, radio, radio)

        painter.save()
        painter.translate(0.0, self._feedback)
        painter.drawControl(QStyle.CE_PushButtonLabel, opcion)
        painter.restore()
