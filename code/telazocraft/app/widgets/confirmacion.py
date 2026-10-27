# -*- coding: utf-8 -*-
"""Pregunta de confirmación dentro de la propia ventana, en lugar de un aviso encima.

Petición del usuario (06/10/2026): en los flujos de versiones y de SDK no quiere ventanas que se
abran encima de otras, tampoco las de «¿Seguro?». Esto es un panel que aparece en su sitio con el
texto y dos botones, y desaparece al responder.

Contrato: una sola pregunta a la vez; `preguntar` sustituye a la anterior sin responderla.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from .animated_button import AnimatedButton
from ...common.i18n import tr


class Confirmacion(QFrame):
    # Al aparecer o desaparecer: la ventana que la aloja ajusta su alto.
    cambiada = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(10)
        self.texto = QLabel("")
        self.texto.setWordWrap(True)
        self.texto.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(self.texto)
        pie = QHBoxLayout()
        pie.addStretch(1)
        self.btn_no = AnimatedButton(tr("No"))
        self.btn_no.clicked.connect(lambda: self._responder(False))
        pie.addWidget(self.btn_no)
        self.btn_si = AnimatedButton(tr("Sí"))
        self.btn_si.setObjectName("aplicar")
        self.btn_si.clicked.connect(lambda: self._responder(True))
        pie.addWidget(self.btn_si)
        v.addLayout(pie)
        self._al_si = None
        self._al_no = None
        self.setVisible(False)

    def preguntar(self, texto, al_si, si="Sí", no="No", al_no=None, por_defecto_no=False):
        """Enseña la pregunta. `al_si()` o `al_no()` se llaman al responder.

        `por_defecto_no` pone el foco en «No» (borrar, volver atrás): Intro no confirma sin querer.
        """
        self.texto.setText(texto)
        self.btn_si.setText(si)
        self.btn_no.setText(no)
        self._al_si, self._al_no = al_si, al_no
        self.setVisible(True)
        (self.btn_no if por_defecto_no else self.btn_si).setFocus()
        self.cambiada.emit()

    def abierta(self):
        return not self.isHidden()

    def cerrar(self):
        self._al_si = self._al_no = None
        if not self.isHidden():
            self.setVisible(False)
            self.cambiada.emit()

    def _responder(self, si):
        accion = self._al_si if si else self._al_no
        self.cerrar()
        if accion is not None:
            accion()
