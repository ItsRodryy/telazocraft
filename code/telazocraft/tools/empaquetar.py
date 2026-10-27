"""CPython autocontenido, dependencias dinámicas, código compilado e Inno Setup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from .. import __version__
from ..motor.util import descargar, huella, guardar_json, archivar

PUBLICACION = "20261001"
PYTHON = "3.12.15"
BASE = f"https://github.com/astral-sh/python-build-standalone/releases/download/{PUBLICACION}/"
ARCHIVO = f"cpython-{PYTHON}+{PUBLICACION}-x86_64-pc-windows-msvc-install_only.tar.gz"


def compilar(raiz, paquete, python, version):
    script = """import os,sys,py_compile
from pathlib import Path
src=Path(sys.argv[1]);dst=Path(sys.argv[2])
for p in src.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:
  rel=p.relative_to(src);out=dst/rel;out.parent.mkdir(parents=True,exist_ok=True)
  if p.suffix=='.py':
   if rel.as_posix()=='telazocraft/__init__.py':
    import tempfile,re
    with tempfile.TemporaryDirectory(prefix='telazocraft_version_') as td:
     tmp=Path(td)/'__init__.py';tmp.write_text(re.sub(r'__version__ = ".*?"','__version__ = "'+sys.argv[3]+'"',p.read_text(encoding='utf-8')),encoding='utf-8')
     py_compile.compile(str(tmp),cfile=str(out.with_suffix('.pyc')),dfile=rel.as_posix(),doraise=True)
   else:py_compile.compile(str(p),cfile=str(out.with_suffix('.pyc')),dfile=rel.as_posix(),doraise=True)
  else:
   import shutil;shutil.copy2(p,out)
"""
    subprocess.run([str(python), "-B", "-c", script, str(raiz / "code"), str(paquete / "code"), version], check=True)


def fabricar(raiz, salida, iscc, repositorio="", version=__version__):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Versión de instalador inválida")
    raiz, salida = Path(raiz).resolve(), Path(salida).resolve()
    if not (raiz / "pyproject.toml").is_file() or not (raiz / "code/telazocraft/__init__.py").is_file():
        raise ValueError("La raíz no es el proyecto Telazocraft")
    cache = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "Telazocraft" / "cache_build"
    cache.mkdir(parents=True, exist_ok=True)
    print("Python autocontenido: verificando descarga", flush=True)
    with urllib.request.urlopen(BASE + "SHA256SUMS", timeout=60) as r:
        sumas = r.read().decode("utf-8")
    esperado = next((l.split()[0] for l in sumas.splitlines() if l.split()[-1].lstrip("*") == ARCHIVO), None)
    if not esperado:
        raise ValueError("No se encontró el SHA-256 oficial de Python")
    tar = cache / ARCHIVO
    if not tar.exists() or huella(tar) != esperado:
        descargar(BASE + ARCHIVO, tar, esperado)
    paquete = raiz / "build" / "Telazocraft"
    if paquete.exists():
        archivo = (raiz / "archivo" / "compilaciones").resolve()
        if not paquete.resolve().is_relative_to(raiz) or not archivo.is_relative_to(raiz):
            raise ValueError("Ruta de compilación fuera del proyecto")
        archivar(paquete, archivo)
    paquete.mkdir(parents=True)
    with tarfile.open(tar) as t:
        for m in t.getmembers():
            destino = (paquete / m.name).resolve()
            if not destino.is_relative_to(paquete.resolve()) or m.issym() or m.islnk():
                raise ValueError("Ruta inesperada en el archivo de Python")
        t.extractall(paquete, filter="data")
    python = paquete / "python" / "python.exe"
    print("Instalando dependencias del paquete", flush=True)
    subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(raiz / "requirements.txt")], check=True)
    site = paquete / "python/Lib/site-packages"
    (site / "telazocraft.pth").write_text("../../../code\n", encoding="utf-8")
    print("Compilando código y copiando licencias", flush=True)
    compilar(raiz, paquete, python, version)
    guardar_json(paquete / "code/telazocraft/recursos/release.json", {"repositorio": repositorio, "version": version})
    for nombre in ("LICENSE", "THIRD_PARTY_NOTICES", "README.md"):
        shutil.copy2(raiz / nombre, paquete / nombre)
    # Se conservan los metadatos y textos de licencia originales instalados por pip y CPython.
    script = "from telazocraft.app.qt_app import crear_app;from telazocraft.app.icons import logo_pixmap;from telazocraft.app.marca import guardar_icono, imagenes_instalador;import sys;app=crear_app();guardar_icono(sys.argv[1]);imagenes_instalador(sys.argv[1])"
    subprocess.run([str(python), "-B", "-c", script, str(paquete / "Telazocraft.ico")], check=True,
                   env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
    compiladores=list((Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework64').glob('v4*/csc.exe'))
    if not compiladores:raise FileNotFoundError('Falta el compilador .NET Framework de Windows')
    subprocess.run([str(compiladores[-1]),'/nologo','/target:winexe','/optimize+',
                    '/reference:System.Windows.Forms.dll','/win32icon:'+str(paquete/'Telazocraft.ico'),
                    '/out:'+str(paquete/'Telazocraft.exe'),str(raiz/'tools/launcher.cs')],check=True)
    with tempfile.TemporaryDirectory(prefix="telazocraft_smoke_build_") as temporal:
        (Path(temporal) / "telazocraft.json").write_text('{"schema":1}', encoding="utf-8")
        subprocess.run([str(python), "-B", "-m", "telazocraft", "--biblioteca", temporal, "--smoke"], check=True,
                       env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}, timeout=30)
        subprocess.run([str(paquete/'Telazocraft.exe'),'--biblioteca',temporal,'--smoke'],check=True,
                       env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},timeout=30)
    salida.mkdir(parents=True, exist_ok=True)
    exe = salida / f"Telazocraft-{version}-windows.exe"
    if exe.exists():
        archivar(exe, raiz / "archivo" / "instaladores")
    print("Fabricando instalador", flush=True)
    subprocess.run([str(iscc), "/Qp", "/DPaquete=" + str(paquete), "/DSalida=" + str(salida), "/DVersion=" + version,
                    str(raiz / "installer/telazocraft.iss")], check=True)
    if not exe.is_file():
        raise FileNotFoundError("El compilador no produjo el instalador")
    (salida / "SHA256SUMS").write_text(huella(exe) + "  " + exe.name + "\n", encoding="utf-8")
    print("Instalador verificado: " + str(exe), flush=True)
    return exe


def main():
    from ..common.tls import activar
    activar()
    p = argparse.ArgumentParser()
    p.add_argument("--raiz", default=str(Path(__file__).resolve().parents[3]))
    p.add_argument("--salida")
    p.add_argument("--iscc", default=shutil.which("ISCC.exe"))
    p.add_argument("--repositorio", default=os.environ.get("GITHUB_REPOSITORY", ""))
    p.add_argument("--version", default=__version__)
    args = p.parse_args()
    if not args.iscc:
        p.error("Instala Inno Setup 6.7 o pasa --iscc con la ruta de ISCC.exe")
    fabricar(args.raiz, args.salida or str(Path(args.raiz) / "dist"), args.iscc, args.repositorio, args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
