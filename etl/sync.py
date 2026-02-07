"""
Motor de sincronización principal.

Orquesta la extracción de Odoo.sh y la carga en PostgreSQL local.
Soporta sincronización completa e incremental.
"""

import logging
import time
from datetime import datetime

from config.settings import BATCH_SIZE, MAX_RECORDS
from config.models import get_enabled_models
from etl.odoo_client import OdooClient
from etl.pg_loader import (
    get_connection,
    init_sync_log,
    get_last_sync,
    update_sync_log,
    ensure_table,
    upsert_batch,
)

logger = logging.getLogger(__name__)


def sync_model(odoo, conn, model_cfg, force_full=False):
    """
    Sincroniza un modelo individual de Odoo a PostgreSQL.

    Args:
        odoo: instancia de OdooClient conectada
        conn: conexión a PostgreSQL
        model_cfg: diccionario de configuración del modelo
        force_full: si True, ignora la última sync y trae todo

    Returns:
        tuple(records_synced, duration_seconds)
    """
    model_name = model_cfg["odoo_model"]
    pg_table = model_cfg["pg_table"]
    fields = model_cfg.get("fields", [])
    base_domain = list(model_cfg.get("domain", []))
    incremental = model_cfg.get("incremental", True) and not force_full

    start = time.time()
    total_synced = 0

    # Verificar si el modelo existe en Odoo
    if not odoo.check_model_exists(model_name):
        logger.warning("Modelo %s no existe en Odoo, omitiendo.", model_name)
        update_sync_log(
            conn, model_name, pg_table, 0, 0,
            status="skipped", error_message="Modelo no existe en Odoo",
        )
        return 0, 0

    # Construir dominio con filtro incremental
    domain = list(base_domain)
    if incremental:
        last_sync = get_last_sync(conn, model_name)
        if last_sync:
            sync_str = last_sync.strftime("%Y-%m-%d %H:%M:%S")
            domain.append(("write_date", ">=", sync_str))
            logger.info(
                "Sync incremental de %s desde %s", model_name, sync_str
            )
        else:
            logger.info(
                "Primera sync de %s (sin registro previo, carga completa)",
                model_name,
            )
    else:
        logger.info("Sync completa de %s (force_full=True)", model_name)

    # Asegurar que siempre incluimos id y write_date
    if fields:
        if "id" not in fields:
            fields = ["id"] + fields
        if "write_date" not in fields:
            fields.append("write_date")

    # Leer por lotes
    first_batch = True
    for batch in odoo.read_batched(
        model_name,
        domain=domain,
        fields=fields if fields else None,
        batch_size=BATCH_SIZE,
        order="id asc",
    ):
        if first_batch and batch:
            # Crear/actualizar estructura de tabla con el primer lote
            ensure_table(conn, pg_table, batch[0], fields or list(batch[0].keys()))
            first_batch = False

        count = upsert_batch(conn, pg_table, batch, fields or list(batch[0].keys()))
        total_synced += count

        if MAX_RECORDS and total_synced >= MAX_RECORDS:
            logger.info("Límite de %d registros alcanzado para %s", MAX_RECORDS, model_name)
            break

    duration = time.time() - start
    logger.info(
        "✓ %s → %s: %d registros en %.1fs",
        model_name, pg_table, total_synced, duration,
    )

    update_sync_log(conn, model_name, pg_table, total_synced, duration)
    return total_synced, duration


def run_sync(force_full=False, models_filter=None):
    """
    Ejecuta la sincronización completa de todos los modelos habilitados.

    Args:
        force_full: si True, hace carga completa ignorando incrementales
        models_filter: lista de nombres de modelos a sincronizar (None = todos)

    Returns:
        dict con resumen de la ejecución
    """
    start_time = time.time()
    summary = {
        "started_at": datetime.utcnow().isoformat(),
        "models": {},
        "total_records": 0,
        "errors": [],
    }

    # Conexiones
    odoo = OdooClient()
    odoo.connect()

    conn = get_connection()
    init_sync_log(conn)

    # Obtener modelos a sincronizar
    enabled_models = get_enabled_models()
    if models_filter:
        enabled_models = [
            m for m in enabled_models
            if m["odoo_model"] in models_filter or m["pg_table"] in models_filter
        ]

    logger.info(
        "Iniciando sincronización de %d modelos (force_full=%s)",
        len(enabled_models), force_full,
    )

    for model_cfg in enabled_models:
        model_name = model_cfg["odoo_model"]
        try:
            records, duration = sync_model(odoo, conn, model_cfg, force_full)
            summary["models"][model_name] = {
                "records": records,
                "duration": round(duration, 2),
                "status": "success",
            }
            summary["total_records"] += records
        except Exception as exc:
            error_msg = f"{model_name}: {exc}"
            logger.error("Error sincronizando %s: %s", model_name, exc, exc_info=True)
            summary["models"][model_name] = {
                "records": 0,
                "duration": 0,
                "status": "error",
                "error": str(exc),
            }
            summary["errors"].append(error_msg)

            # Registrar error en sync_log
            update_sync_log(
                conn, model_name, model_cfg["pg_table"],
                0, 0, status="error", error_message=str(exc),
            )

    conn.close()

    total_duration = time.time() - start_time
    summary["total_duration"] = round(total_duration, 2)
    summary["finished_at"] = datetime.utcnow().isoformat()

    logger.info(
        "Sincronización completada: %d registros en %.1fs (%d errores)",
        summary["total_records"], total_duration, len(summary["errors"]),
    )

    return summary
