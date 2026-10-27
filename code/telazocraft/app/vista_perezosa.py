# -*- coding: utf-8 -*-
"""Hueco estable del ``QStackedWidget`` que construye una vista al usarla por primera vez."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from ..common.i18n import tr


class VistaPerezosa(QWidget):
    construida = Signal(object)

    def __init__(self, fabrica, nombre="Vista", parent=None):
        super().__init__(parent)
        self._fabrica = fabrica
        self._nombre = str(nombre)
        self._widget = None
        self._error = None
        self._construyendo = False
        self._pendientes = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._espera = QLabel(tr("Preparando %s…") % self._nombre)
        self._espera.setObjectName("tenue")
        self._espera.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._espera, 1)

    def construida_ya(self):
        return self._widget is not None

    def widget(self):
        return self._widget

    def construir(self, propagar=False):
        if self._widget is not None:
            return self._widget
        if self._error is not None and not propagar:
            return None
        # Guardia de reentrada. Construir una vista puede procesar eventos por dentro —el visor 3D
        # inicializa OpenGL, y eso vacía la cola de Qt—, así que llegaba un segundo `showEvent`
        # mientras el primero seguía dentro de la fábrica: `self._widget` aún era None y se
        # construía la vista DOS veces, una debajo de otra. Se veía como la pantalla de Volumen
        # repetida entera, con su barra y su panel de medidas.
        if self._construyendo:
            return None
        self._construyendo = True
        try:
            widget = self._fabrica()
            if not isinstance(widget, QWidget):
                raise TypeError("La fábrica de %s no devolvió un QWidget." % self._nombre)
            self._layout.removeWidget(self._espera)
            # Se oculta ya: `deleteLater` espera al bucle de eventos y, mientras, el rótulo asomaba
            # por el hueco transparente que queda entre los paneles de la vista nueva.
            self._espera.hide()
            self._espera.deleteLater()
            self._layout.addWidget(widget, 1)
            self._widget = widget
            for nombre, (args, kwargs) in list(self._pendientes.items()):
                funcion = getattr(widget, nombre, None)
                if callable(funcion):
                    funcion(*args, **kwargs)
            self._pendientes.clear()
            self.construida.emit(widget)
            return widget
        except Exception as exc:
            self._error = exc
            self._espera.setText(tr("No se pudo abrir %s: %s") % (self._nombre, exc))
            if propagar:
                raise
            return None
        finally:
            self._construyendo = False

    def invocar(self, nombre, *args, **kwargs):
        if self._widget is not None:
            funcion = getattr(self._widget, nombre, None)
            return funcion(*args, **kwargs) if callable(funcion) else None
        self._pendientes[nombre] = (args, kwargs)
        return None

    def set_worker(self, worker):
        return self.invocar("set_worker", worker)

    def aplicar_preferencias(self, preferencias):
        return self.invocar("aplicar_preferencias", preferencias)

    def set_modo_trabajo(self, modo):
        return self.invocar("set_modo_trabajo", modo)

    def set_modo(self, modo):
        return self.invocar("set_modo", modo)

    def detener(self):
        if self._widget is not None:
            return self.invocar("detener")
        return None

    def resolver_pendientes(self, permitir_cancelar=True):
        """Sin construir no hay nada pendiente; construida, decide la vista (True = seguir)."""
        if self._widget is None:
            return True
        funcion = getattr(self._widget, "resolver_pendientes", None)
        return bool(funcion(permitir_cancelar)) if callable(funcion) else True

    def showEvent(self, evento):
        super().showEvent(evento)
        self.construir()

