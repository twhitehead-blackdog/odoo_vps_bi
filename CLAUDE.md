# CLAUDE.md — AI Assistant Guide for odoo_vps_bi

## Project Overview

**odoo_vps_bi** is an ETL pipeline that synchronizes data from **Odoo.sh** (via XML-RPC) into a local **PostgreSQL** database on a VPS, refreshed every 15 minutes, for consumption by **Power BI**.

```
Odoo.sh  ──XML-RPC──→  ETL (Python)  ──UPSERT──→  PostgreSQL VPS  ←──DirectQuery──  Power BI
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Data source | Odoo.sh (XML-RPC API) |
| ETL | Python 3.8+ (stdlib `xmlrpc.client` + `psycopg2`) |
| Database | PostgreSQL 12+ |
| Scheduling | cron or systemd timer (every 15 min) |
| BI Frontend | Power BI (DirectQuery or Import) |

---

## Project Structure

```
odoo_vps_bi/
├── CLAUDE.md               # This file — AI assistant guide
├── README.md               # Setup instructions and usage
├── run_sync.py             # CLI entry point for the ETL
├── requirements.txt        # Python dependencies (psycopg2-binary)
├── .env.example            # Template for credentials
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── settings.py         # Reads .env, exposes all config constants
│   └── models.py           # Defines which Odoo models/fields to sync
├── etl/
│   ├── __init__.py
│   ├── odoo_client.py      # XML-RPC client with batched reads
│   ├── pg_loader.py        # Dynamic table creation + UPSERT logic
│   └── sync.py             # Orchestrator: incremental & full sync
├── sql/
│   ├── init_database.sql   # Create DB, users, permissions
│   └── create_bi_views.sql # Denormalized views for Power BI
├── scripts/
│   ├── setup_cron.sh       # Install cron job (every 15 min)
│   ├── setup_systemd.sh    # Install systemd timer (alternative)
│   └── full_reset.sh       # Drop all & reload from scratch
└── logs/                   # Created at runtime (gitignored)
```

---

## Key Files — What They Do

### `config/settings.py`
Central configuration. Reads from `.env` file (or environment variables). Contains:
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` — Odoo.sh connection
- `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASSWORD` — PostgreSQL connection
- `BATCH_SIZE` — records per XML-RPC call (default 500)
- `LOG_LEVEL` — logging verbosity

### `config/models.py`
Defines all Odoo models to sync as a list of dicts. Each entry specifies:
- `odoo_model` / `pg_table` — source model → target table
- `fields` — explicit field list (Many2one stored as integer ID)
- `domain` — Odoo domain filter
- `incremental` — if True, only fetches records changed since last sync
- `priority` — execution order (lower = first; masters before transactional)

### `etl/odoo_client.py`
XML-RPC wrapper. Key method: `read_batched()` — generator that yields batches of records, handling pagination automatically.

### `etl/pg_loader.py`
- `ensure_table()` — creates tables dynamically from first batch (infers PG types)
- `upsert_batch()` — `INSERT ... ON CONFLICT (id) DO UPDATE` for idempotent loads
- `etl_sync_log` — tracks last sync timestamp per model for incremental logic

### `etl/sync.py`
Orchestrates the full pipeline. `run_sync()` iterates enabled models, applies incremental domain filter (`write_date >= last_sync`), and returns a summary dict.

### `sql/create_bi_views.sql`
Pre-built denormalized views for Power BI:
- `bi_ventas` — sales orders + lines + partner + product
- `bi_compras` — purchase orders + lines
- `bi_facturas` — invoices with partner/journal
- `bi_apuntes_contables` — journal items with account details
- `bi_crm` — CRM pipeline with stages
- `bi_inventario` — current stock (quants) with product/location
- `bi_pagos` — payments with partner/journal
- `bi_sync_status` — ETL health monitoring

---

## Synced Odoo Models (28 models)

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
| 60 | POS | `pos.order`, `pos.order.line` |

Models that don't exist in the Odoo instance are automatically skipped.

