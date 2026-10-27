"""Lecturas de biblioteca para trabajadores; este módulo no crea widgets."""
import time
from ..motor import jugadores,modrinth
from ..motor.diario import Diario
from ..motor.historial import importar

def leer(servidor, cache_mods, anterior=None, importar_logs=False):
    if importar_logs:importar(servidor)
    registros=Diario(servidor).leer()
    carpeta=servidor.biblioteca.ruta('copias',servidor.id)
    rutas=sorted(carpeta.glob('*/*.zip'),key=lambda p:p.stat().st_mtime,reverse=True)
    firma=tuple((p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in sorted((servidor.ruta/'mods').glob('*.jar')))
    ahora=time.monotonic();anterior=anterior or {}
    tamano=anterior.get('tamano',0);medido=anterior.get('medido',0)
    if not medido or ahora-medido>300:
        tamano=sum(p.stat().st_size for p in servidor.ruta.rglob('*') if p.is_file() and not p.is_symlink());medido=ahora
    mods=anterior.get('mods',[]) if firma==anterior.get('firma_mods') else modrinth.inventario(servidor,False,cache_mods)
    return {'diario':registros,'jugadores':jugadores.conocidos(servidor,registros=registros),'copias':rutas,
            'mods':mods,'firma_mods':firma,'tamano':tamano,'medido':medido}
