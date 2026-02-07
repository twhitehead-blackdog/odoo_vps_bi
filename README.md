# Odoo VPS BI

ETL que sincroniza datos de **Odoo.sh** a **PostgreSQL** local en un VPS cada 15 minutos, para consumirlos desde **Power BI**. Incluye un **portal web** independiente para monitorear y gestionar la sincronizacion.

## Arquitectura

```
┌──────────────┐    XML-RPC     ┌──────────────┐    DirectQuery    ┌──────────────┐
│   Odoo.sh    │ ──────────────→│  PostgreSQL   │ ←────────────────│   Power BI   │
│  (origen)    │   cada 15 min  │  VPS (local)  │                  │  (reportes)  │
└──────────────┘                └──────────────┘                   └──────────────┘
                                       ↑
                                ┌──────────────┐
                                │  Portal Web  │
                                │  (Flask:8050)│
                                └──────────────┘
```

## Modelos sincronizados

| Area | Modelos |
|------|---------|
| Maestros | `res.partner`, `res.company`, `res.currency`, `res.users`, `res.country` |
| Productos | `product.product`, `product.template`, `product.category`, `uom.uom` |
| Ventas | `sale.order`, `sale.order.line` |
| Compras | `purchase.order`, `purchase.order.line` |
| Contabilidad | `account.move`, `account.move.line`, `account.account`, `account.payment` |
| Inventario | `stock.picking`, `stock.move`, `stock.quant`, `stock.warehouse`, `stock.location` |
| CRM | `crm.lead`, `crm.stage` |
| RRHH | `hr.employee`, `hr.department` |
| POS | `pos.order`, `pos.order.line`, `pos.payment`, `pos.session`, `pos.config`, `pos.payment.method`, `report.pos.order` |

## Inicio rapido

### 1. Requisitos

- Python 3.8+
- PostgreSQL 12+
- Acceso XML-RPC a tu instancia Odoo.sh (usuario con API Key)

### 2. Instalar

```bash
git clone <repo-url> && cd odoo_vps_bi
pip install -r requirements.txt
```

### 3. Configurar

```bash
# Crear base de datos PostgreSQL
sudo -u postgres psql -f sql/init_database.sql

# Configurar credenciales
cp .env.example .env
nano .env   # Rellenar con tus datos
```

### 4. Primera ejecucion (carga completa)

```bash
# Verificar modelos configurados
python run_sync.py --list

# Ejecutar carga completa
python run_sync.py --full

# Crear vistas para Power BI
psql -U bi_user -d odoo_bi -f sql/create_bi_views.sql
```

### 5. Programar ejecucion cada 15 minutos

```bash
# Opcion A: cron
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh

# Opcion B: systemd timer (recomendado)
sudo ./scripts/setup_systemd.sh
```

### 6. Iniciar el portal web

```bash
# Desarrollo
python run_portal.py

# Produccion (con gunicorn)
gunicorn -w 2 -b 0.0.0.0:8050 portal.app:app

# Como servicio systemd
sudo ./scripts/setup_portal_systemd.sh
```

Acceder a `http://tu-vps-ip:8050`

### 7. Conectar Power BI

En Power BI Desktop:
1. **Obtener datos** > **Base de datos PostgreSQL**
2. Servidor: `tu-vps-ip:5432`
3. Base de datos: `odoo_bi`
4. Usuario: `powerbi_reader`
5. Usar las vistas `bi_*` (bi_ventas, bi_compras, bi_facturas, bi_pos_ventas, etc.)

## Portal Web

El portal (puerto 8050) es una app Flask independiente que permite:

- **Dashboard**: KPIs, estado de cada modelo, ultima sync, errores
- **Modelos**: lista completa agrupada por area, busqueda, ver campos y datos
- **Detalle de modelo**: columnas PostgreSQL, preview de datos, estado de sync
- **Logs**: visualizacion en tiempo real de logs del ETL
- **Sync remoto**: lanzar sincronizacion (incremental o completa) desde el navegador
- **API JSON**: endpoints en `/api/` para integracion programatica

### API Endpoints

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/status` | GET | Estado general del sistema |
| `/api/models` | GET | Lista de modelos con estado |
| `/api/sync/start` | POST | Iniciar sync (`{"full": true, "models": [...]}`) |
| `/api/sync/status` | GET | Estado del sync en curso |
| `/api/sync/output` | GET | Salida en vivo del sync |
| `/api/table/<name>/count` | GET | Conteo de filas de una tabla |

## Comandos ETL

```bash
# Sync incremental (solo cambios)
python run_sync.py

# Sync completa
python run_sync.py --full

# Solo ciertos modelos
python run_sync.py --models sale.order pos.order report.pos.order

# Ver modelos configurados
python run_sync.py --list

# Inspeccionar campos de un modelo en Odoo
python run_sync.py --inspect pos.order
```

## Estructura del proyecto

```
odoo_vps_bi/
├── run_sync.py              # CLI del ETL
├── run_portal.py            # Punto de entrada del portal web
├── config/
│   ├── settings.py          # Configuracion (lee de .env)
│   └── models.py            # Modelos a sincronizar (35 modelos)
├── etl/
│   ├── odoo_client.py       # Cliente XML-RPC para Odoo
│   ├── pg_loader.py         # Carga a PostgreSQL (upsert)
│   └── sync.py              # Orquestador de sincronizacion
├── portal/
│   ├── app.py               # App Flask (rutas, API, helpers)
│   ├── templates/            # HTML (Jinja2 + Bootstrap 5)
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── models.html
│   │   ├── model_detail.html
│   │   └── logs.html
│   └── static/
│       ├── css/portal.css
│       └── js/portal.js
├── sql/
│   ├── init_database.sql    # Crear BD y usuarios
│   └── create_bi_views.sql  # 10 vistas para Power BI
├── scripts/
│   ├── setup_cron.sh        # Cron cada 15 min
│   ├── setup_systemd.sh     # Timer systemd para ETL
│   ├── setup_portal_systemd.sh  # Servicio systemd para portal
│   └── full_reset.sh        # Reset completo
├── .env.example
├── .gitignore
└── requirements.txt         # psycopg2-binary, flask, gunicorn
```

## Personalizacion

### Agregar un nuevo modelo

Editar `config/models.py` y agregar una entrada a `MODELS`:

```python
{
    "odoo_model": "mi.modelo",
    "pg_table": "mi_modelo",
    "fields": ["id", "name", "campo1", "campo2", "write_date"],
    "domain": [],
    "incremental": True,
    "enabled": True,
    "priority": 50,
},
```

### Agregar una vista para Power BI

Agregar al archivo `sql/create_bi_views.sql` y ejecutar:

```bash
psql -U bi_user -d odoo_bi -f sql/create_bi_views.sql
```