---

## Common Commands

```bash
# Incremental sync (normal, every 15 min via cron)
python run_sync.py

# Full sync (first time or reset)
python run_sync.py --full

# Sync specific models only
python run_sync.py --models sale.order account.move

# List configured models
python run_sync.py --list

# Inspect available fields on an Odoo model
python run_sync.py --inspect sale.order

# Full reset (drop all tables, reload, recreate views)
./scripts/full_reset.sh
```

---

## Development Conventions

### Python Style
- PEP 8
- No external dependencies beyond `psycopg2-binary` (uses stdlib `xmlrpc.client`)
- All credentials via environment variables / `.env` — never hardcoded
- Logging via stdlib `logging` — structured messages at INFO level

### Adding a New Model
1. Add entry to `config/models.py` → `MODELS` list
2. Tables are created automatically on first sync
3. Optionally add a `bi_*` view in `sql/create_bi_views.sql`

### SQL Views
- Views in `sql/create_bi_views.sql` are idempotent (`CREATE OR REPLACE`)
- Use `LEFT JOIN` to handle missing related records gracefully
- Keep column names descriptive for Power BI auto-detection

### Security
- `.env` is gitignored — never commit credentials
- Use Odoo **API Keys** (not passwords) for the XML-RPC connection
- The `powerbi_reader` PostgreSQL role has SELECT-only access
- The `bi_user` role owns the tables and runs the ETL

---

## Environment Configuration (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `ODOO_URL` | Odoo.sh instance URL | `https://mycompany.odoo.com` |
| `ODOO_DB` | Odoo database name | — |
| `ODOO_USER` | Odoo username | `admin` |
| `ODOO_PASSWORD` | API Key (recommended) or password | — |
| `PG_HOST` | PostgreSQL host | `127.0.0.1` |
| `PG_PORT` | PostgreSQL port | `5432` |
| `PG_DB` | Target database name | `odoo_bi` |
| `PG_USER` | PostgreSQL user (ETL) | `bi_user` |
| `PG_PASSWORD` | PostgreSQL password | — |
| `ETL_BATCH_SIZE` | Records per XML-RPC call | `500` |
| `ETL_MAX_RECORDS` | Max records per model (0=unlimited) | `0` |
| `ETL_LOG_LEVEL` | Logging level | `INFO` |

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ConnectionError: No se pudo autenticar` | Check `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` in `.env`. Use API Key. |
| Model skipped ("no existe en Odoo") | The module is not installed on Odoo.sh. Set `enabled: False` in `config/models.py` or install the module. |
| `psycopg2.OperationalError: connection refused` | PostgreSQL not running or wrong `PG_*` credentials. Check `systemctl status postgresql`. |
| Slow sync | Reduce `ETL_BATCH_SIZE`. Check Odoo.sh plan limits. Consider running full sync off-peak. |
| Power BI can't connect | Ensure VPS firewall allows port 5432. Check `pg_hba.conf` for remote access. Use `powerbi_reader` user. |
| Stale data | Check `bi_sync_status` view. Verify cron is running: `crontab -l` or `systemctl status odoo-bi-sync.timer`. |
| Missing columns after Odoo update | Run `--full` once to auto-add new columns via `ensure_table()`. |

---

## Notes for AI Assistants

- **Read before edit**: Always read existing files before modifying them.
- **Credentials**: Never hardcode. Always use `.env` / environment variables.
- **Incremental sync**: The system tracks `write_date` per model in `etl_sync_log`. Respect this pattern when adding models.
- **Many2one fields**: Stored as integer IDs. To get the name, join in SQL views.
- **One2many / Many2many**: Not synced (would require separate join tables). If needed, create a dedicated model entry.
- **Testing**: No Odoo instance is available locally. Test by running `python run_sync.py --list` (no connection needed) or mock the XML-RPC calls.
- **Power BI views**: Keep them in `sql/create_bi_views.sql`. Always use `CREATE OR REPLACE VIEW`. Use `LEFT JOIN` for optional relations.
