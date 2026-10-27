import re
from pathlib import Path
from .. import __version__
from . import ajustes
from ..motor.util import http_json, leer_json

# Repositorio público por defecto; el empaquetador de Actions lo fija en recursos/release.json.
REPOSITORIO = "ItsRodryy/telazocraft"


def version(texto):
    if not re.fullmatch(r"v?\d+\.\d+\.\d+", texto):
        raise ValueError("Versión no válida")
    return tuple(int(x) for x in texto.lstrip("v").split("."))


def repositorio():
    meta = leer_json(Path(__file__).parents[1] / "recursos/release.json", {})
    return ajustes.cargar().get("repo_actualizaciones", "") or meta.get("repositorio", "") or REPOSITORIO


def ultima(repo=None):
    repo = repo or repositorio()
    if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Repositorio de actualizaciones no válido")
    d = http_json("https://api.github.com/repos/" + repo + "/releases/latest")
    if d.get("draft") or d.get("prerelease"):
        raise ValueError("La publicación no es una versión estable")
    v = d["tag_name"].lstrip("v")
    version(v)
    nombre = f"Telazocraft-{v}-windows.exe"
    asset = next((a for a in d["assets"] if a["name"] == nombre), None)
    if not asset:
        raise ValueError("La publicación no contiene el instalador para Windows")
    digest = asset.get("digest", "")
    if not re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
        raise ValueError("GitHub no publica un SHA-256 verificable para el instalador")
    if not asset["browser_download_url"].startswith("https://github.com/" + repo + "/releases/download/"):
        raise ValueError("URL de instalador inesperada")
    return {"version": v, "nueva": version(v) > version(__version__), "url": asset["browser_download_url"],
            "sha256": digest.split(":", 1)[1], "nombre": nombre, "notas": d.get("body", "")}
