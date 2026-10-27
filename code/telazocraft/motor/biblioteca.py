from pathlib import Path
from .util import guardar_json, leer_json, identificador, ruta_dentro


class Biblioteca:
    def __init__(self, ruta, crear=False):
        self.raiz = Path(ruta).resolve()
        if crear:
            self.raiz.mkdir(parents=True, exist_ok=True)
            if not (self.raiz / "telazocraft.json").exists():
                guardar_json(self.raiz / "telazocraft.json", {"schema": 1})
        if leer_json(self.raiz / "telazocraft.json").get("schema") != 1:
            raise ValueError("Biblioteca incompatible")
        for carpeta in ("servidores", "copias", "compartido", "exportaciones", "archivo"):
            (self.raiz / carpeta).mkdir(exist_ok=True)

    def servidor(self, id):
        from .servidor import Servidor
        return Servidor(self, identificador(id))

    def servidores(self):
        return [self.servidor(p.parent.name) for p in sorted((self.raiz / "servidores").glob("*/servidor.json"))]

    def ruta(self, *partes):
        return ruta_dentro(self.raiz, *partes)

    @property
    def lock(self):
        return self.raiz / "compartido" / "EN_USO.lock"
