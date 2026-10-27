import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from telazocraft.common import github_releases
from telazocraft.tools.empaquetar import compilar


class EmpaquetadoTests(unittest.TestCase):
    def test_release_exige_hash_y_version_estable(self):
        d = {"tag_name": "v9.8.7", "draft": False, "prerelease": False,
             "assets": [{"name": "Telazocraft-9.8.7-windows.exe", "digest": "sha256:" + "a"*64,
                         "browser_download_url": "https://github.com/ejemplo/telazocraft/releases/download/v9.8.7/Telazocraft-9.8.7-windows.exe"}]}
        with patch.object(github_releases, "http_json", return_value=d):
            self.assertTrue(github_releases.ultima("ejemplo/telazocraft")["nueva"])
            d["assets"][0]["digest"] = ""
            with self.assertRaises(ValueError):
                github_releases.ultima("ejemplo/telazocraft")
            d["prerelease"] = True
            with self.assertRaises(ValueError):
                github_releases.ultima("ejemplo/telazocraft")

    def test_codigo_compilado_importable_y_version_del_paquete(self):
        raiz = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix="telazocraft_compilar_") as td:
            paquete = Path(td)
            compilar(raiz, paquete, Path(sys.executable), "9.8.7")
            init = paquete / "code/telazocraft/__init__.pyc"
            self.assertTrue(init.exists())
            self.assertFalse(list((paquete / "code/telazocraft").rglob("*.py")))
            script = "import sys;sys.path.insert(0,sys.argv[1]);import telazocraft;assert telazocraft.__version__=='9.8.7';assert telazocraft.__file__.endswith('.pyc')"
            subprocess.run([sys.executable, "-B", "-c", script, str(paquete / "code")], check=True)
