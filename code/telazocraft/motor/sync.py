import configparser
import urllib.parse
from .util import http_json


class GuardiaSync:
    def __init__(self, biblioteca):
        self.ruta = biblioteca.raiz / "compartido" / "sync_guardia.local.ini"

    def estado(self):
        if not self.ruta.exists():
            return {"disponible": False}
        c = configparser.ConfigParser()
        c.read(self.ruta, encoding="utf-8")
        s = c["syncthing"]
        base = s.get("gui_url", "http://127.0.0.1:8384").rstrip("/")
        # La clave se usa únicamente como cabecera, nunca forma parte de eventos ni mensajes.
        d = http_json(base + "/rest/db/status?" + urllib.parse.urlencode({"folder": s["folder_id"]}),
                      cabeceras={"X-API-Key": s["api_key"]})
        return {"disponible": True, **{k: d[k] for k in ("state", "needBytes", "needFiles", "needDeletes")}}

    def comprobar(self):
        d = self.estado()
        if d["disponible"] and (d["state"] != "idle" or any(d[k] for k in ("needBytes", "needFiles", "needDeletes"))):
            raise RuntimeError("Syncthing todavía no está al día")
        return d
