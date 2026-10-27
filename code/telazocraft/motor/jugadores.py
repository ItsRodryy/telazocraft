import base64
import datetime
import json
import re
import urllib.parse
import urllib.request
from . import mojang, propiedades
from .diario import Diario
from .tiempos import sesiones_jugadores
from .util import leer_json, guardar_json, http_json


def conocidos(servidor, conectados=(), entradas=None, ahora=None, registros=None):
    datos = {}
    registros=Diario(servidor).leer() if registros is None else registros
    horas,_=sesiones_jugadores(registros,conectados,entradas,ahora)
    for archivo in ("whitelist.json", "ops.json", "usercache.json", "banned-players.json"):
        for d in leer_json(servidor.ruta / archivo, []):
            if "name" in d and "uuid" in d:
                clave = d["name"].casefold()
                datos.setdefault(clave, {"nick": d["name"], "uuid": d["uuid"], "horas": 0, "ultima": ""})
                datos[clave][archivo] = True
                datos[clave].setdefault("uuids", set()).add(d["uuid"])
    for d in registros:
        nick = d.get("jugador")
        if nick:
            row = datos.setdefault(nick.casefold(), {"nick": nick, "uuid": "", "horas": 0, "ultima": ""})
            row["ultima"] = max(row["ultima"], d.get("fecha", ""))
    for nick in conectados:
        datos.setdefault(nick.casefold(), {"nick": nick, "uuid": "", "horas": 0, "ultima": ""})
    for row in datos.values():
        row.pop('uuids',None)
        row['horas']=horas.get(row['nick'].casefold(),0)
        row["conectado"] = row["nick"].casefold() in {n.casefold() for n in conectados}
    # usercache también contiene consultas de skins de mods/NPC; no son jugadores conocidos.
    visibles = [d for d in datos.values() if d['conectado'] or d['ultima'] or d['horas'] or
                any(d.get(k) for k in ('whitelist.json','ops.json','banned-players.json'))]
    return sorted(visibles, key=lambda d: (not d["conectado"], d["nick"].casefold()))


def modificar_lista(servidor, nick, lista, agregar=True):
    servidor.exigir_parado()
    if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", nick):
        raise ValueError("Nombre de jugador no válido")
    if lista not in ("whitelist", "ops", "banned-players"):
        raise ValueError("Lista no válida")
    ruta = servidor.ruta / (lista + ".json")
    rows = leer_json(ruta, [])
    rows = [d for d in rows if d.get("name", "").casefold() != nick.casefold()]
    if agregar:
        uuid = mojang.perfil(nick)["uuid"] if servidor.datos["acceso"] == "premium" else mojang.offline(nick)
        row = {"name": nick, "uuid": uuid}
        if lista == "ops":
            row.update({"level": 4, "bypassesPlayerLimit": False})
        elif lista == "banned-players":
            row.update({"created": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z"),
                        "source": "Telazocraft", "expires": "forever", "reason": "Bloqueado por el administrador"})
        rows.append(row)
    guardar_json(ruta, rows)


def textura(nick):
    perfil = mojang.perfil(nick)
    d = http_json("https://sessionserver.mojang.com/session/minecraft/profile/" + perfil["uuid"].replace("-", ""))
    prop = next(p["value"] for p in d["properties"] if p["name"] == "textures")
    url = json.loads(base64.b64decode(prop))["textures"]["SKIN"]["url"]
    p = urllib.parse.urlsplit(url)
    if p.hostname != "textures.minecraft.net" or not re.fullmatch(r"/texture/[a-fA-F0-9]{64}", p.path):
        raise ValueError("Servidor de texturas no permitido")
    with urllib.request.urlopen("https://textures.minecraft.net" + p.path, timeout=15) as r:
        datos = r.read(4 * 1024 * 1024 + 1)
    if len(datos) > 4 * 1024 * 1024 or not datos.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Textura no válida")
    return datos
