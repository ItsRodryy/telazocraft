import datetime
import json
import threading


class Diario:
    def __init__(self, servidor):
        self.ruta = servidor.ruta / "sesiones.jsonl"
        self.lock = threading.Lock()

    def registrar(self, tipo, **datos):
        dato = {"fecha": datetime.datetime.now(datetime.timezone.utc).isoformat(), "tipo": tipo, **datos}
        with self.lock, self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dato, ensure_ascii=False) + "\n")
        return dato

    def leer(self):
        if not self.ruta.exists():
            return []
        resultado = []
        for linea in self.ruta.read_text(encoding="utf-8").splitlines():
            try:
                resultado.append(json.loads(linea))
            except ValueError:
                resultado.append({"tipo": "registro_dañado", "fecha": ""})
        return resultado
