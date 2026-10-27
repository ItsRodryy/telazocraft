import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

AGENTE = "telazocraft/0.1.0"


def ruta_dentro(base, *partes):
    base = Path(base).resolve()
    destino = base.joinpath(*partes).resolve()
    if not destino.is_relative_to(base):
        raise ValueError("Ruta fuera de la biblioteca")
    return destino


def identificador(valor):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", valor):
        raise ValueError("Identificador no válido")
    return valor


def leer_json(ruta, defecto=None):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except FileNotFoundError:
        if defecto is None:
            raise
        return defecto


def guardar_json(ruta, datos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + ".tmp")
    with temporal.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporal, ruta)


def huella(ruta, algoritmo="sha256"):
    h = hashlib.new(algoritmo)
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def archivar(ruta, carpeta):
    ruta, carpeta = Path(ruta), Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / ruta.name
    if destino.exists():
        destino = carpeta / (ruta.name + "." + str(time.time_ns()))
    shutil.move(str(ruta), str(destino))
    return destino


def http_json(url, datos=None, metodo=None, cabeceras=None, timeout=30):
    headers = {"User-Agent": AGENTE, "Accept": "application/json", **(cabeceras or {})}
    cuerpo = None
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=cuerpo, headers=headers, method=metodo)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def descargar(url, destino, esperado, algoritmo="sha256", progreso=lambda leidos,total: None):
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError("La descarga debe usar HTTPS")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + ".descarga")
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=60) as r, temporal.open("wb") as f:
        total=int(getattr(r,'headers',{}).get('Content-Length',0));leidos=0
        for bloque in iter(lambda:r.read(1024*1024),b''):
            f.write(bloque);leidos+=len(bloque);progreso(leidos,total)
    if huella(temporal, algoritmo).lower() != esperado.lower():
        archivar(temporal, destino.parent / "descargas_fallidas")
        raise ValueError("La descarga no coincide con su hash")
    os.replace(temporal, destino)
    return destino
