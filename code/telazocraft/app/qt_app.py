from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from pathlib import Path
import os
from . import style


def crear_app():
    if os.name == 'nt' and QApplication.instance() is None:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ItsRodryy.Telazocraft')
    app = QApplication.instance() or QApplication([])
    if not getattr(app,'_log_configurado',False):
        import logging
        from logging.handlers import RotatingFileHandler
        from ..common import ajustes
        carpeta=ajustes.ruta().parent;carpeta.mkdir(parents=True,exist_ok=True)
        handler=RotatingFileHandler(carpeta/'telazocraft.log',maxBytes=1024*1024,backupCount=2,encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
        logging.getLogger('telazocraft').addHandler(handler);logging.getLogger('telazocraft').setLevel(logging.INFO)
        app._log_configurado=True
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
    from . import interaction
    interaction.instalar(app)
    return app
