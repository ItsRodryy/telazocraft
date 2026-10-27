# -*- coding: utf-8 -*-
"""Widgets pegados a una esquina de otro widget, sin layout y sin saltos.

Los botones de pantalla completa y los rótulos superpuestos de los visores no pueden ir en un layout
—taparían imagen o robarían sitio—, así que se colocan a mano sobre el panel. Hacerlo suelto en cada
pestaña salía caro: cada una calculaba la esquina a su manera y recolocaba con `QTimer.singleShot`,
así que al entrar en pantalla completa el botón se veía viajar por la pantalla en dos o tres saltos.
Una geometría nueva llegaba, el botón seguía en la anterior y solo se ponía en su sitio un
fotograma —o 120 ms— después.

Aquí el flotante es **hijo del panel** y se recoloca en el `resizeEvent` del propio panel, que es
síncrono y ocurre antes de pintar: cuando el panel aparece con su tamaño nuevo, el flotante ya está
en la esquina. No hay temporizadores.

Se ancla UN widget por ancla. Si hacen falta varios botones juntos, se meten en un contenedor con su
layout y se ancla el contenedor: repartirlos es trabajo de Qt, no de este módulo.
"""

from PySide6.QtCore import QEvent, QObject

ARRIBA_IZQUIERDA = "arriba-izquierda"
ARRIBA_DERECHA = "arriba-derecha"
ABAJO_IZQUIERDA = "abajo-izquierda"
ABAJO_DERECHA = "abajo-derecha"


class AnclaEsquina(QObject):
    """Mantiene `flotante` pegado a una esquina de un panel, que puede cambiar en caliente."""

    def __init__(self, flotante, esquina=ABAJO_IZQUIERDA, margen=8, parent=None):
        super().__init__(parent)
        self._flotante = flotante
        self._esquina = esquina
        self._margen = int(margen)
        self._objetivo = None
        # Si el flotante debe verse cuando su panel se ve. Lo decide quien ancla, con `set_visible`;
        # no se deduce de `isVisible()`, que es False mientras el panel todavía no está en pantalla y
        # dejaba el botón escondido para siempre.
        self._visible = True
        # `adjustSize()` puede disparar el `Resize` que este mismo filtro escucha. Sin esta guarda la
        # llamada se muerde la cola en cuanto el flotante cambia de tamaño.
        self._recolocando = False
        # El flotante también cambia de tamaño (un rótulo que crece, un botón que aparece): si no se
        # escucha, se queda anclado por la esquina que tenía antes de crecer.
        flotante.installEventFilter(self)

    def objetivo(self):
        return self._objetivo

    def set_objetivo(self, objetivo):
        """Reparenta el flotante al panel dado. Con `None` lo deja huérfano y oculto."""
        if objetivo is self._objetivo:
            self.recolocar()
            return
        if self._objetivo is not None:
            self._objetivo.removeEventFilter(self)
        self._objetivo = objetivo
        if objetivo is None:
            self._flotante.setParent(None)
            self._flotante.hide()
            return
        objetivo.installEventFilter(self)
        # Reparentar oculta el widget: Qt lo hace siempre, y sin esto el botón desaparecía al pasar
        # de la rejilla a la vista enfocada.
        self._flotante.setParent(objetivo)
        self._flotante.setVisible(self._visible)
        self.recolocar()

    def set_visible(self, visible):
        """Enciende o apaga el flotante. Se respeta al reanclar y al mostrarse el panel."""
        self._visible = bool(visible)
        if self._objetivo is not None:
            self._flotante.setVisible(self._visible)

    def set_esquina(self, esquina):
        self._esquina = esquina
        self.recolocar()

    def _dimensionar(self):
        """El tamaño natural del flotante, con el texto YA envuelto al ancho que le toca.

        `adjustSize()` no vale aquí: pregunta el `sizeHint`, y el de un widget con etiquetas de
        varias líneas se calcula sin saber a qué ancho van a quedar. Un recuadro con seis avisos
        salía con alto para dos líneas y el resto se quedaba cortado. Fuera de un layout, el ancho lo
        decidimos nosotros, así que se puede preguntar el alto para ESE ancho, que es exacto.
        """
        flotante = self._flotante
        hint = flotante.sizeHint()
        ancho = min(hint.width(), flotante.maximumWidth())
        alto = hint.height()
        if flotante.hasHeightForWidth():
            alto = max(alto, flotante.heightForWidth(ancho))
        flotante.resize(ancho, alto)

    def recolocar(self):
        objetivo = self._objetivo
        if objetivo is None or self._recolocando or self._flotante.parent() is not objetivo:
            return
        self._recolocando = True
        try:
            self._dimensionar()
            ancho, alto = self._flotante.width(), self._flotante.height()
            margen = self._margen
            derecha = max(margen, objetivo.width() - ancho - margen)
            abajo = max(margen, objetivo.height() - alto - margen)
            x = derecha if self._esquina in (ARRIBA_DERECHA, ABAJO_DERECHA) else margen
            y = abajo if self._esquina in (ABAJO_IZQUIERDA, ABAJO_DERECHA) else margen
            self._flotante.move(x, y)
            self._flotante.raise_()
        finally:
            self._recolocando = False

    def eventFilter(self, objeto, evento):
        tipo = evento.type()
        if objeto is self._objetivo and tipo in (QEvent.Resize, QEvent.Show, QEvent.LayoutRequest):
            if tipo == QEvent.Show:
                # El panel entra en pantalla: el flotante va con él. Reparentar lo había ocultado y
                # sin esto se quedaba escondido aunque estuviera en su sitio.
                self._flotante.setVisible(self._visible)
            self.recolocar()
        elif objeto is self._flotante and tipo in (QEvent.Resize, QEvent.Show,
                                                  QEvent.LayoutRequest):
            self.recolocar()
        return False
