import re
import time
from collections import deque


class Consola:
    def __init__(self):
        self.lineas = deque(maxlen=5000)
        self.jugadores = set()
        self.entradas = {}
        self.hubo_jugador = False
        self.vacio_desde = None
        self.lista_numero = 0

    def recibir(self, linea):
        self.lineas.append(linea)
        m = re.search(r": (\S+) (joined|left) the game", linea)
        if m:
            nick, accion = m.groups()
            if accion == "joined":
                self.jugadores.add(nick)
                self.entradas[nick] = time.time()
                self.hubo_jugador = True
                self.vacio_desde = None
            else:
                self.jugadores.discard(nick)
                if not self.jugadores and self.hubo_jugador:
                    self.vacio_desde = time.time()
            self.lista_numero = len(self.jugadores)
            return {"tipo": "entrada" if accion == "joined" else "salida", "jugador": nick}
        m = re.search(r"There are (\d+) of a max of \d+ players online(?::\s*(.*))?", linea)
        if m:
            self.lista_numero = int(m[1])
            if m[2] is not None:
                self.jugadores = {s.strip() for s in m[2].split(",") if s.strip()}
            if self.lista_numero:
                self.hubo_jugador = True
                self.vacio_desde = None
            elif self.hubo_jugador and self.vacio_desde is None:
                self.vacio_desde = time.time()
        m = re.search(r"\[([^\]]+)\] LV_MUERTE_HARDCORE", linea)
        if m:
            return {"tipo": "muerte", "jugador": m[1]}
        return None
