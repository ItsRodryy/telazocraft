from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from pathlib import Path
import os
from . import style


def crear_app():
    app = QApplication.instance() or QApplication([])
    if not QFontDatabase.families() and os.name == "nt":
        carpeta = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for nombre in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"):
            if (carpeta / nombre).is_file():
                QFontDatabase.addApplicationFont(str(carpeta / nombre))
    app.setApplicationName("Telazocraft")
    app.setOrganizationName("Telazocraft")
    app.setQuitOnLastWindowClosed(False)
    style.aplicar_tema(app, style.desde_preferencias({"tema_color": "gris", "transparencia": False}))
    from .widgets import fundido
    fundido.instalar(app)
    return app
