# CLAUDE.md — AI Assistant Guide for odoo_vps_bi

## Project Overview

**odoo_vps_bi** is an ETL pipeline that synchronizes data from **Odoo.sh** (via XML-RPC) into a local **PostgreSQL** database on a VPS, refreshed every 15 minutes, for consumption by **Power BI**. It includes an independent **Flask web portal** for monitoring and managing the ETL.

```
Odoo.sh  ──XML-RPC──→  ETL (Python)  ──UPSERT──→  PostgreSQL VPS  ←──DirectQuery──  Power BI
                                                          ↑
                                                    Portal Flask :8050
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Data source | Odoo.sh (XML-RPC API) |
| ETL | Python 3.8+ (stdlib `xmlrpc.client` + `psycopg2`) |
| Database | PostgreSQL 12+ |
| Web portal | Flask 3.0+ / Gunicorn / Bootstrap 5 |
| Scheduling | cron or systemd timer (every 15 min) |
| BI Frontend | Power BI (DirectQuery or Import) |

---

## Project Structure

```
odoo_vps_bi/
├── CLAUDE.md                  # This file
├── README.md                  # Setup & usage
├── run_sync.py                # CLI entry point for ETL
├── run_portal.py              # CLI entry point for web portal
├── requirements.txt           # psycopg2-binary, flask, gunicorn
├── .env.example               # Credential template
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── settings.py            # Reads .env, exposes config constants
│   └── models.py              # 35 Odoo models to sync
├── etl/
│   ├── __init__.py
│   ├── odoo_client.py         # XML-RPC client with batched reads
│   ├── pg_loader.py           # Dynamic table creation + UPSERT
│   └── sync.py                # Orchestrator: incremental & full sync
├── portal/
│   ├── __init__.py
│   ├── app.py                 # Flask app (routes, API, helpers)
│   ├── templates/
│   │   ├── base.html          # Layout: navbar, sync modal, dark theme
│   │   ├── dashboard.html     # KPIs + sync status table
│   │   ├── models.html        # All models grouped by area
│   │   ├── model_detail.html  # Fields, PG columns, data preview
│   │   └── logs.html          # ETL log viewer with filter
│   └── static/
│       ├── css/portal.css
│       └── js/portal.js       # Sync trigger, polling, UI logic
├── sql/
│   ├── init_database.sql      # Create DB, users, permissions
│   └── create_bi_views.sql    # 10 denormalized views for Power BI
├── scripts/
│   ├── setup_cron.sh          # Install cron job
│   ├── setup_systemd.sh       # Install systemd timer for ETL
│   ├── setup_portal_systemd.sh# Install systemd service for portal
│   └── full_reset.sh          # Drop all & reload
└── logs/                      # Runtime (gitignored)
```

---

## Key Files

### ETL Core

| File | Purpose |
|------|---------|
| `config/settings.py` | Central config — reads `.env`, exposes `ODOO_*`, `PG_*`, `BATCH_SIZE`, `LOG_LEVEL` |
| `config/models.py` | `MODELS` list defining all Odoo models to sync (model, table, fields, domain, priority) |
| `etl/odoo_client.py` | XML-RPC wrapper. Key: `read_batched()` generator for paginated reads |
| `etl/pg_loader.py` | `ensure_table()` auto-creates tables; `upsert_batch()` does `INSERT ON CONFLICT` |
| `etl/sync.py` | `run_sync()` orchestrates full pipeline; applies `write_date >= last_sync` filter |
| `run_sync.py` | CLI: `--full`, `--models`, `--list`, `--inspect` |

### Portal Web

| File | Purpose |
|------|---------|
| `portal/app.py` | Flask app with page routes (`/`, `/models`, `/models/<name>`, `/logs`) and API routes (`/api/*`) |
| `portal/templates/base.html` | Layout: dark theme, navbar, sync buttons, live sync modal |
| `portal/templates/dashboard.html` | KPI cards + sync log table per model |
| `portal/templates/models.html` | All models grouped by area with search filter |
| `portal/templates/model_detail.html` | Model config, sync status, PG columns, data preview (last 20 rows) |
| `portal/templates/logs.html` | ETL log viewer with text filter |
| `portal/static/js/portal.js` | `startSync()`, `syncModel()`, `showSyncModal()` with live output polling |
| `run_portal.py` | CLI: `--host`, `--port`, `--no-debug` |

### SQL Views for Power BI

| View | Content |
|------|---------|
| `bi_ventas` | Sales orders + lines + partner + product |
| `bi_compras` | Purchase orders + lines |
| `bi_facturas` | Invoices with partner, journal, type label |
| `bi_apuntes_contables` | Journal items with account details |
| `bi_crm` | CRM pipeline with stages |
| `bi_inventario` | Stock quants with product/location |
| `bi_pagos` | Payments with partner/journal |
| `bi_pos_ventas` | POS orders + lines + session + product |
| `bi_pos_pagos` | POS payments by method |
| `bi_pos_sesiones` | POS session summary |
| `bi_sync_status` | ETL health monitoring |

---

## Synced Odoo Models (35 models)

| Priority | Area | Models |
|----------|------|--------|
| 1 | Masters | `res.company`, `res.currency`, `res.currency.rate`, `res.country`, `res.country.state`, `res.users`, `account.journal` |
| 2 | Contacts | `res.partner` |
| 3 | Products | `product.category`, `product.template`, `product.product`, `uom.uom` |
| 10 | Sales | `sale.order`, `sale.order.line` |
| 11 | Purchases | `purchase.order`, `purchase.order.line` |
| 20 | Accounting | `account.move`, `account.move.line`, `account.account` |
| 21 | Payments | `account.payment` |
| 30 | Inventory | `stock.warehouse`, `stock.location`, `stock.picking`, `stock.move`, `stock.quant` |
| 40 | CRM | `crm.lead`, `crm.stage` |
| 50 | HR | `hr.employee`, `hr.department` |
| 60-62 | POS | `pos.session`, `pos.config`, `pos.payment.method`, `pos.order`, `pos.order.line`, `pos.payment`, `report.pos.order` |

Models that don't exist in the Odoo instance are automatically skipped.

---

## Common Commands

```bash
# --- ETL ---
python run_sync.py              # Incremental sync
python run_sync.py --full       # Full sync
python run_sync.py --models sale.order pos.order  # Specific models
python run_sync.py --list       # List all configured models
python run_sync.py --inspect sale.order  # Show Odoo fields

# --- Portal ---
python run_portal.py            # Dev server on :8050
python run_portal.py --port 9000
gunicorn -w 2 -b 0.0.0.0:8050 portal.app:app  # Production

# --- Portal API (examples) ---
curl http://localhost:8050/api/status
curl http://localhost:8050/api/models
curl -X POST http://localhost:8050/api/sync/start -H 'Content-Type: application/json' -d '{"full": true}'
curl -X POST http://localhost:8050/api/sync/start -H 'Content-Type: application/json' -d '{"models": ["pos.order"]}'
```

---

## Development Conventions

### Python Style
- PEP 8
- Dependencies: `psycopg2-binary`, `flask`, `gunicorn` (stdlib `xmlrpc.client`)
- All credentials via `.env` / environment variables — never hardcoded
- Logging via stdlib `logging` at INFO level

### Adding a New Model
1. Add entry to `config/models.py` → `MODELS` list
2. Tables are created automatically on first sync
3. Optionally add a `bi_*` view in `sql/create_bi_views.sql`

### Portal Development
- Templates use Jinja2 + Bootstrap 5 (CDN) + Bootstrap Icons
- Dark theme by default (`data-bs-theme="dark"` on `<html>`)
- Custom filters: `timedelta_short`, `number_format`, `dt_format`
- Sync runs in background thread via `subprocess.Popen` on `run_sync.py`
- API returns JSON; frontend polls `/api/sync/output` every 1s during sync

### SQL Views
- `CREATE OR REPLACE VIEW` — idempotent
- `LEFT JOIN` for optional relations
- Keep column names descriptive for Power BI auto-detection

### Security
- `.env` is gitignored — never commit credentials
- Use Odoo **API Keys** for XML-RPC
- `powerbi_reader` PG role: SELECT-only
- `bi_user` PG role: owns tables, runs ETL
- Portal has no auth by default — add if exposed to internet

---

## Environment Configuration (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `ODOO_URL` | Odoo.sh instance URL | `https://mycompany.odoo.com` |
| `ODOO_DB` | Odoo database name | — |
| `ODOO_USER` | Odoo username | `admin` |
| `ODOO_PASSWORD` | API Key (recommended) | — |
| `PG_HOST` | PostgreSQL host | `127.0.0.1` |
| `PG_PORT` | PostgreSQL port | `5432` |
| `PG_DB` | Target database | `odoo_bi` |
| `PG_USER` | PostgreSQL user (ETL) | `bi_user` |
| `PG_PASSWORD` | PostgreSQL password | — |
| `ETL_BATCH_SIZE` | Records per XML-RPC call | `500` |
| `ETL_MAX_RECORDS` | Max per model (0=unlimited) | `0` |
| `ETL_LOG_LEVEL` | Logging level | `INFO` |

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ConnectionError: No se pudo autenticar` | Check `ODOO_*` in `.env`. Use API Key. |
| Model skipped ("no existe") | Module not installed on Odoo.sh. Set `enabled: False` or install it. |
| `psycopg2.OperationalError` | PostgreSQL not running or wrong `PG_*` creds. |
| Slow sync | Reduce `ETL_BATCH_SIZE`. Run full sync off-peak. |
| Power BI can't connect | Firewall port 5432. Check `pg_hba.conf`. Use `powerbi_reader`. |
| Stale data | Check `bi_sync_status` view or portal dashboard. Verify cron/timer. |
| Portal won't start | `pip install flask gunicorn`. Check port 8050 not in use. |

---

## Notes for AI Assistants

- **Read before edit**: Always read existing files before modifying them.
- **Credentials**: Never hardcode. Always use `.env` / environment variables.
- **Incremental sync**: Tracks `write_date` per model in `etl_sync_log`.
- **Many2one fields**: Stored as integer IDs. Join in SQL views for names.
- **One2many / Many2many**: Not synced. Create dedicated model entries if needed.
- **Portal is NOT an Odoo module**: It's an independent Flask app. Don't mix Odoo ORM.
- **Testing**: Run `python run_sync.py --list` (no connection needed). For portal: `python run_portal.py`.
- **Power BI views**: Keep in `sql/create_bi_views.sql`. Use `CREATE OR REPLACE VIEW` + `LEFT JOIN`.
- **POS models**: `report.pos.order` uses `incremental: False` because it's a SQL view in Odoo with no `write_date`.
