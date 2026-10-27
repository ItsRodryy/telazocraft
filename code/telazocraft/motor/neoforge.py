import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from .java import buscar, OCULTO
from .util import descargar

MAVEN = "https://maven.neoforged.net/releases/net/neoforged/neoforge"


def versiones():
    with urllib.request.urlopen(MAVEN + "/maven-metadata.xml", timeout=30) as r:
        return [n.text for n in ET.fromstring(r.read()).findall("./versioning/versions/version")]


def instalar(servidor):
    servidor.exigir_parado()
    v = servidor.datos["version_loader"]
    if v not in versiones():
        raise ValueError("Versión de NeoForge inexistente")
    nombre = f"neoforge-{v}-installer.jar"
    url = MAVEN + f"/{v}/{nombre}"
    with urllib.request.urlopen(url + ".sha256", timeout=30) as r:
        sha = r.read().decode().strip().split()[0]
    jar = descargar(url, servidor.ruta / nombre, sha)
    subprocess.run([buscar(servidor.datos["java_mayor"]), "-jar", str(jar), "--install-server"],
                   cwd=servidor.ruta, check=True, timeout=900, creationflags=OCULTO)
