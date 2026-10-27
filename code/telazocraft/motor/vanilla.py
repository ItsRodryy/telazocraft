from .util import http_json, descargar

MANIFIESTO = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def versiones():
    return http_json(MANIFIESTO)["versions"]


def metadatos(version):
    v = next((v for v in versiones() if v["id"] == version), None)
    if v is None:
        raise ValueError("Versión de Minecraft inexistente")
    return http_json(v["url"])


def instalar(servidor, progreso=lambda n,total:None):
    d = metadatos(servidor.datos["version_mc"])
    f = d["downloads"]["server"]
    descargar(f["url"], servidor.ruta / "server.jar", f["sha1"], "sha1",progreso=progreso)
    servidor.datos["java_mayor"] = d["javaVersion"]["majorVersion"]
    servidor.guardar()
