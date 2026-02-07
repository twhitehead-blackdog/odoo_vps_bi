#!/usr/bin/env python3
"""
Punto de entrada para el portal web de monitoreo del ETL.

Uso:
    # Modo desarrollo (debug, auto-reload)
    python run_portal.py

    # Producción con gunicorn (recomendado)
    gunicorn -w 2 -b 0.0.0.0:8050 portal.app:app

    # Puerto personalizado
    python run_portal.py --port 9000

    # Bind a una IP específica
    python run_portal.py --host 127.0.0.1 --port 8050
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from portal.app import app


def main():
    parser = argparse.ArgumentParser(
        description="Portal web de monitoreo del ETL Odoo BI"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8050, help="Puerto (default: 8050)")
    parser.add_argument("--no-debug", action="store_true", help="Desactivar modo debug")

    args = parser.parse_args()

    print(f"\n  Odoo BI Portal")
    print(f"  http://{args.host}:{args.port}\n")

    app.run(
        host=args.host,
        port=args.port,
        debug=not args.no_debug,
    )


if __name__ == "__main__":
    main()
