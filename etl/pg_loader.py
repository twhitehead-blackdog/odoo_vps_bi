"""
Módulo para cargar datos en PostgreSQL local.

Crea tablas dinámicamente basándose en los datos recibidos de Odoo
y hace UPSERT (INSERT ... ON CONFLICT DO UPDATE) para sincronización incremental.
"""

import logging
from datetime import datetime, date

import psycopg2
import psycopg2.extras

from config.settings import PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD

logger = logging.getLogger(__name__)

# Tabla de control para rastrear la última sincronización por modelo
SYNC_LOG_TABLE = "etl_sync_log"


def get_connection():
    """Crea una conexión a PostgreSQL."""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def init_sync_log(conn):
    """Crea la tabla de control de sincronización si no existe."""
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {SYNC_LOG_TABLE} (
                id SERIAL PRIMARY KEY,
                model_name VARCHAR(128) NOT NULL,
                pg_table VARCHAR(128) NOT NULL,
                last_sync TIMESTAMP NOT NULL,
                records_synced INTEGER DEFAULT 0,
                duration_seconds FLOAT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT,
                UNIQUE(model_name)
            )
        """)
    conn.commit()


def get_last_sync(conn, model_name):
    """Retorna la fecha de última sincronización exitosa para un modelo."""
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT last_sync FROM {SYNC_LOG_TABLE} "
            f"WHERE model_name = %s AND status = 'success'",
            (model_name,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def update_sync_log(conn, model_name, pg_table, records_synced,
                    duration_seconds, status="success", error_message=None):
    """Registra o actualiza el log de sincronización."""
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO {SYNC_LOG_TABLE}
                (model_name, pg_table, last_sync, records_synced,
                 duration_seconds, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (model_name) DO UPDATE SET
                pg_table = EXCLUDED.pg_table,
                last_sync = EXCLUDED.last_sync,
                records_synced = EXCLUDED.records_synced,
                duration_seconds = EXCLUDED.duration_seconds,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message
        """, (
            model_name, pg_table, datetime.utcnow(),
            records_synced, duration_seconds, status, error_message,
        ))
    conn.commit()


# ── Mapeo de tipos Odoo → PostgreSQL ─────────────────────────────────────────

def _infer_pg_type(value):
    """Infiere el tipo PostgreSQL a partir del valor Python recibido de Odoo."""
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return "DOUBLE PRECISION"
    if isinstance(value, (datetime, date)):
        return "TIMESTAMP"
    if isinstance(value, (list, tuple)):
        # Many2one viene como [id, name] — solo guardamos el ID
        return "BIGINT"
    return "TEXT"


def _clean_value(value):
    """Limpia un valor de Odoo para insertar en PostgreSQL."""
    if value is False or value is None:
        return None
    # Many2one: [id, "name"] → id
    if isinstance(value, (list, tuple)) and len(value) >= 1:
        return value[0] if value[0] else None
    return value


# ── Creación dinámica de tablas ──────────────────────────────────────────────

def ensure_table(conn, pg_table, sample_record, fields_list):
    """
    Crea la tabla si no existe, basándose en un registro de ejemplo.
    Si existe, agrega columnas nuevas que falten.
    """
    # Determinar columnas y tipos a partir del sample
    columns = {}
    for field in fields_list:
        if field == "id":
            columns["id"] = "BIGINT PRIMARY KEY"
        else:
            val = sample_record.get(field, "")
            columns[field] = _infer_pg_type(val)

    with conn.cursor() as cur:
        # Verificar si la tabla existe
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
            (pg_table,),
        )
        exists = cur.fetchone()[0]

        if not exists:
            cols_sql = ",\n    ".join(
                f'"{col}" {dtype}' for col, dtype in columns.items()
            )
            create_sql = f'CREATE TABLE "{pg_table}" (\n    {cols_sql}\n)'
            logger.info("Creando tabla: %s", pg_table)
            cur.execute(create_sql)

            # Índice en write_date para sincronización incremental
            if "write_date" in columns:
                cur.execute(
                    f'CREATE INDEX IF NOT EXISTS "idx_{pg_table}_write_date" '
                    f'ON "{pg_table}" ("write_date")'
                )
        else:
            # Verificar columnas existentes y agregar las que falten
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s",
                (pg_table,),
            )
            existing_cols = {row[0] for row in cur.fetchall()}

            for col, dtype in columns.items():
                if col not in existing_cols:
                    # No usar PRIMARY KEY en ALTER ADD
                    clean_dtype = dtype.replace(" PRIMARY KEY", "")
                    logger.info("Agregando columna %s.%s (%s)", pg_table, col, clean_dtype)
                    cur.execute(
                        f'ALTER TABLE "{pg_table}" ADD COLUMN "{col}" {clean_dtype}'
                    )

    conn.commit()


# ── Upsert de datos ─────────────────────────────────────────────────────────

def upsert_batch(conn, pg_table, records, fields_list):
    """
    Inserta o actualiza un lote de registros en PostgreSQL.
    Usa ON CONFLICT (id) DO UPDATE para idempotencia.
    """
    if not records:
        return 0

    # Preparar columnas
    columns = [f for f in fields_list if f in records[0]]
    if "id" not in columns:
        columns.insert(0, "id")

    col_names = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    update_set = ", ".join(
        f'"{c}" = EXCLUDED."{c}"' for c in columns if c != "id"
    )

    sql = (
        f'INSERT INTO "{pg_table}" ({col_names}) VALUES ({placeholders}) '
        f"ON CONFLICT (id) DO UPDATE SET {update_set}"
    )

    # Preparar valores
    rows = []
    for rec in records:
        row = tuple(_clean_value(rec.get(col)) for col in columns)
        rows.append(row)

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=100)

    conn.commit()
    return len(rows)
