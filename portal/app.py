"""
Portal web para monitoreo y gestión del ETL Odoo.sh → PostgreSQL.

Aplicación Flask independiente (NO es un módulo de Odoo).
"""

import json
import logging
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash

# Asegurar que el directorio raíz del proyecto esté en el path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD, LOG_DIR
from config.models import MODELS, get_enabled_models
from etl.pg_loader import get_connection, SYNC_LOG_TABLE

app = Flask(__name__)
app.secret_key = "odoo-bi-portal-secret-change-me"

logger = logging.getLogger(__name__)

# Estado global del sync en curso
_sync_status = {
    "running": False,
    "started_at": None,
    "output": "",
    "pid": None,
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _get_db():
    """Retorna conexión PG o None si no se puede conectar."""
    try:
        return get_connection()
    except Exception:
        return None


def _query(sql, params=None):
    """Ejecuta un SELECT y retorna lista de dicts."""
    conn = _get_db()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def _query_one(sql, params=None):
    """Ejecuta un SELECT y retorna un dict o None."""
    rows = _query(sql, params)
    return rows[0] if rows else None


def _table_exists(table_name):
    """Verifica si una tabla existe en PostgreSQL."""
    row = _query_one(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s) AS e",
        (table_name,),
    )
    return row and row.get("e", False)


def _get_sync_log():
    """Retorna el log de sincronización completo."""
    if not _table_exists(SYNC_LOG_TABLE):
        return []
    return _query(f"""
        SELECT model_name, pg_table, last_sync, records_synced,
               duration_seconds, status, error_message,
               NOW() - last_sync AS time_since_sync
        FROM {SYNC_LOG_TABLE}
        ORDER BY last_sync DESC
    """)


def _get_table_counts():
    """Retorna conteo de filas para cada tabla sincronizada."""
    counts = {}
    conn = _get_db()
    if not conn:
        return counts
    try:
        with conn.cursor() as cur:
            for m in MODELS:
                tbl = m["pg_table"]
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
                    counts[tbl] = cur.fetchone()[0]
                except Exception:
                    conn.rollback()
                    counts[tbl] = None
    finally:
        conn.close()
    return counts


def _run_sync_background(args):
    """Ejecuta run_sync.py en background y captura salida."""
    global _sync_status
    _sync_status["running"] = True
    _sync_status["started_at"] = datetime.utcnow().isoformat()
    _sync_status["output"] = ""

    cmd = [sys.executable, str(PROJECT_ROOT / "run_sync.py")] + args
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        _sync_status["pid"] = proc.pid
        output_lines = []
        for line in proc.stdout:
            output_lines.append(line)
            _sync_status["output"] = "".join(output_lines[-200:])
        proc.wait()
    except Exception as exc:
        _sync_status["output"] += f"\nERROR: {exc}"
    finally:
        _sync_status["running"] = False
        _sync_status["pid"] = None


# ── Rutas: Dashboard ───────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    """Página principal: resumen del estado de sincronización."""
    sync_log = _get_sync_log()
    table_counts = _get_table_counts()
    enabled_models = get_enabled_models()

    # Estadísticas generales
    db_connected = _get_db() is not None
    total_models = len(enabled_models)
    synced_models = len([s for s in sync_log if s["status"] == "success"])
    error_models = len([s for s in sync_log if s["status"] == "error"])
    skipped_models = len([s for s in sync_log if s["status"] == "skipped"])
    total_records = sum(c for c in table_counts.values() if c is not None)

    # Última sync global
    last_sync = sync_log[0]["last_sync"] if sync_log else None

    # Enriquecer sync_log con row_count
    for entry in sync_log:
        entry["row_count"] = table_counts.get(entry["pg_table"])

    return render_template(
        "dashboard.html",
        db_connected=db_connected,
        total_models=total_models,
        synced_models=synced_models,
        error_models=error_models,
        skipped_models=skipped_models,
        total_records=total_records,
        last_sync=last_sync,
        sync_log=sync_log,
        sync_running=_sync_status["running"],
    )


# ── Rutas: Modelos ─────────────────────────────────────────────────────────

@app.route("/models")
def models_list():
    """Lista de todos los modelos configurados con su estado."""
    enabled = get_enabled_models()
    sync_log = {s["model_name"]: s for s in _get_sync_log()}
    table_counts = _get_table_counts()

    models_data = []
    for m in MODELS:
        log_entry = sync_log.get(m["odoo_model"], {})
        models_data.append({
            **m,
            "last_sync": log_entry.get("last_sync"),
            "records_synced": log_entry.get("records_synced", 0),
            "status": log_entry.get("status", "never"),
            "error_message": log_entry.get("error_message"),
            "row_count": table_counts.get(m["pg_table"]),
            "fields_count": len(m.get("fields", [])),
        })

    return render_template("models.html", models=models_data)


