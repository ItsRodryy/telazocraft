"""Entrada del empaquetador desde la raíz del proyecto."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from telazocraft.common.tls import activar
activar()
from telazocraft.tools.empaquetar import main

if __name__ == "__main__":
    raise SystemExit(main())
