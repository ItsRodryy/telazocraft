import hashlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from . import test_motor
from telazocraft.motor import modrinth
from telazocraft.motor.util import descargar


class RedTests(unittest.TestCase):
    setUp = test_motor.MotorTests.setUp
    def test_lado_servidor_y_jar_manual_con_cache(self):
        mods = self.s.ruta / "mods"
        mods.mkdir()
        (mods / "mod.jar").write_bytes(b"jar")
        sha = hashlib.sha1(b"jar").hexdigest()
        respuestas = [{sha: {"project_id": "proyecto", "version_number": "1", "id": "v1"}},
                      [{"id": "proyecto", "title": "Mod de ejemplo", "client_side": "unsupported"}]]
        with patch.object(modrinth, "http_json", side_effect=respuestas):
            datos = modrinth.inventario(self.s)
        self.assertEqual(datos[0]["lado"], "unsupported")
        self.assertEqual(modrinth.inventario(self.s, False), datos)

    def test_descarga_corrupta_conserva_destino(self):
        destino = self.b.raiz / "mod.jar"
        destino.write_bytes(b"bueno")
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b"malo")):
            with self.assertRaises(ValueError):
                descargar("https://example.invalid/mod.jar", destino, "0" * 64)
        self.assertEqual(destino.read_bytes(), b"bueno")

    def test_mod_incompatible_no_descarga(self):
        with patch.object(modrinth, "http_json", return_value={"game_versions": ["otra"], "loaders": ["vanilla"]}), patch.object(modrinth, "descargar") as d:
            with self.assertRaises(ValueError):
                modrinth.instalar(self.s, "version")
            d.assert_not_called()
