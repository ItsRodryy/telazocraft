import hashlib
import re
import uuid
import urllib.parse
from .util import http_json, guardar_json, leer_json
from . import copias, propiedades


def offline(nick):
    return str(uuid.UUID(bytes=hashlib.md5(("OfflinePlayer:" + nick).encode("utf-8")).digest(), version=3))


def perfil(nick):
    if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", nick):
        raise ValueError("Nombre de jugador no válido")
    d = http_json("https://api.mojang.com/users/profiles/minecraft/" + urllib.parse.quote(nick))
    if not d or "id" not in d:
        raise ValueError("No existe un perfil premium para " + nick)
    return {"name": d["name"], "uuid": str(uuid.UUID(d["id"]))}


def migrar(servidor, acceso, resolver=perfil):
    servidor.exigir_parado()
    if acceso not in ("abierto", "premium"):
        raise ValueError("Acceso desconocido")
    if acceso == servidor.datos["acceso"]:
        return []
    archivos = ("whitelist.json", "ops.json", "usercache.json", "banned-players.json")
    listas = {n: leer_json(servidor.ruta / n, []) for n in archivos}
    conocidos = {d["name"]: d["uuid"] for rows in listas.values() for d in rows if "name" in d and "uuid" in d}
    mapa, avisos = {}, []
    for nick, anterior in conocidos.items():
        try:
            nuevo = resolver(nick)["uuid"] if acceso == "premium" else offline(nick)
            mapa[anterior] = nuevo
        except (ValueError, OSError) as exc:
            avisos.append(f"{nick}: {exc}")
    if avisos:
        raise ValueError("No se aplicó ningún cambio. " + "; ".join(avisos))
    movimientos = []
    for carpeta in ("playerdata", "advancements", "stats"):
        for p in (servidor.mundo / carpeta).glob("*"):
            for viejo, nuevo in mapa.items():
                if viejo != nuevo and p.name.startswith(viejo + "."):
                    destino = p.with_name(nuevo + p.name[len(viejo):])
                    if destino.exists():
                        raise ValueError("Ya existe el destino de un personaje; migración cancelada")
                    movimientos.append((p, destino))
    copias.crear(servidor, "manual")
    for origen, destino in movimientos:
        origen.rename(destino)
    for n, rows in listas.items():
        for d in rows:
            if d.get("uuid") in mapa:
                d["uuid"] = mapa[d["uuid"]]
        guardar_json(servidor.ruta / n, rows)
    for carpeta in (servidor.mundo / "data", servidor.mundo / "serverconfig"):
        for p in carpeta.rglob("*"):
            if p.is_file():
                contenido = p.read_bytes()
                if any(v.encode() in contenido or uuid.UUID(v).bytes in contenido for v in mapa):
                    avisos.append("Revisar datos de mods: " + str(p.relative_to(servidor.ruta)))
    propiedades.escribir(servidor.ruta / "server.properties", {"online-mode": acceso == "premium"})
    servidor.datos["acceso"] = acceso
    servidor.guardar()
    return avisos
