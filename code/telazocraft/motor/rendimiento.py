import re
import time
from collections import deque
from .hardware import Monitor


class Rendimiento:
    def __init__(self):
        self.muestras = deque(maxlen=3600)
        self.monitor = Monitor()
        self.tps, self.mspt = None, None

    def linea(self, linea):
        limpia = re.sub(r"\x1b\[[0-9;]*m", "", linea)
        tps = re.search(r"(?:TPS|ticks per second)[^0-9]*([0-9]+[.,]?[0-9]*)", limpia, re.I)
        mspt = re.search(r"(?:tick time|MSPT|Average tick time)[^0-9]*([0-9]+[.,]?[0-9]*)", limpia, re.I)
        if tps:
            self.tps = float(tps[1].replace(",", "."))
        if mspt:
            self.mspt = float(mspt[1].replace(",", "."))

    def medir(self, proceso, jugadores):
        d = self.monitor.medir(proceso.proc.pid if proceso.vivo else None)
        muestra = {"hora": time.time(), "tps": self.tps, "mspt": self.mspt, "jugadores": jugadores, **d}
        self.muestras.append(muestra)
        return muestra
