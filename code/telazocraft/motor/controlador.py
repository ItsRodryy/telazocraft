import datetime
import json
import platform
import threading
import time
from collections import deque
from . import copias
from .consola import Consola
from .diario import Diario
from .hardcore import Hardcore, preparar
from .playit import Playit
from .proceso import Proceso
from .rendimiento import Rendimiento
from .sesion import Sesion
from .sync import GuardiaSync


class Controlador:
    def __init__(self, servidor, evento=lambda tipo, datos: None, comando_prueba=None):
        self.servidor, self.evento = servidor, evento
        self.estado = "apagado"
        self.consola = Consola()
        self.diario = Diario(servidor)
        self.rendimiento = Rendimiento()
        self.proceso = Proceso(servidor, self._linea, comando_prueba)
        self.sesion = Sesion(servidor.biblioteca, servidor.id)
        self.playit = Playit(servidor.biblioteca, lambda s: self.emitir("aviso", s))
        self.hardcore = Hardcore(servidor, self.proceso.enviar)
        self.fin = threading.Event()
        self.listo = threading.Event()
        self.reinicio = threading.Event()
        self.hilo = None
        self.reinicios_hardcore = deque()

    def emitir(self, tipo, datos):
        self.evento(tipo, datos)

    def _estado(self, valor):
        self.estado = valor
        self.emitir("estado", valor)

    def _linea(self, linea):
        self.emitir("log", linea)
        self.rendimiento.linea(linea)
        evento = self.consola.recibir(linea)
        if evento:
            nick = evento["jugador"]
            if evento["tipo"] == "entrada":
                self.hardcore.entrada()
            elif evento["tipo"] == "salida":
                evento["duracion_seg"] = max(0, time.time() - self.consola.entradas.pop(nick, time.time()))
            elif evento["tipo"] == "muerte":
                self.hardcore.muerte(nick)
            self.diario.registrar(**evento)
            self.emitir("jugadores", {"conectados": sorted(self.consola.jugadores), "evento": evento})
        if "Done (" in linea:
            self.listo.set()
            self._estado("encendido")

    def iniciar(self):
        if self.hilo and self.hilo.is_alive():
            raise RuntimeError("Este servidor ya tiene una sesión")
        self.servidor.recargar()
        self.servidor.exigir_parado()
        self.fin.clear()
        GuardiaSync(self.servidor.biblioteca).comprobar()
        if self.fin.is_set():
            return
        self.sesion.adquirir()
        self.reinicio.clear()
        self.hilo = threading.Thread(target=self._ejecutar, name="servidor-" + self.servidor.id, daemon=False)
        self.hilo.start()

    def parar(self, esperar=False, timeout=300):
        self.fin.set()
        if esperar and self.hilo:
            self.hilo.join(timeout)
            if self.hilo.is_alive():
                raise TimeoutError("La parada todavía no ha terminado")

    def reiniciar(self):
        if not self.proceso.vivo:
            raise RuntimeError("El servidor está apagado")
        self.reinicio.set()

    def comando(self, texto):
        if texto.strip().lstrip("/").lower() == "stop":
            self.parar()
        else:
            self.proceso.enviar(texto)

    def copiar(self, nivel):
        self._estado("copiando")
        destino = copias.crear(self.servidor, nivel, en_sesion=True)
        self.diario.registrar("copia", nivel=nivel, archivo=destino.name)
        self.emitir("copia", str(destino))

    def _ejecutar(self):
        error = None
        try:
            preparar(self.servidor)
            self.playit.iniciar()
            self.diario.registrar("arranque", equipo=platform.node())
            crashes = 0
            while not self.fin.is_set():
                self.listo.clear()
                self._estado("arrancando")
                self.proceso.iniciar()
                inicio = time.monotonic()
                ciclo = float(self.servidor.datos.get("reinicio_h", 2)) * 3600
                fin_ciclo = inicio + ciclo if ciclo else float("inf")
                lista = inicio
                hardware = inicio + 60
                avisos = {300, 180, 60, 30, 10}
                motivo = "sesion"
                while self.proceso.vivo and not self.fin.wait(0.25):
                    ahora = time.monotonic()
                    if self.listo.is_set():
                        self.hardcore.tick()
                        if ahora >= lista:
                            self.proceso.enviar("list")
                            lista = ahora + 300
                        if ahora >= hardware:
                            muestra = self.rendimiento.monitor.medir(self.proceso.proc.pid)
                            carpeta = self.servidor.biblioteca.ruta("compartido", "logs_hardware")
                            carpeta.mkdir(exist_ok=True)
                            with (carpeta / (datetime.date.today().isoformat() + ".log")).open("a", encoding="utf-8") as f:
                                f.write(json.dumps({"servidor": self.servidor.id, "hora": time.time(), **muestra}) + "\n")
                            hardware = ahora + 60
                        for segundos in sorted(avisos, reverse=True):
                            if fin_ciclo - ahora <= segundos:
                                self.proceso.enviar("tellraw @a " + json.dumps({"text": f"Reinicio en {segundos} s", "color": "gold"}))
                                avisos.remove(segundos)
                        if self.hardcore.muerto:
                            motivo = "partida"
                            break
                        vacio = self.consola.vacio_desde
                        minutos = self.servidor.datos.get("apagar_si_vacio_min", 10)
                        if minutos and vacio is not None and time.time() - vacio >= minutos * 60:
                            self.fin.set()
                            break
                        if self.reinicio.is_set() or ahora >= fin_ciclo:
                            motivo = "auto"
                            self.reinicio.clear()
                            break
                caido = not self.proceso.vivo and not self.fin.is_set()
                self._estado("parando")
                self.proceso.parar()
                if caido:
                    crashes = crashes + 1 if time.monotonic() - inicio < 600 else 0
                    self.emitir("aviso", "El servidor se cerró inesperadamente")
                    if crashes >= 3:
                        raise RuntimeError("Tres fallos de arranque: se ha detenido el bucle")
                    if (self.servidor.mundo / "level.dat").exists():
                        self.copiar("auto")
                    if self.fin.wait(10):
                        break
                elif motivo == "partida":
                    self.diario.registrar("partida_perdida", jugador=self.hardcore.muerto)
                    semilla = self.hardcore.nueva_partida(en_sesion=True)
                    self.emitir("aviso", "Partida perdida; nueva semilla: " + str(semilla))
                    limite = self.hardcore.config.get("freno_reinicios", 0)
                    ahora = time.monotonic()
                    self.reinicios_hardcore.append(ahora)
                    while self.reinicios_hardcore and ahora - self.reinicios_hardcore[0] > 900:
                        self.reinicios_hardcore.popleft()
                    if limite and len(self.reinicios_hardcore) >= limite:
                        raise RuntimeError("Se ha alcanzado el freno de reinicios hardcore")
                else:
                    self.copiar(motivo)
                    if motivo == "sesion":
                        break
                self.consola.jugadores.clear()
                self.consola.lista_numero = 0
                self.consola.vacio_desde = time.time() if self.consola.hubo_jugador else None
        except Exception as exc:
            error = str(exc)
            self.emitir("error", error)
        finally:
            try:
                if self.proceso.vivo:
                    self.proceso.parar()
                    self.copiar("sesion")
                self.diario.registrar("parada", error=error)
            except Exception as exc:
                error = str(exc)
                self.emitir("error", error)
            self.playit.cerrar()
            if not self.proceso.vivo:
                self.sesion.cerrar()
            self._estado("error" if error else "apagado")

    def medir_rendimiento(self):
        if self.proceso.vivo and self.listo.is_set():
            self.proceso.enviar("neoforge tps" if self.servidor.datos["tipo"] == "neoforge" else "tick query")
            return self.rendimiento.medir(self.proceso, self.consola.lista_numero)
        return None
