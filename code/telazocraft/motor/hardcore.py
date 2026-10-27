import json
import secrets
import time
import zipfile
from . import copias, propiedades
from .util import guardar_json, archivar


def formato_datos(servidor):
    jars = [servidor.ruta / "server.jar"] + list((servidor.ruta / "libraries/net/minecraft/server").rglob("*.jar"))
    for jar in jars:
        if jar.exists():
            with zipfile.ZipFile(jar) as z:
                if "version.json" in z.namelist():
                    d = json.loads(z.read("version.json"))
                    version = d["pack_version"].get("data", d["pack_version"].get("data_major"))
                    if version is None:
                        raise ValueError("El JAR no declara su formato de datapack")
                    return version["major"] if isinstance(version, dict) else version
    raise ValueError("No se pudo comprobar pack_format en el JAR de Minecraft")


def preparar(servidor):
    if not servidor.datos.get("hardcore"):
        return
    pack = servidor.mundo / "datapacks" / "telazocraft"
    if pack.exists():
        return
    formato = formato_datos(servidor)
    guardar_json(pack / "pack.mcmeta", {"pack": {"pack_format": formato, "min_format": formato, "max_format": formato,
                                                "description": "Partidas hardcore de Telazocraft"}})
    guardar_json(pack / "data/minecraft/tags/function/load.json", {"values": ["telazocraft:load"]})
    guardar_json(pack / "data/minecraft/tags/function/tick.json", {"values": ["telazocraft:tick"]})
    funciones = pack / "data/telazocraft/function"
    funciones.mkdir(parents=True, exist_ok=True)
    (funciones / "load.mcfunction").write_text("scoreboard objectives add tc_muertes deathCount\n", encoding="utf-8")
    (funciones / "tick.mcfunction").write_text("execute as @a[scores={tc_muertes=1..}] run function telazocraft:muerte\n", encoding="utf-8")
    (funciones / "muerte.mcfunction").write_text("say LV_MUERTE_HARDCORE\nscoreboard players set @s tc_muertes 0\n", encoding="utf-8")


class Hardcore:
    def __init__(self, servidor, enviar):
        self.servidor, self.enviar = servidor, enviar
        self.config = servidor.datos.get("hardcore")
        self.marcador = servidor.ruta / ".gracia_pendiente"
        self.fin = None
        self.siguiente_efecto = 0
        self.muerto = None

    def entrada(self):
        if self.config and self.marcador.exists() and self.fin is None:
            self.fin = time.monotonic() + self.config.get("gracia_seg", 30)

    @property
    def gracia(self):
        return self.fin is not None and time.monotonic() < self.fin

    def tick(self):
        if self.gracia and time.monotonic() >= self.siguiente_efecto:
            self.enviar("effect give @a minecraft:resistance 6 4 true")
            self.enviar("effect give @a minecraft:fire_resistance 6 0 true")
            self.siguiente_efecto = time.monotonic() + 3
        elif self.fin is not None and not self.gracia and self.marcador.exists():
            self.enviar("effect clear @a minecraft:resistance")
            self.enviar("effect clear @a minecraft:fire_resistance")
            self.marcador.unlink()

    def muerte(self, nick):
        if self.config and not self.gracia:
            self.muerto = nick

    def nueva_partida(self, en_sesion=False):
        if self.servidor.mundo.exists() and (self.servidor.mundo / "level.dat").exists():
            copias.crear(self.servidor, "partida", False, en_sesion)
            archivar(self.servidor.mundo, self.servidor.biblioteca.ruta("archivo", "partidas", self.servidor.id))
        semilla = secrets.randbelow(2**64) - 2**63
        propiedades.escribir(self.servidor.ruta / "server.properties", {"level-seed": semilla, "hardcore": True})
        preparar(self.servidor)
        self.marcador.write_text(str(semilla), encoding="utf-8")
        self.fin, self.muerto = None, None
        return semilla
