import subprocess
import re
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from .java import buscar, OCULTO
from .util import descargar
from .util import huella

MAVEN = "https://maven.neoforged.net/releases/net/neoforged/neoforge"


def versiones():
    with urllib.request.urlopen(MAVEN + "/maven-metadata.xml", timeout=30) as r:
        return [n.text for n in ET.fromstring(r.read()).findall("./versioning/versions/version")]


def instalador(servidor, carpeta, progreso=lambda n,total:None):
    v = servidor.datos["version_loader"]
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+(?:-[a-zA-Z0-9.]+)?',v):raise ValueError('Versión de NeoForge inválida')
    nombre = f"neoforge-{v}-installer.jar"
    url = MAVEN + f"/{v}/{nombre}"
    with urllib.request.urlopen(url + ".sha256", timeout=30) as r:
        sha = r.read().decode().strip().split()[0]
    destino=Path(carpeta)/nombre
    if destino.exists() and huella(destino)==sha:return destino
    return descargar(url,destino,sha,progreso=progreso)

def instalar(servidor):
    servidor.exigir_parado()
    jar=instalador(servidor,servidor.ruta)
    subprocess.run([buscar(servidor.datos["java_mayor"]), "-jar", str(jar), "--install-server"],
                   cwd=servidor.ruta, check=True, timeout=900, creationflags=OCULTO)
