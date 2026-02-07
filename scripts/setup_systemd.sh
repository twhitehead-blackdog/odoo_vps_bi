#!/bin/bash
# ============================================================================
# Alternativa a cron: configura un timer de systemd para la sincronización.
# Systemd timers son más robustos que cron (logs con journalctl, reintentos).
#
# Uso:
#   sudo ./scripts/setup_systemd.sh
# ============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(which python3)}"
SERVICE_USER="${SERVICE_USER:-$(whoami)}"

echo "Creando servicio systemd..."

# Crear el archivo de servicio
cat > /etc/systemd/system/odoo-bi-sync.service << EOF
[Unit]
Description=Odoo BI ETL Sync (Odoo.sh → PostgreSQL)
After=network.target postgresql.service

[Service]
Type=oneshot
User=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PYTHON_BIN} ${PROJECT_DIR}/run_sync.py
Environment=PYTHONUNBUFFERED=1

# Reintentar si falla
Restart=on-failure
RestartSec=60

# Timeout: 10 minutos máximo por ejecución
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOF

# Crear el timer (cada 15 minutos)
cat > /etc/systemd/system/odoo-bi-sync.timer << EOF
[Unit]
Description=Ejecutar Odoo BI Sync cada 15 minutos

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

# Activar
systemctl daemon-reload
systemctl enable odoo-bi-sync.timer
systemctl start odoo-bi-sync.timer

echo ""
echo "Timer systemd configurado y activo."
echo ""
echo "Comandos útiles:"
echo "  systemctl status odoo-bi-sync.timer    # Estado del timer"
echo "  systemctl status odoo-bi-sync.service  # Estado de la última ejecución"
echo "  journalctl -u odoo-bi-sync.service -f  # Ver logs en vivo"
echo "  systemctl start odoo-bi-sync.service   # Ejecutar manualmente ahora"
