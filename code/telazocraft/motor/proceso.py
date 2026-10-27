import subprocess
import threading
from .java import buscar, OCULTO


def comando(servidor):
    d = servidor.datos
    java = buscar(d["java_mayor"])
    if d["tipo"] == "neoforge":
        args = servidor.ruta / "libraries/net/neoforged/neoforge" / d["version_loader"] / "win_args.txt"
        if not args.is_file():
            raise FileNotFoundError("Faltan los argumentos de NeoForge de la versión elegida")
        return [java, "@user_jvm_args.txt", "@" + args.relative_to(servidor.ruta).as_posix(), "nogui"]
    return [java, f"-Xms{min(1024, d['ram_mb'])}M", f"-Xmx{d['ram_mb']}M", "-jar", "server.jar", "nogui"]


class Proceso:
    def __init__(self, servidor, linea, comando_prueba=None):
        self.servidor, self.linea = servidor, linea
        self.comando_prueba = comando_prueba
        self.proc = None
        self.escritura = threading.Lock()
        self.lector = None

    def iniciar(self):
        if self.vivo:
            raise RuntimeError("El proceso ya está encendido")
        self.proc = subprocess.Popen(self.comando_prueba or comando(self.servidor), cwd=self.servidor.ruta,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=OCULTO)
        self.lector = threading.Thread(target=self._leer, daemon=True)
        self.lector.start()

    def _leer(self):
        for linea in self.proc.stdout:
            self.linea(linea.rstrip("\r\n"))

    @property
    def vivo(self):
        return self.proc is not None and self.proc.poll() is None

    def enviar(self, texto):
        if "\n" in texto or "\r" in texto:
            raise ValueError("Envía un comando cada vez")
        with self.escritura:
            if not self.vivo:
                raise RuntimeError("El servidor está apagado")
            self.proc.stdin.write(texto.lstrip("/") + "\n")
            self.proc.stdin.flush()

    def parar(self, timeout=180):
        if self.vivo:
            self.enviar("save-all flush")
            self.enviar("stop")
            # Un timeout conserva el bloqueo: no fingir una parada ni copiar datos abiertos.
            self.proc.wait(timeout=timeout)
        if self.lector and self.lector is not threading.current_thread():
            self.lector.join(timeout=5)
        if self.proc:
            self.proc.stdout.close()
            self.proc.stdin.close()