@app.route("/models/<path:model_name>")
def model_detail(model_name):
    """Detalle de un modelo: campos, últimos registros, estado de sync."""
    model_cfg = next((m for m in MODELS if m["odoo_model"] == model_name), None)
    if not model_cfg:
        flash(f"Modelo '{model_name}' no encontrado en la configuración.", "danger")
        return redirect(url_for("models_list"))

    pg_table = model_cfg["pg_table"]
    sync_entry = _query_one(
        f"SELECT * FROM {SYNC_LOG_TABLE} WHERE model_name = %s",
        (model_name,),
    ) if _table_exists(SYNC_LOG_TABLE) else None

    # Conteo de filas
    row_count = None
    sample_rows = []
    columns = []

    if _table_exists(pg_table):
        rc = _query_one(f'SELECT COUNT(*) AS cnt FROM "{pg_table}"')
        row_count = rc["cnt"] if rc else 0

        # Columnas de la tabla
        columns = _query(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = %s ORDER BY ordinal_position",
            (pg_table,),
        )

        # Últimos 20 registros
        col_names = ", ".join(f'"{c["column_name"]}"' for c in columns[:15])
        if col_names:
            sample_rows = _query(
                f'SELECT {col_names} FROM "{pg_table}" ORDER BY id DESC LIMIT 20'
            )

    return render_template(
        "model_detail.html",
        model=model_cfg,
        sync_entry=sync_entry,
        row_count=row_count,
        columns=columns,
        sample_rows=sample_rows,
    )


# ── Rutas: Logs ────────────────────────────────────────────────────────────

@app.route("/logs")
def logs_page():
    """Muestra los logs del ETL."""
    log_file = LOG_DIR / "sync.log"
    lines = []
    if log_file.exists():
        with open(log_file, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-500:]
    return render_template("logs.html", log_lines=lines)


# ── Rutas: API (JSON) ──────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    """Estado general en JSON."""
    sync_log = _get_sync_log()
    table_counts = _get_table_counts()
    return jsonify({
        "db_connected": _get_db() is not None,
        "sync_running": _sync_status["running"],
        "sync_started_at": _sync_status["started_at"],
        "models_total": len(MODELS),
        "models_enabled": len(get_enabled_models()),
        "last_sync": sync_log[0]["last_sync"].isoformat() if sync_log and sync_log[0]["last_sync"] else None,
        "total_records": sum(c for c in table_counts.values() if c is not None),
        "errors": [s["model_name"] for s in sync_log if s["status"] == "error"],
    })


@app.route("/api/sync/status")
def api_sync_status():
    """Estado del sync en curso."""
    return jsonify(_sync_status)


@app.route("/api/sync/start", methods=["POST"])
def api_sync_start():
    """Inicia sincronización desde el portal."""
    if _sync_status["running"]:
        return jsonify({"error": "Ya hay una sincronización en curso"}), 409

    data = request.get_json(silent=True) or {}
    args = []
    if data.get("full"):
        args.append("--full")
    if data.get("models"):
        args.extend(["--models"] + data["models"])

    thread = threading.Thread(target=_run_sync_background, args=(args,), daemon=True)
    thread.start()

    return jsonify({"status": "started", "args": args})


@app.route("/api/sync/output")
def api_sync_output():
    """Retorna la salida en vivo del sync en curso."""
    return jsonify({
        "running": _sync_status["running"],
        "output": _sync_status["output"],
    })


@app.route("/api/models")
def api_models():
    """Lista de modelos en JSON."""
    sync_log = {s["model_name"]: s for s in _get_sync_log()}
    table_counts = _get_table_counts()

    result = []
    for m in MODELS:
        log_entry = sync_log.get(m["odoo_model"], {})
        result.append({
            "odoo_model": m["odoo_model"],
            "pg_table": m["pg_table"],
            "enabled": m.get("enabled", True),
            "incremental": m.get("incremental", True),
            "priority": m.get("priority", 99),
            "fields_count": len(m.get("fields", [])),
            "last_sync": log_entry.get("last_sync", "").isoformat() if log_entry.get("last_sync") else None,
            "records_synced": log_entry.get("records_synced", 0),
            "row_count": table_counts.get(m["pg_table"]),
            "status": log_entry.get("status", "never"),
        })

    return jsonify(result)


@app.route("/api/table/<table_name>/count")
def api_table_count(table_name):
    """Conteo de registros de una tabla."""
    if not _table_exists(table_name):
        return jsonify({"error": "Tabla no existe"}), 404
    row = _query_one(f'SELECT COUNT(*) AS cnt FROM "{table_name}"')
    return jsonify({"table": table_name, "count": row["cnt"] if row else 0})


# ── Filtros Jinja ──────────────────────────────────────────────────────────

@app.template_filter("timedelta_short")
def timedelta_short(td):
    """Formatea un timedelta a algo legible: '2h 15m', '3d 4h', '45s'."""
    if not td:
        return "—"
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "ahora"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


@app.template_filter("number_format")
def number_format(value):
    """Formatea números con separador de miles."""
    if value is None:
        return "—"
    return f"{value:,.0f}"


@app.template_filter("dt_format")
def dt_format(value, fmt="%Y-%m-%d %H:%M:%S"):
    """Formatea datetime."""
    if not value:
        return "—"
    if isinstance(value, str):
        return value
    return value.strftime(fmt)


# ── Arranque ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=8050, debug=True)
