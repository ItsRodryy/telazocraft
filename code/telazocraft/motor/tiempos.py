"""Intervalos unidos para no contar dos veces el diario y los logs importados."""
import datetime as dt
import time
from .diario import Diario

def marca(valor):
    try:return dt.datetime.fromisoformat(valor).timestamp()
    except (ValueError,TypeError):return None

def segundos(intervalos):
    total=0;fin_previo=float('-inf')
    for inicio,fin in sorted(intervalos):
        if fin<inicio:continue
        total+=max(0,fin-max(inicio,fin_previo));fin_previo=max(fin_previo,fin)
    return total

def sesiones_jugadores(registros, conectados=(), entradas=None, ahora=None):
    ahora=time.time() if ahora is None else ahora
    entradas=entradas or {};intervalos={};abiertas={};nombres={}
    for r in sorted(registros,key=lambda x:x.get('fecha','')):
        nick=r.get('jugador','');key=nick.casefold();fin=marca(r.get('fecha'))
        if not key or fin is None:continue
        nombres[key]=nick
        if r.get('tipo')=='entrada':abiertas[key]=fin
        elif r.get('tipo')=='salida':
            inicio=fin-r.get('duracion_seg',max(0,fin-abiertas.get(key,fin)))
            intervalos.setdefault(key,[]).append((inicio,fin));abiertas.pop(key,None)
    vivas=[]
    for nick in conectados:
        key=nick.casefold();inicio=entradas.get(nick,abiertas.get(key,ahora))
        intervalos.setdefault(key,[]).append((inicio,ahora))
        vivas.append({'jugador':nick,'fecha':dt.datetime.fromtimestamp(inicio,dt.timezone.utc).isoformat(),'duracion_seg':max(0,ahora-inicio),'en_curso':True})
    return {key:segundos(valores)/3600 for key,valores in intervalos.items()},vivas

def horas_encendido(registros, activo=False, ahora=None):
    ahora=time.time() if ahora is None else ahora
    intervalos=[];inicio=None
    for r in sorted(registros,key=lambda x:x.get('fecha','')):
        fin=marca(r.get('fecha'))
        if fin is None:continue
        tipo=r.get('tipo')
        if tipo=='encendido_log':intervalos.append((fin-r['duracion_seg'],fin))
        elif tipo=='arranque':
            if inicio is None:inicio=fin
        elif tipo=='parada' and inicio is not None:
            intervalos.append((inicio,fin));inicio=None
    if activo and inicio is not None:intervalos.append((inicio,ahora))
    return segundos(intervalos)/3600
