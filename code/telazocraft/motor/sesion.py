import datetime
import json
import os
import platform
import secrets
from .util import leer_json


class Sesion:
    def __init__(self, biblioteca, id):
        self.biblioteca, self.id = biblioteca, id
        self.token = secrets.token_hex(16)
        self.propia = False

    def adquirir(self):
        dato = {"equipo": platform.node(), "pid": os.getpid(), "servidor": self.id,
                "inicio": datetime.datetime.now(datetime.timezone.utc).isoformat(), "token": self.token}
        try:
            with self.biblioteca.lock.open("x", encoding="utf-8") as f:
                json.dump(dato, f, ensure_ascii=False)
        except FileExistsError:
            quien = self.biblioteca.lock.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError("Biblioteca en uso: " + quien) from None
        self.propia = True
        testigo = self.biblioteca.raiz / "compartido" / "_ultimo_jugador.txt"
        testigo.write_text(f"{dato['equipo']} | {dato['inicio']} | {self.id}\n", encoding="utf-8")

    def cerrar(self):
        if self.propia:
            if leer_json(self.biblioteca.lock).get("token") != self.token:
                raise RuntimeError("El bloqueo cambió de dueño; no se elimina")
            self.biblioteca.lock.unlink()
            self.propia = False
