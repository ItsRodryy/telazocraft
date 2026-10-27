"""Importa sesiones verificables de logs sin escribir en mundos ni identidades."""
import datetime as dt
import gzip
import hashlib
import json
import re
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .diario import Diario

MESES = {n: i + 1 for i, n in enumerate(("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"))}
MESES.update(dict(jan=1, apr=4, aug=8, dec=12))
FECHA = re.compile(r"^\[(\d{2})([A-Za-z]{3})(\d{4}) (\d{2}:\d{2}:\d{2})(?:\.\d+)?\]")
HORA = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]")
JUGADOR = re.compile(r"(?:\]: |: )([A-Za-z0-9_]{1,16}) (joined|left) the game\s*$")


@lru_cache(maxsize=1)
def zona_local():
    try:
        return ZoneInfo("Europe/Madrid")
    except ZoneInfoNotFoundError:
        # Windows sin tzdata: las reglas del SO para la fecha histórica.
        return None


def importar(servidor):
    diario = Diario(servidor)
    anteriores = diario.leer()
    ids = {r.get("import_id") for r in anteriores}
    entradas_vivas = {(r.get("jugador", "").casefold(), r.get("fecha", "")[:19])
                      for r in anteriores if r.get("tipo") == "entrada" and r.get("origen") != "logs"}
    nuevos = []
    carpeta = servidor.ruta / "logs"
    rutas = sorted(set(carpeta.glob("*.log")) | set(carpeta.glob("*.log.gz")))
    for ruta in rutas:
        fecha_archivo = re.search(r"\d{4}-\d{2}-\d{2}", ruta.name)
        dia = dt.date.fromisoformat(fecha_archivo[0]) if fecha_archivo else dt.datetime.fromtimestamp(ruta.stat().st_mtime).date()
        abiertos = {}
        ultimo = None
        primero = None
        parada = None
        def cerrar(nick, fin):
            inicio, nombre = abiertos.pop(nick)
            if fin < inicio:
                return
            llave = hashlib.sha256(f"{nombre.casefold()}|{inicio.isoformat()}|{fin.isoformat()}".encode()).hexdigest()
            if llave in ids or (nick, inicio.astimezone(dt.timezone.utc).isoformat()[:19]) in entradas_vivas:
                return
            ids.add(llave)
            base = {"jugador": nombre, "origen": "logs", "import_id": llave}
            nuevos.extend(({**base, "tipo": "entrada", "fecha": inicio.astimezone(dt.timezone.utc).isoformat()},
                           {**base, "tipo": "salida", "fecha": fin.astimezone(dt.timezone.utc).isoformat(),
                            "duracion_seg": (fin - inicio).total_seconds()}))
        abrir = gzip.open if ruta.suffix == ".gz" else open
        try:
            with abrir(ruta, "rt", encoding="utf-8", errors="replace") as f:
                for linea in f:
                    m = FECHA.match(linea)
                    h = HORA.match(linea)
                    if m and m[2].lower() in MESES:
                        momento = dt.datetime(int(m[3]), MESES[m[2].lower()], int(m[1]), *map(int, m[4].split(":")))
                    elif h:
                        momento = dt.datetime.combine(dia, dt.time.fromisoformat(h[1]))
                        if ultimo and momento.replace(tzinfo=ultimo.tzinfo) < ultimo - dt.timedelta(hours=12):
                            dia += dt.timedelta(days=1)
                            momento += dt.timedelta(days=1)
                    else:
                        continue
                    momento = momento.replace(tzinfo=zona_local())
                    if momento.tzinfo is None:
                        momento = momento.astimezone()
                    ultimo = momento
                    if primero is None:primero=momento
                    evento = JUGADOR.search(linea)
                    if evento:
                        nombre, tipo = evento.groups(); nick = nombre.casefold()
                        if tipo == "joined":
                            if nick in abiertos:
                                cerrar(nick, momento)
                            abiertos[nick] = (momento, nombre)
                        elif nick in abiertos:
                            cerrar(nick, momento)
                    if "Stopping server" in linea or "All dimensions are saved" in linea:
                        if parada is None:parada=momento
                        for nick in list(abiertos):
                            cerrar(nick, momento)
            if ultimo and ruta.name!='latest.log':
                for nick in list(abiertos):
                    cerrar(nick, ultimo)
            fin=parada or (ultimo if ruta.name!='latest.log' else None)
            if primero and fin and fin>=primero:
                llave='encendido:'+hashlib.sha256(f'{primero.isoformat()}|{fin.isoformat()}'.encode()).hexdigest()
                if llave not in ids:
                    ids.add(llave);nuevos.append({'tipo':'encendido_log','fecha':fin.astimezone(dt.timezone.utc).isoformat(),'duracion_seg':(fin-primero).total_seconds(),'origen':'logs','import_id':llave})
        except (OSError, EOFError):
            continue
    if nuevos:
        nuevos.sort(key=lambda r: (r["fecha"], r["tipo"]))
        with diario.ruta.open("a", encoding="utf-8") as f:
            for r in nuevos:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return sum(r['tipo']=='salida' for r in nuevos)
