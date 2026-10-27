from .common.tls import activar
activar()

import argparse
import queue
import sys
import threading
from .common import ajustes
from .motor.biblioteca import Biblioteca


def consola(biblioteca, id):
    from .motor.controlador import Controlador
    salida = queue.Queue()
    control = Controlador(biblioteca.servidor(id), lambda tipo, datos: salida.put((tipo, datos)))
    control.iniciar()

    def entrada():
        for linea in sys.stdin:
            texto = linea.strip()
            if texto:
                try:
                    control.comando(texto)
                except Exception as e:
                    salida.put(("error", str(e)))
    threading.Thread(target=entrada, daemon=True).start()
    try:
        while control.hilo.is_alive() or not salida.empty():
            try:
                tipo, datos = salida.get(timeout=0.25)
                print(datos if tipo == "log" else f"[{tipo}] {datos}", flush=True)
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print("Guardando y creando copia de sesión...", flush=True)
        control.parar(esperar=True)
    return 1 if control.estado == "error" else 0


def main():
    p = argparse.ArgumentParser(prog="telazocraft")
    p.add_argument("--biblioteca")
    p.add_argument("--consola", metavar="ID")
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    ruta = args.biblioteca or ajustes.cargar().get("biblioteca")
    if args.consola:
        if not ruta:
            p.error("Elige una biblioteca con --biblioteca")
        return consola(Biblioteca(ruta), args.consola)
    from .app.principal import ejecutar
    return ejecutar(ruta, smoke=args.smoke)


if __name__ == "__main__":
    sys.exit(main())
