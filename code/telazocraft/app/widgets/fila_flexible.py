# -*- coding: utf-8 -*-
"""Fila de controles que se reparte en varias cuando deja de caber.

Una `QHBoxLayout` con cuatro botones de texto no tiene plan B: cuando falta ancho, Qt los comprime
por debajo de su tamaño natural y los rótulos se cortan («Restablec…»). El usuario no ve un
problema de espacio, ve un programa mal hecho.

Esto reparte los mismos controles en las filas que hagan falta, respetando siempre su ancho
natural. `capture_tab` ya resolvía su barra así, pero con una rejilla de 12 columnas escrita a mano
para sus controles concretos; esto es lo mismo sin conocer a nadie.
"""

from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget


class FilaFlexible(QWidget):
    """Coloca los controles en una fila, o en varias si el ancho no da."""

    def __init__(self, controles=(), separacion=8, estirar_ultimo=False, parent=None):
        super().__init__(parent)
        self._controles = []
        self._columnas = 0
        self._rejilla = QGridLayout(self)
        self._rejilla.setContentsMargins(0, 0, 0, 0)
        self._rejilla.setHorizontalSpacing(separacion)
        self._rejilla.setVerticalSpacing(separacion)
        self._estirar_ultimo = bool(estirar_ultimo)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        for control in controles:
            self.anadir(control)

    def anadir(self, control):
        control.setParent(self)
        self._controles.append(control)
        self._recolocar(forzar=True)

    def quitar(self, control):
        """La simétrica de `anadir`. Sin ella, una fila que refleja algo cambiante —las cámaras que
        hay conectadas— solo podría crecer."""
        if control not in self._controles:
            return
        self._controles.remove(control)
        control.setParent(None)
        self._recolocar(forzar=True)

    def controles(self):
        return list(self._controles)

    def columnas(self):
        """Cuántos controles hay por fila ahora mismo. Lo usan las pruebas."""
        return self._columnas

    def _cuantos_caben(self):
        if not self._controles:
            return 0
        separacion = self._rejilla.horizontalSpacing()
        ancho = max(1, self.width())
        # Se reparte por el control MÁS ANCHO: con anchos distintos, ajustar por el estrecho dejaría
        # al otro fuera. Que todas las columnas quepan es lo único que evita el recorte.
        mayor = max(c.sizeHint().width() for c in self._controles)
        caben = max(1, int((ancho + separacion) // (mayor + separacion)))
        return min(caben, len(self._controles))

    def _recolocar(self, forzar=False):
        caben = self._cuantos_caben()
        if not forzar and caben == self._columnas:
            return
        self._columnas = caben
        while self._rejilla.count():
            self._rejilla.takeAt(0)
        for columna in range(len(self._controles)):
            self._rejilla.setColumnStretch(columna, 0)
        for indice, control in enumerate(self._controles):
            self._rejilla.addWidget(control, indice // caben, indice % caben)
        if self._estirar_ultimo and caben:
            self._rejilla.setColumnStretch(caben - 1, 1)
        self._rejilla.invalidate()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._recolocar()
