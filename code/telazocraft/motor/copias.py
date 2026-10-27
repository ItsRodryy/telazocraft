import datetime
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from .util import archivar, ruta_dentro


def verificar(ruta):
    with zipfile.ZipFile(ruta) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP dañado")
        nombres = z.namelist()
        if not any(PurePosixPath(n).name == "level.dat" for n in nombres):
            raise ValueError("El ZIP no contiene level.dat")
        for n in nombres:
            p = PurePosixPath(n.replace("\\", "/"))
            if p.is_absolute() or ".." in p.parts or ":" in n:
                raise ValueError("Ruta peligrosa en ZIP")
        return nombres


def crear(servidor, nivel="manual", con_diaria=True, en_sesion=False, progreso=lambda valor,texto: None):
    if nivel not in ("auto", "manual", "sesion", "diaria", "partida"):
        raise ValueError("Nivel de copia desconocido")
    if not en_sesion:
        servidor.exigir_parado()
    mundo = servidor.mundo
    if not (mundo / "level.dat").is_file():
        raise ValueError("No hay un mundo válido para copiar")
    carpeta = servidor.biblioteca.ruta("copias", servidor.id, "locales" if nivel in ("auto", "manual") else "partidas" if nivel == "partida" else "compartidas")
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos=[p for p in mundo.rglob('*') if p.is_file() and p.name!='session.lock']
    tamano = sum(p.stat().st_size for p in archivos)
    if shutil.disk_usage(carpeta).free < tamano * 2:
        raise OSError("Espacio libre insuficiente para una copia segura")
    fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    destino = carpeta / f"mundo_{servidor.id}_{nivel}_{fecha}.zip"
    temporal = destino.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        escritos=0
        for p in archivos:
            if p.is_symlink():
                raise ValueError("Enlace dentro del mundo")
            if p.is_file() and p.name != "session.lock":
                z.write(p, Path(mundo.name) / p.relative_to(mundo))
                escritos+=p.stat().st_size;progreso(int(90*escritos/max(1,tamano)),'Copiando mundo')
    progreso(92,'Verificando copia')
    verificar(temporal)
    os.replace(temporal, destino)
    rotar(servidor, carpeta, nivel)
    if con_diaria and nivel != "diaria":
        hoy = datetime.date.today().isoformat()
        compartidas = servidor.biblioteca.ruta("copias", servidor.id, "compartidas")
        existentes = list(compartidas.glob(f"*diaria*{hoy}*.zip"))
        if not existentes:
            crear(servidor, "diaria", False, en_sesion, lambda n,t:progreso(94+n*5//100,t))
    progreso(100,'Copia verificada')
    return destino


def rotar(servidor, carpeta, nivel):
    datos = servidor.datos.get("copias", {})
    if nivel in ("auto", "manual"):
        rutas = list(carpeta.glob("*.zip"))
        limite = datos.get("locales", 4)
    else:
        rutas = list(carpeta.glob(f"*_{nivel}_*.zip"))
        # Los ZIP anteriores al cambio de nombre siguen perteneciendo al mismo nivel.
        limite = datos.get("sesion" if nivel == "sesion" else "diarias", 3 if nivel == "sesion" else 5)
        if nivel == "partida":
            limite = (servidor.datos.get("hardcore") or {}).get("partidas_guardadas", 3)
    for ruta in sorted(rutas, key=lambda p: p.stat().st_mtime)[:-max(1, int(limite))]:
        archivar(ruta, servidor.biblioteca.ruta("archivo", "copias_rotadas", servidor.id))


def restaurar(servidor, copia):
    servidor.exigir_parado()
    verificar(copia)
    contenedor = servidor.ruta / ("restauracion_" + str(os.getpid()))
    contenedor.mkdir()
    try:
        with zipfile.ZipFile(copia) as z:
            for info in z.infolist():
                destino = ruta_dentro(contenedor, info.filename.replace("\\", "/"))
                if info.is_dir():
                    destino.mkdir(parents=True, exist_ok=True)
                else:
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as src, destino.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
        candidatos = list(contenedor.glob("*/level.dat"))
        if len(candidatos) != 1:
            raise ValueError("La copia debe contener un único mundo")
        if servidor.mundo.exists():
            archivar(servidor.mundo, servidor.biblioteca.ruta("archivo", "restaurados", servidor.id))
        os.replace(candidatos[0].parent, servidor.mundo)
    finally:
        if contenedor.exists():
            archivar(contenedor, servidor.biblioteca.ruta("archivo", "restauraciones", servidor.id))
