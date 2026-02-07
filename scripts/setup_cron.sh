#!/bin/bash
# ============================================================================
# Configura el cron job para ejecutar la sincronización cada 15 minutos.
#
# Uso:
#   chmod +x scripts/setup_cron.sh
#   ./scripts/setup_cron.sh
# ============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CRON_LOG="${PROJECT_DIR}/logs/cron.log"

# Verificar que Python tiene las dependencias
echo "Verificando dependencias..."
$PYTHON_BIN -c "import psycopg2" 2>/dev/null || {
    echo "ERROR: psycopg2 no está instalado. Ejecutar: pip install psycopg2-binary"
    exit 1
}

# Crear directorio de logs
mkdir -p "${PROJECT_DIR}/logs"

# Línea del cron
CRON_CMD="*/15 * * * * cd ${PROJECT_DIR} && ${PYTHON_BIN} run_sync.py >> ${CRON_LOG} 2>&1"

# Verificar si ya existe
if crontab -l 2>/dev/null | grep -qF "run_sync.py"; then
    echo "El cron job ya existe. Actualizando..."
    # Eliminar la línea existente y agregar la nueva
    (crontab -l 2>/dev/null | grep -vF "run_sync.py"; echo "$CRON_CMD") | crontab -
else
    echo "Agregando cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
fi

echo ""
echo "Cron job configurado:"
echo "  $CRON_CMD"
echo ""
echo "Verificar con: crontab -l"
echo "Logs en: ${CRON_LOG}"
