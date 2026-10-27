# -*- coding: utf-8 -*-
"""Botón que abre en el explorador del sistema la carpeta de lo que haya elegido.

Vive en los widgets comunes y no en Volumen porque lo quieren todos los selectores del programa:
calibración, carpeta de captura, YAML, intrínsecas. Escribirlo una vez evita que cada pantalla se
invente su forma de abrir una carpeta, que es como acaban comportándose distinto.

`QDesktopServices.openUrl` es lo que hay que usar aquí: delega en el escritorio, así que abre el
Explorador en Windows y Nautilus en Ubuntu sin una sola línea por plataforma. Lanzar `explorer.exe`
o `xdg-open` a mano obligaría a escribir dos caminos y a mantener los dos.
"""

import os
import logging

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from .icon_button import IconButton
from ...common.i18n import tr

AYUDA = tr("Abrir la carpeta en el explorador")


def abrir_carpeta(ruta):
    """Abre la carpeta de `ruta`. Si `ruta` es un fichero, abre la carpeta que lo contiene.

    Sube por los padres hasta encontrar una carpeta que exista: pedir que se abra algo que aún no se
    ha creado es lo normal —una salida que todavía no se ha escrito—, y ahí lo útil es abrir lo más
    cercano que sí existe, no no hacer nada.
    """
    ruta = str(ruta or "").strip()
    if not ruta:
        return False
    destino = os.path.abspath(ruta)
    if not os.path.isdir(destino):
        destino = os.path.dirname(destino)
    while destino and not os.path.isdir(destino):
        padre = os.path.dirname(destino)
        if padre == destino:
            return False
        destino = padre
    if not destino:
        return False
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(destino)))


class BotonCarpeta(IconButton):
    """`proveedor` es un invocable que devuelve la ruta actual: así el botón nunca se desactualiza."""

    def __init__(self, proveedor, tooltip=AYUDA, parent=None):
        super().__init__("carpeta", tooltip, size=14)
        if parent is not None:
            self.setParent(parent)
        self._proveedor = proveedor
        self.setFixedWidth(30)
        self.clicked.connect(self._abrir)

    def _abrir(self):
        try:
            ruta = self._proveedor() or ""
        except Exception as exc:
            logging.getLogger(__name__).exception('No se pudo obtener la carpeta')
            if hasattr(self.window(),'mostrar_error'):self.window().mostrar_error(tr('No se pudo abrir la carpeta: %s')%exc)
            return False
        ok=abrir_carpeta(ruta)
        if not ok:
            logging.getLogger(__name__).warning('No se pudo abrir la carpeta')
            if hasattr(self.window(),'mostrar_error'):self.window().mostrar_error(tr('No se pudo abrir la carpeta'))
        return ok
