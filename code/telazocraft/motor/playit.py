import os
import subprocess
import threading
from .java import OCULTO


class Playit:
    def __init__(self, biblioteca, aviso):
        self.ruta = biblioteca.raiz / "compartido" / "playit.exe"
        self.aviso, self.proc = aviso, None
        self.fin = threading.Event()
        self.hilo = None

    def iniciar(self):
        if os.environ.get("GESTOR_NO_PLAYIT") == "1":
            self.aviso("Playit omitido en esta prueba")
            return
        if not self.ruta.is_file():
            self.aviso("Playit no está instalado; conexión local disponible")
            return
        self._lanzar()
        self.hilo = threading.Thread(target=self._vigilar, daemon=True)
        self.hilo.start()

    def _lanzar(self):
        self.proc = subprocess.Popen([str(self.ruta)], cwd=self.ruta.parent, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=OCULTO)

    def _vigilar(self):
        while not self.fin.wait(15):
            if self.proc.poll() is not None:
                self.aviso("Playit se ha cerrado; reiniciando túnel")
                try:
                    self._lanzar()
                except OSError as e:
                    self.aviso(str(e))

    @property
    def vivo(self):
        return self.proc is not None and self.proc.poll() is None

    def cerrar(self):
        self.fin.set()
        if self.hilo:
            self.hilo.join(timeout=20)
        if self.vivo:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
