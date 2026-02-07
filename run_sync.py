#!/usr/bin/env python3
"""
Punto de entrada principal para la sincronización Odoo.sh → PostgreSQL.

Uso:
    # Sincronización incremental (normal, cada 15 min)
    python run_sync.py

    # Carga completa (primera vez o reset)
    python run_sync.py --full

    # Sincronizar solo modelos específicos
    python run_sync.py --models sale.order account.move

    # Listar modelos configurados
    python run_sync.py --list

    # Ver campos disponibles de un modelo en Odoo
    python run_sync.py --inspect sale.order
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import LOG_LEVEL, LOG_DIR
from config.models import get_enabled_models
from etl.sync import run_sync
from etl.odoo_client import OdooClient


def setup_logging():
    """Configura logging a consola y archivo."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    log_file = LOG_DIR / "sync.log"

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=log_format,
        handlers=handlers,
    )


def cmd_list():
    """Muestra los modelos configurados."""
    models = get_enabled_models()
    print(f"\n{'Modelo Odoo':<30} {'Tabla PG':<30} {'Prior.':<8} {'Incremental'}")
    print("-" * 80)
    for m in models:
        inc = "Sí" if m.get("incremental") else "No"
        print(f"{m['odoo_model']:<30} {m['pg_table']:<30} {m.get('priority', 99):<8} {inc}")
    print(f"\nTotal: {len(models)} modelos habilitados")


def cmd_inspect(model_name):
    """Muestra los campos disponibles de un modelo en Odoo."""
    odoo = OdooClient()
    odoo.connect()

    if not odoo.check_model_exists(model_name):
        print(f"El modelo '{model_name}' no existe en Odoo.")
        return

    fields = odoo.get_model_fields(model_name)
    print(f"\nCampos de '{model_name}' ({len(fields)} campos):\n")
    print(f"{'Campo':<35} {'Tipo':<20} {'Descripción'}")
    print("-" * 90)
    for name, info in sorted(fields.items()):
        ftype = info.get("type", "?")
        desc = info.get("string", "")
        print(f"{name:<35} {ftype:<20} {desc}")


def main():
    parser = argparse.ArgumentParser(
        description="ETL: Odoo.sh → PostgreSQL para Power BI"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Carga completa (ignora sync incremental)",
    )
    parser.add_argument(
        "--models", nargs="+",
        help="Solo sincronizar estos modelos (ej: sale.order account.move)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Listar modelos configurados y salir",
    )
    parser.add_argument(
        "--inspect", metavar="MODEL",
        help="Ver campos disponibles de un modelo en Odoo",
    )

    args = parser.parse_args()

    setup_logging()

    if args.list:
        cmd_list()
        return

    if args.inspect:
        cmd_inspect(args.inspect)
        return

    summary = run_sync(
        force_full=args.full,
        models_filter=args.models,
    )

    # Imprimir resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE SINCRONIZACIÓN")
    print("=" * 60)
    print(f"Inicio:     {summary['started_at']}")
    print(f"Fin:        {summary['finished_at']}")
    print(f"Duración:   {summary['total_duration']}s")
    print(f"Registros:  {summary['total_records']}")
    print(f"Errores:    {len(summary['errors'])}")

    if summary["errors"]:
        print("\nErrores:")
        for err in summary["errors"]:
            print(f"  ✗ {err}")

    print()

    # Exit code basado en errores
    sys.exit(1 if summary["errors"] else 0)


if __name__ == "__main__":
    main()
