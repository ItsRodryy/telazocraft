"""Resultados Modrinth con iconos locales y descarga fuera del hilo de interfaz."""
import hashlib
import threading
import urllib.parse
import urllib.request
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from ...common import ajustes
from .. import icons
from ...common.i18n import tr


class ListaMods(QListWidget):
    icono_listo = Signal(str)

    def __init__(self):
        super().__init__()
        self.icono_listo.connect(self.pintar_icono)

    @staticmethod
    def ruta_icono(url):
        return ajustes.ruta().parent / 'iconos_mods' / (hashlib.sha256(url.encode()).hexdigest() + '.png')

    def cargar(self, hits):
        self.clear()
        pendientes = []
        for hit in hits:
            url = hit.get('icon_url') or ''
            ruta = self.ruta_icono(url)
            item = QListWidgetItem(QIcon(str(ruta)) if ruta.exists() else icons.glifo('mods', 24), hit['title']+(' · '+tr('Instalado') if hit.get('instalado') else ''))
            item.setData(Qt.UserRole, url)
            self.addItem(item)
            if url and not ruta.exists():
                pendientes.append(url)

        def descargar():
            for url in dict.fromkeys(pendientes):
                partes = urllib.parse.urlsplit(url)
                if partes.scheme != 'https' or partes.hostname != 'cdn.modrinth.com':
                    continue
                try:
                    with urllib.request.urlopen(url, timeout=5) as r:
                        datos = r.read(2 * 1024 * 1024)
                    ruta = self.ruta_icono(url)
                    ruta.parent.mkdir(parents=True, exist_ok=True)
                    ruta.write_bytes(datos)
                    self.icono_listo.emit(url)
                except (OSError, RuntimeError):
                    pass
        if pendientes:
            threading.Thread(target=descargar, daemon=True).start()

    def pintar_icono(self, url):
        icono = QIcon(str(self.ruta_icono(url)))
        if icono.isNull():
            return
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == url:
                item.setIcon(icono)
