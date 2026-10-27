import hashlib
import json
import os
import urllib.parse
import zipfile
from functools import lru_cache
from .util import http_json, guardar_json, leer_json, huella, descargar, archivar

API = "https://api.modrinth.com/v2"

@lru_cache(maxsize=512)
def _huella_jar(ruta,tamano,modificado):
    return huella(ruta,'sha1')


def buscar(texto, servidor):
    facets = [["versions:" + servidor.datos["version_mc"]], ["categories:" + servidor.datos["tipo"]]]
    return http_json(API + "/search?" + urllib.parse.urlencode({"query": texto, "facets": json.dumps(facets), "limit": 30}))["hits"]


def versiones(proyecto, servidor):
    q = urllib.parse.urlencode({"loaders": json.dumps([servidor.datos["tipo"]]), "game_versions": json.dumps([servidor.datos["version_mc"]])})
    return http_json(API + "/project/" + urllib.parse.quote(proyecto, safe="") + "/version?" + q)


def inventario(servidor, red=True, cache_path=None):
    cache = leer_json(servidor.ruta / "mods.json", {"versiones": {}, "proyectos": {}})
    if cache_path and cache_path.exists():
        cache = leer_json(cache_path, cache)
    jars = sorted((servidor.ruta / "mods").glob("*.jar"))
    hashes = {p.name: _huella_jar(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in jars}
    if red and hashes:
        versiones_remotas = http_json(API + "/version_files", {"hashes": list(hashes.values()), "algorithm": "sha1"})
        ids = sorted({v["project_id"] for v in versiones_remotas.values()})
        proyectos = http_json(API + "/projects?" + urllib.parse.urlencode({"ids": json.dumps(ids)})) if ids else []
        cache = {"versiones": versiones_remotas, "proyectos": {p["id"]: p for p in proyectos}}
        guardar_json(cache_path or servidor.ruta / "mods.json", cache)
    resultado = []
    for p in jars:
        v = cache["versiones"].get(hashes[p.name], {})
        proyecto = cache["proyectos"].get(v.get("project_id"), {})
        resultado.append({"archivo": p.name, "nombre": proyecto.get("title", p.stem), "version": v.get("version_number", ""),
                          "lado": proyecto.get("client_side", "unknown"), "origen": "Modrinth" if v else "manual",
                          "sha1": hashes[p.name], "proyecto": proyecto.get("id"), "version_id": v.get("id"),
                          "icon_url": proyecto.get("icon_url"), "server_side": proyecto.get("server_side", "unknown")})
    return resultado


def instalar(servidor, version_id, vistos=None, progreso=lambda n,texto:None):
    servidor.exigir_parado()
    vistos = set() if vistos is None else vistos
    if version_id in vistos:
        return []
    vistos.add(version_id)
    v = http_json(API + "/version/" + urllib.parse.quote(version_id, safe=""))
    if servidor.datos["version_mc"] not in v["game_versions"] or servidor.datos["tipo"] not in v["loaders"]:
        raise ValueError("Mod incompatible con este servidor")
    instalados = []
    for dep in v.get("dependencies", []):
        if dep["dependency_type"] == "required":
            id = dep.get("version_id")
            if not id:
                opciones = versiones(dep["project_id"], servidor)
                if not opciones:
                    raise ValueError("Falta una dependencia compatible")
                id = opciones[0]["id"]
            instalados += instalar(servidor, id, vistos,progreso)
    archivo = next((f for f in v["files"] if f.get("primary")), v["files"][0])
    nombre = archivo["filename"]
    if not nombre.endswith(".jar") or "/" in nombre or "\\" in nombre:
        raise ValueError("Nombre de mod inválido")
    destino = servidor.ruta / "mods" / nombre
    if destino.exists() and huella(destino, "sha512") == archivo["hashes"]["sha512"]:
        return instalados
    # Verificar la descarga antes de retirar la versión que ya funciona.
    temporal = servidor.ruta / "mods_retirados" / "descargas" / nombre
    descargar(archivo["url"], temporal, archivo["hashes"]["sha512"], "sha512",
              progreso=lambda n,total:progreso(int(100*n/total) if total else 0,'Descargando '+nombre))
    for viejo in inventario(servidor, red=True):
        if viejo["proyecto"] == v["project_id"]:
            retirar(servidor, viejo["archivo"])
    destino.parent.mkdir(exist_ok=True)
    os.replace(temporal, destino)
    return instalados + [nombre]


def retirar(servidor, nombre):
    servidor.exigir_parado()
    if "/" in nombre or "\\" in nombre or not nombre.endswith(".jar"):
        raise ValueError("Nombre de mod inválido")
    return archivar(servidor.ruta / "mods" / nombre, servidor.ruta / "mods_retirados")


def agregar_jar(servidor, origen):
    from pathlib import Path
    import shutil
    servidor.exigir_parado()
    origen = Path(origen)
    if origen.suffix != ".jar" or not zipfile.is_zipfile(origen):
        raise ValueError("El archivo no es un JAR válido")
    destino = servidor.ruta / "mods" / origen.name
    if destino.exists():
        raise FileExistsError("Ya existe ese mod")
    destino.parent.mkdir(exist_ok=True)
    shutil.copy2(origen, destino)
    return destino


def actualizaciones(servidor):
    resultado = []
    for mod in inventario(servidor):
        if mod["proyecto"]:
            opciones = versiones(mod["proyecto"], servidor)
            if opciones and opciones[0]["id"] != mod["version_id"]:
                resultado.append({**mod, "nueva": opciones[0]})
    return resultado
