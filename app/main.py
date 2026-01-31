"""Punto de entrada de la aplicación Analizador CFDI EDDP.

Ejecuta la interfaz gráfica y gestiona la inicialización de Qt. Este módulo
permite que la aplicación sea ejecutable directamente con `python -m cfdi_analyzer_edpp.app.main`.
"""
from __future__ import annotations

import sys

from app.ui_main import run_app


def main() -> int:
    return run_app()


if __name__ == "__main__":
    sys.exit(main())