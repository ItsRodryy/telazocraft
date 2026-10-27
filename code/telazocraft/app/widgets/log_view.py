# -*- coding: utf-8 -*-
"""Consola integrada: el log del servidor, sin abrir ficheros."""

from PySide6.QtWidgets import QPlainTextEdit


_MAX_LINEAS = 2000


class LogView(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setObjectName("log")
        self.setReadOnly(True)
        self.setMaximumBlockCount(_MAX_LINEAS)   # descarta lo viejo: no crece sin limite
        # El texto y la barra de desplazamiento se pintan hasta el borde: sin recortar de verdad,
        # las esquinas del panel se ven cuadradas por mucho `border-radius` que tenga el QSS.

    def agregar(self, linea):
        self.appendPlainText(linea)
