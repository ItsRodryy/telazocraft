import copy
import shutil
import time
from .biblioteca import Biblioteca
from .servidor import Servidor
from .util import identificador, guardar_json, leer_json
from . import java, neoforge, vanilla, modrinth, propiedades
from .hardcore import Hardcore


def crear(biblioteca, id, nombre, tipo, version_mc, version_loader="", plantilla=None, hardcore=False,
          acceso="abierto", whitelist_de=None, mods=(), semilla="", instalar_java=False, progreso=lambda s: None):
    identificador(id)
    if biblioteca.lock.exists():
        raise RuntimeError("Detén el servidor antes de crear otro")
    destino = biblioteca.ruta("servidores", id)
    if destino.exists():
        raise FileExistsError("Ya existe ese servidor")
    if tipo not in ("neoforge", "vanilla") or acceso not in ("abierto", "premium"):
        raise ValueError("Tipo o acceso no válido")
    if plantilla:
        origen_plantilla = biblioteca.servidor(plantilla)
        tipo, version_mc = origen_plantilla.datos["tipo"], origen_plantilla.datos["version_mc"]
        version_loader = origen_plantilla.datos.get("version_loader", "")
    meta = vanilla.metadatos(version_mc)
    mayor = meta["javaVersion"]["majorVersion"]
    try:
        java.buscar(mayor)
    except RuntimeError:
        if not instalar_java:
            raise
        progreso(f"Instalando Java {mayor}")
        java.instalar(mayor)
    temporal = biblioteca.ruta("archivo", "preparacion_servidores", id + "_" + str(time.time_ns()))
    temporal.mkdir(parents=True)
    if plantilla:
        plantilla = biblioteca.servidor(plantilla)
        tipo, version_mc = plantilla.datos["tipo"], plantilla.datos["version_mc"]
        version_loader, mayor = plantilla.datos.get("version_loader", ""), plantilla.datos["java_mayor"]
        for n in ("mods", "config", "defaultconfigs", "libraries", "user_jvm_args.txt"):
            origen = plantilla.ruta / n
            if origen.is_dir():
                shutil.copytree(origen, temporal / n)
            elif origen.is_file():
                shutil.copy2(origen, temporal / n)
    datos = {"schema": 1, "nombre": nombre.strip() or id, "tipo": tipo, "version_mc": version_mc,
             "version_loader": version_loader, "java_mayor": mayor, "ram_mb": 4096, "acceso": acceso,
             "reinicio_h": 2, "apagar_si_vacio_min": 10, "copias": {"locales": 4, "sesion": 3, "diarias": 5},
             "extras_cliente": ["xaeros-minimap", "xaeros-world-map"],
             "hardcore": {"gracia_seg": 30, "partidas_guardadas": 3, "freno_reinicios": 0} if hardcore else None}
    guardar_json(temporal / "servidor.json", datos)
    servidor = object.__new__(Servidor)
    servidor.biblioteca, servidor.id, servidor.ruta, servidor.datos = biblioteca, id, temporal, datos
    (temporal / "mods").mkdir(exist_ok=True)
    (temporal / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    propiedades.escribir(temporal / "server.properties", {"level-name": "world", "level-seed": semilla, "hardcore": hardcore,
                          "online-mode": acceso == "premium", "white-list": bool(whitelist_de), "server-port": 25565,
                          "motd": datos["nombre"], "difficulty": "hard" if hardcore else "normal", "max-players": 20})
    if whitelist_de:
        origen = biblioteca.servidor(whitelist_de)
        guardar_json(temporal / "whitelist.json", leer_json(origen.ruta / "whitelist.json", []))
    guardar_json(temporal / "ops.json", [])
    if not plantilla:
        progreso("Instalando " + tipo)
        if tipo == "vanilla":
            vanilla.instalar(servidor)
        else:
            neoforge.instalar(servidor)
    elif tipo == "vanilla":
        vanilla.instalar(servidor)
    if not (temporal / "user_jvm_args.txt").exists():
        (temporal / "user_jvm_args.txt").write_text("-Xms1024M\n-Xmx4096M\n", encoding="utf-8")
    for slug in mods:
        progreso("Instalando mod: " + slug)
        opciones = modrinth.versiones(slug, servidor)
        if not opciones:
            raise ValueError("No hay una versión compatible de " + slug)
        modrinth.instalar(servidor, opciones[0]["id"])
    if hardcore:
        progreso("Preparando partida hardcore")
        Hardcore(servidor, lambda c: None).nueva_partida()
    temporal.rename(destino)
    return biblioteca.servidor(id)


def compatibilidad(servidor, versiones_mc):
    mods = [m for m in modrinth.inventario(servidor) if m["proyecto"]]
    resultado = []
    for version in versiones_mc:
        simulacion = object.__new__(Servidor)
        simulacion.datos = {**servidor.datos, "version_mc": version}
        resultado.append({"version": version, "compatibles": sum(bool(modrinth.versiones(m["proyecto"], simulacion)) for m in mods), "total": len(mods)})
    return resultado
