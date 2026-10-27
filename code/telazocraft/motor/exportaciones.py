import datetime
import zipfile
from . import modrinth
from .util import descargar, archivar


def crear(servidor):
    mods = modrinth.inventario(servidor, red=True)
    carpeta = servidor.biblioteca.ruta("exportaciones", servidor.id)
    carpeta.mkdir(parents=True, exist_ok=True)
    extras = []
    for slug in servidor.datos.get("extras_cliente", []):
        opciones = modrinth.versiones(slug, servidor)
        if not opciones:
            raise ValueError("No hay una versión compatible de " + slug)
        f = next((f for f in opciones[0]["files"] if f.get("primary")), opciones[0]["files"][0])
        ruta = carpeta / "extras" / f["filename"]
        descargar(f["url"], ruta, f["hashes"]["sha512"], "sha512")
        extras.append(ruta)
    archivos = [servidor.ruta / "mods" / m["archivo"] for m in mods if m["lado"] != "unsupported"] + extras
    nombres = [p.name for p in archivos]
    if len(nombres) != len(set(nombres)):
        raise ValueError("Hay mods duplicados en el ZIP")
    sello = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destino = carpeta / f"mods_cliente_{servidor.id}_{sello}.zip"
    temporal = destino.with_suffix(".zip.tmp")
    d = servidor.datos
    leeme = (f"Instala NeoForge {d['version_loader']} para Minecraft {d['version_mc']} en el launcher oficial "
             "o TLauncher. Extrae los JAR de este ZIP en .minecraft/mods. No los instales en el servidor.\n")
    with zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for p in archivos:
            z.write(p, p.name)
        z.writestr("LEEME.txt", leeme.encode("utf-8"))
    with zipfile.ZipFile(temporal) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP dañado")
    temporal.replace(destino)
    for viejo in sorted(carpeta.glob("mods_cliente_*.zip"), key=lambda p: p.stat().st_mtime)[:-3]:
        archivar(viejo, servidor.biblioteca.ruta("archivo", "exportaciones", servidor.id))
    return destino, {"servidor": len(archivos) - len(extras), "extras": len(extras), "excluidos": sum(m["lado"] == "unsupported" for m in mods)}
