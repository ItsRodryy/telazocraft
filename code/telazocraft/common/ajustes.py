import os
from pathlib import Path
from ..motor.util import guardar_json, leer_json


def ruta():
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "Telazocraft" / "ajustes.json"


def cargar():
    try:
        return leer_json(ruta(), {})
    except (ValueError, OSError):
        return {}


def guardar(datos):
    guardar_json(ruta(), datos)
