#!/bin/bash
# ============================================================================
# Configura el portal web como servicio systemd con gunicorn.
#
# Uso:
#   sudo ./scripts/setup_portal_systemd.sh
# ============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(which python3)}"
GUNICORN_BIN="${GUNICORN_BIN:-$(which gunicorn 2>/dev/null || echo "${PROJECT_DIR}/venv/bin/gunicorn")}"
SERVICE_USER="${SERVICE_USER:-$(whoami)}"
PORT="${PORTAL_PORT:-8050}"

echo "Creando servicio systemd para el portal..."

cat > /etc/systemd/system/odoo-bi-portal.service << EOF
[Unit]
Description=Odoo BI Portal Web
After=network.target postgresql.service

[Service]
Type=exec
User=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${GUNICORN_BIN} -w 2 -b 0.0.0.0:${PORT} --timeout 120 portal.app:app
Environment=PYTHONUNBUFFERED=1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable odoo-bi-portal.service
systemctl start odoo-bi-portal.service

echo ""
echo "Portal iniciado en http://0.0.0.0:${PORT}"
echo ""
echo "Comandos utiles:"
echo "  systemctl status odoo-bi-portal     # Estado"
echo "  systemctl restart odoo-bi-portal    # Reiniciar"
echo "  journalctl -u odoo-bi-portal -f     # Logs en vivo"
