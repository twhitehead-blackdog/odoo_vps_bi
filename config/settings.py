"""
Configuración central del ETL Odoo.sh → PostgreSQL VPS.

Las credenciales se leen de variables de entorno o de un archivo .env
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Cargar .env si existe (sin depender de python-dotenv en producción)
# ---------------------------------------------------------------------------
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

# ---------------------------------------------------------------------------
# Odoo.sh  –  conexión XML-RPC
# ---------------------------------------------------------------------------
ODOO_URL = os.environ.get("ODOO_URL", "https://mycompany.odoo.com")
ODOO_DB = os.environ.get("ODOO_DB", "mycompany-main-12345678")
ODOO_USER = os.environ.get("ODOO_USER", "admin")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "")  # API key recomendado

# ---------------------------------------------------------------------------
# PostgreSQL local (VPS)  –  destino para Power BI
# ---------------------------------------------------------------------------
PG_HOST = os.environ.get("PG_HOST", "127.0.0.1")
PG_PORT = int(os.environ.get("PG_PORT", "5432"))
PG_DB = os.environ.get("PG_DB", "odoo_bi")
PG_USER = os.environ.get("PG_USER", "bi_user")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "")

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------
# Tamaño de lote para lectura desde Odoo (XML-RPC tiene límites prácticos)
BATCH_SIZE = int(os.environ.get("ETL_BATCH_SIZE", "500"))

# Número de registros máximos por modelo (0 = sin límite)
MAX_RECORDS = int(os.environ.get("ETL_MAX_RECORDS", "0"))

# Nivel de logging: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = os.environ.get("ETL_LOG_LEVEL", "INFO")

# Directorio de logs
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
