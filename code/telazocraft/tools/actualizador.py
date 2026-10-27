import subprocess
import tempfile
from pathlib import Path
from ..motor.util import descargar
from ..motor.java import OCULTO


def preparar(actualizacion, progreso=lambda n,t:None):
    carpeta = Path(tempfile.mkdtemp(prefix="telazocraft_actualizacion_"))
    return descargar(actualizacion["url"], carpeta / actualizacion["nombre"], actualizacion["sha256"],progreso=progreso)


def ejecutar(instalador):
    return subprocess.Popen([str(instalador), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"],
                            creationflags=OCULTO)
