import glob
import re
import shutil
import subprocess
from pathlib import Path

OCULTO = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def version(ruta):
    try:
        r = subprocess.run([str(ruta), "-version"], capture_output=True, text=True, timeout=10, creationflags=OCULTO)
        m = re.search(r'version "(\d+)', r.stdout + r.stderr)
        return int(m[1]) if m and r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def detectar():
    candidatos = []
    for base in ("C:/Program Files/Microsoft", "C:/Program Files/Eclipse Adoptium", "C:/Program Files/Java"):
        candidatos.extend(glob.glob(base + "/*/bin/java.exe"))
    if shutil.which("java"):
        candidatos.append(shutil.which("java"))
    return [{"ruta": str(p), "mayor": n} for p in dict.fromkeys(candidatos) if (n := version(p))]


def buscar(mayor):
    for d in detectar():
        if d["mayor"] == int(mayor):
            return d["ruta"]
    raise RuntimeError(f"Falta Java {mayor}; instálalo desde el asistente")


def instalar(mayor):
    subprocess.run(["winget", "install", "--id", f"Microsoft.OpenJDK.{int(mayor)}", "--exact",
                    "--accept-package-agreements", "--accept-source-agreements", "--silent"], check=True, creationflags=OCULTO)
    return buscar(mayor)
