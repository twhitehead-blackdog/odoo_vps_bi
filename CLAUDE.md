# CLAUDE.md — AI Assistant Guide for odoo_vps_bi

## Project Overview

**odoo_vps_bi** is a Business Intelligence (BI) project built around Odoo, designed to run on a VPS environment. This repository is in its initial setup phase — no application code has been committed yet.

### Repository Status

- **State**: Newly initialized, empty repository
- **Remote**: Hosted via local proxy at `127.0.0.1:40632`
- **Primary branch**: Not yet established (no commits)

---

## Expected Technology Stack

Based on the project name and Odoo ecosystem conventions:

| Layer | Technology |
|---|---|
| ERP / Backend | Odoo (Python) |
| Database | PostgreSQL |
| Frontend | Odoo QWeb templates, JavaScript (OWL framework in Odoo 17+) |
| Deployment | VPS (likely Docker or direct install) |
| BI / Reporting | Odoo reporting, custom BI modules, or external tools |

---

## Project Structure (Planned)

When code is added, an Odoo project typically follows this layout:

```
odoo_vps_bi/
├── CLAUDE.md              # This file — AI assistant guide
├── README.md              # Project overview and setup instructions
├── docker-compose.yml     # Container orchestration (if using Docker)
├── Dockerfile             # Odoo container definition
├── requirements.txt       # Python dependencies
├── config/
│   └── odoo.conf          # Odoo server configuration
├── addons/                # Custom Odoo modules
│   └── bi_module/         # Example BI module
│       ├── __init__.py
│       ├── __manifest__.py
│       ├── models/
│       ├── views/
│       ├── security/
│       ├── data/
│       ├── reports/
│       └── static/
├── scripts/               # Utility and deployment scripts
└── tests/                 # Integration/unit tests
```

---

## Development Conventions

### Odoo Module Structure

Each custom module should follow Odoo's standard layout:

- `__manifest__.py` — Module metadata (name, version, dependencies, data files)
- `__init__.py` — Python package initialization
- `models/` — Business logic and ORM model definitions
- `views/` — XML view definitions (form, tree, kanban, etc.)
- `security/` — Access control (ir.model.access.csv, record rules)
- `data/` — Default/demo data XML files
- `reports/` — QWeb report templates
- `static/` — Frontend assets (JS, CSS, images)
- `wizard/` — Transient models for user wizards
- `controllers/` — HTTP route handlers

### Python Style

- Follow PEP 8
- Use Odoo's ORM API (v13+ new API style with `self` as recordset)
- Avoid raw SQL unless strictly necessary for BI performance
- Use `_inherit` for extending existing models, `_name` for new ones
- Keep business logic in model methods, not in controllers or views

### Naming Conventions

- **Module names**: lowercase with underscores (e.g., `bi_dashboard`, `vps_analytics`)
- **Model names**: dotted notation (e.g., `bi.report`, `bi.kpi.metric`)
- **XML IDs**: `module_name.descriptive_id` (e.g., `bi_dashboard.view_report_form`)
- **Python files**: lowercase with underscores matching model names

### Security

- Always define access control in `security/ir.model.access.csv`
- Use record rules for row-level security when needed
- Never hardcode credentials — use `odoo.conf` or environment variables
- Sanitize any user input used in raw SQL queries

---

## Common Commands

### Odoo Server

```bash
# Start Odoo (direct install)
python odoo-bin -c config/odoo.conf

# Start with specific addons path
python odoo-bin -c config/odoo.conf --addons-path=addons

# Update a specific module
python odoo-bin -c config/odoo.conf -u bi_module -d <database_name>

# Install a module
python odoo-bin -c config/odoo.conf -i bi_module -d <database_name>
```

### Docker (if applicable)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f odoo

# Restart Odoo
docker-compose restart odoo

# Access Odoo shell
docker-compose exec odoo odoo shell -d <database_name>
```

### Testing

```bash
# Run tests for a specific module
python odoo-bin -c config/odoo.conf --test-enable --stop-after-init -i bi_module -d test_db

# Run tests in Docker
docker-compose exec odoo odoo --test-enable --stop-after-init -u bi_module -d test_db
```

### Database

```bash
# PostgreSQL access
psql -U odoo -d <database_name>

# Backup
pg_dump -U odoo <database_name> > backup.sql

# Restore
psql -U odoo <database_name> < backup.sql
```

---

## BI-Specific Guidelines

### Reporting and Dashboards

- Use Odoo's built-in reporting engine (QWeb PDF reports) for standard reports
- For custom BI dashboards, create dedicated view types or use `ir.actions.act_window` with custom views
- Consider using PostgreSQL materialized views for complex aggregations
- Cache expensive queries and refresh on a schedule

### Data Models for BI

- Use `_auto = False` with custom `init()` for SQL-based report models
- Example pattern for a BI report model:

```python
from odoo import models, fields

class BiSalesReport(models.Model):
    _name = 'bi.sales.report'
    _description = 'Sales BI Report'
    _auto = False
    _order = 'date desc'

    date = fields.Date(readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    total_amount = fields.Float(readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW bi_sales_report AS (
                SELECT
                    row_number() OVER () AS id,
                    so.date_order::date AS date,
                    sol.product_id,
                    SUM(sol.price_subtotal) AS total_amount
                FROM sale_order_line sol
                JOIN sale_order so ON so.id = sol.order_id
                WHERE so.state IN ('sale', 'done')
                GROUP BY so.date_order::date, sol.product_id
            )
        """)
```

### Performance Considerations

- Index frequently filtered/grouped columns in BI queries
- Use `read_group()` for aggregated data instead of loading full recordsets
- Limit dashboard data to reasonable date ranges
- Use `fields.Date.context_today()` for timezone-aware date handling

---

## Git Workflow

- Use feature branches prefixed with a descriptive name
- Write clear, descriptive commit messages
- Keep commits atomic — one logical change per commit
- Do not commit secrets, credentials, or `.env` files

---

## Environment Configuration

Key settings typically managed via `odoo.conf` or environment variables:

| Setting | Description |
|---|---|
| `db_host` | PostgreSQL host |
| `db_port` | PostgreSQL port (default: 5432) |
| `db_user` | Database user |
| `db_password` | Database password |
| `addons_path` | Comma-separated paths to addon directories |
| `data_dir` | Odoo data/filestore directory |
| `http_port` | Web server port (default: 8069) |
| `admin_passwd` | Master password for database management |

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Module not found | Check `addons_path` in `odoo.conf` includes your custom addons directory |
| Access denied errors | Verify `security/ir.model.access.csv` entries and record rules |
| Slow BI queries | Check PostgreSQL `EXPLAIN ANALYZE` output; add indexes |
| View inheritance errors | Verify `inherit_id` XML references and module dependencies in `__manifest__.py` |
| Assets not loading | Run `odoo-bin -u base -d <db>` to regenerate assets |

---

## Notes for AI Assistants

- This repository is newly initialized. When adding code, follow the conventions above.
- Always read existing files before modifying them.
- When creating Odoo modules, include all required files (`__manifest__.py`, `__init__.py`, security definitions).
- Test module installation with `--test-enable` before considering work complete.
- Keep BI queries efficient — prefer SQL views and `read_group()` over loading full recordsets.
- Update this CLAUDE.md as the project structure evolves.
