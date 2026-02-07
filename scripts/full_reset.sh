#!/bin/bash
# ============================================================================
# Reset completo: elimina todas las tablas y hace una carga desde cero.
# USAR CON CUIDADO — borra todos los datos locales.
#
# Uso:
#   ./scripts/full_reset.sh
# ============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "⚠  ATENCIÓN: Esto eliminará TODOS los datos de la base odoo_bi"
echo "   y hará una carga completa desde Odoo.sh."
echo ""
read -rp "¿Continuar? (escribe 'SI' para confirmar): " CONFIRM

if [ "$CONFIRM" != "SI" ]; then
    echo "Cancelado."
    exit 0
fi

echo ""
echo "Paso 1: Eliminando tablas existentes..."
psql -U "${PG_USER:-bi_user}" -d "${PG_DB:-odoo_bi}" -c "
    DO \$\$
    DECLARE r RECORD;
    BEGIN
        -- Eliminar vistas primero
        FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public')
        LOOP
            EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
        END LOOP;
        -- Eliminar tablas
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
        LOOP
            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        END LOOP;
    END \$\$;
"

echo "Paso 2: Ejecutando sincronización completa..."
cd "$PROJECT_DIR"
python3 run_sync.py --full

echo ""
echo "Paso 3: Creando vistas de BI..."
psql -U "${PG_USER:-bi_user}" -d "${PG_DB:-odoo_bi}" -f sql/create_bi_views.sql

echo ""
echo "Reset completo finalizado."
