from .util import leer_json, guardar_json, ruta_dentro
from .propiedades import leer


class Servidor:
    def __init__(self, biblioteca, id):
        self.biblioteca, self.id = biblioteca, id
        self.ruta = biblioteca.ruta("servidores", id)
        self.recargar()

    def recargar(self):
        self.datos = leer_json(self.ruta / "servidor.json")
        if self.datos.get("schema") != 1:
            raise ValueError("Esquema de servidor incompatible")
        if self.datos.get("tipo") not in ("neoforge", "vanilla"):
            raise ValueError("Tipo de servidor desconocido")
        if int(self.datos.get("ram_mb", 0)) < 512:
            raise ValueError("La RAM debe ser al menos 512 MB")
        return self

    @property
    def nombre(self):
        return self.datos["nombre"]

    @property
    def mundo(self):
        nombre = leer(self.ruta / "server.properties").get("level-name", "world") or "world"
        ruta = ruta_dentro(self.ruta, nombre)
        if ruta == self.ruta:
            raise ValueError("El mundo no puede ser la raíz del servidor")
        return ruta

    def exigir_parado(self):
        if self.biblioteca.lock.exists():
            raise RuntimeError("Hay una sesión abierta; detén el servidor antes de cambiar datos")

    def guardar(self):
        self.exigir_parado()
        guardar_json(self.ruta / "servidor.json", self.datos)
