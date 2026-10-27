from pathlib import Path
import os


def leer(ruta):
    resultado = {}
    try:
        for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
            if linea.strip() and not linea.lstrip().startswith(("#", "!")) and "=" in linea:
                k, v = linea.split("=", 1)
                resultado[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return resultado


def escribir(ruta, cambios):
    ruta = Path(ruta)
    for k, v in cambios.items():
        if any(c in str(k) + str(v) for c in "\r\n"):
            raise ValueError("Las propiedades no admiten saltos de línea")
    lineas = ruta.read_text(encoding="utf-8").splitlines(keepends=True) if ruta.exists() else []
    pendientes = {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in cambios.items()}
    salida = []
    for linea in lineas:
        clave = linea.split("=", 1)[0].strip() if "=" in linea and not linea.lstrip().startswith(("#", "!")) else None
        if clave in pendientes:
            salida.append(clave + "=" + pendientes.pop(clave) + "\n")
        elif clave in cambios:
            continue
        else:
            salida.append(linea)
    if salida and not salida[-1].endswith(("\n", "\r")):
        salida[-1] += "\n"
    salida.extend(k + "=" + v + "\n" for k, v in pendientes.items())
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text("".join(salida), encoding="utf-8", newline="")
    os.replace(temporal, ruta)
