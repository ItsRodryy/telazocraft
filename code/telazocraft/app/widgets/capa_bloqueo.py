# -*- coding: utf-8 -*-
"""Velo oscuro con el motivo en blanco sobre una pantalla que ahora no puede trabajar.

Nació en Fusión y medición (sin las dos cámaras) y se usa igual en Calibración y Pruebas con la
cámara desconectada (decisión del usuario, 13/10/2026). Apaga a la vista sin tragarse el ratón: lo
que no necesita cámara (mirar, desplazarse, el Comparador) sigue respondiendo, y quien la usa
bloquea sus propias acciones.

Contrato: hija de la pantalla que tapa (`anfitrion`); se recoloca sola al cambiar de tamaño.
`aplicar(motivo)` la enseña con ese texto o la esconde con "".
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class CapaBloqueo(QFrame):
    def __init__(self, anfitrion):
        super().__init__(anfitrion)
        self.setObjectName("capaBloqueo")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(48, 32, 48, 32)
        capa.addStretch(1)
        self.texto = QLabel("")
        self.texto.setObjectName("motivoBloqueo")
        self.texto.setAlignment(Qt.AlignCenter)
        self.texto.setWordWrap(True)
        capa.addWidget(self.texto)
        capa.addStretch(1)
        self._motivo = ""
        anfitrion.installEventFilter(self)
        self.hide()

    def motivo(self):
        return self._motivo

    def aplicar(self, motivo):
        """Enseña el velo con `motivo` o lo quita con "". Devuelve si queda puesto."""
        motivo = str(motivo or "")
        self._motivo = motivo
        self.texto.setText(motivo)
        self._encajar()
        self.setVisible(bool(motivo))
        return bool(motivo)

    def _encajar(self):
        anfitrion = self.parentWidget()
        if anfitrion is not None:
            self.setGeometry(anfitrion.rect())
            self.raise_()

    def eventFilter(self, objeto, evento):
        if objeto is self.parentWidget() and evento.type() in (QEvent.Resize, QEvent.Show):
            self._encajar()
        return super().eventFilter(objeto, evento)
