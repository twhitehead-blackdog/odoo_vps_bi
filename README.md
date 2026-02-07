# Odoo VPS BI

ETL que sincroniza datos de **Odoo.sh** a **PostgreSQL** local en un VPS cada 15 minutos, para consumirlos desde **Power BI**.

## Arquitectura

```
┌──────────────┐    XML-RPC     ┌──────────────┐    DirectQuery    ┌──────────────┐
│   Odoo.sh    │ ──────────────→│  PostgreSQL   │ ←────────────────│   Power BI   │
│  (origen)    │   cada 15 min  │  VPS (local)  │                  │  (reportes)  │
└──────────────┘                └──────────────┘                   └──────────────┘
```

## Modelos sincronizados

| Área | Modelos |
|------|---------|
| Maestros | `res.partner`, `res.company`, `res.currency`, `res.users` |
| Productos | `product.product`, `product.template`, `product.category` |
| Ventas | `sale.order`, `sale.order.line` |
| Compras | `purchase.order`, `purchase.order.line` |
| Contabilidad | `account.move`, `account.move.line`, `account.account`, `account.payment` |
| Inventario | `stock.picking`, `stock.move`, `stock.quant`, `stock.warehouse`, `stock.location` |
| CRM | `crm.lead`, `crm.stage` |
| RRHH | `hr.employee`, `hr.department` |
| POS | `pos.order`, `pos.order.line` |

## Inicio rápido

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

### 4. Primera ejecución (carga completa)

```bash
# Verificar modelos configurados
python run_sync.py --list

# Ejecutar carga completa
python run_sync.py --full

# Crear vistas para Power BI
psql -U bi_user -d odoo_bi -f sql/create_bi_views.sql
```

### 5. Programar ejecución cada 15 minutos

```bash
# Opción A: cron
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh

# Opción B: systemd timer (recomendado)
sudo ./scripts/setup_systemd.sh
```

### 6. Conectar Power BI

En Power BI Desktop:
1. **Obtener datos** → **Base de datos PostgreSQL**
2. Servidor: `tu-vps-ip:5432`
3. Base de datos: `odoo_bi`
4. Usuario: `powerbi_reader`
5. Usar las vistas `bi_*` (bi_ventas, bi_compras, bi_facturas, etc.)

## Comandos

```bash
# Sync incremental (solo cambios)
python run_sync.py

# Sync completa
python run_sync.py --full

# Solo ciertos modelos
python run_sync.py --models sale.order sale.order.line

# Ver modelos configurados
python run_sync.py --list

# Inspeccionar campos de un modelo en Odoo
python run_sync.py --inspect sale.order
```

## Estructura del proyecto

```
odoo_vps_bi/
├── run_sync.py            # Punto de entrada CLI
├── config/
│   ├── settings.py        # Configuración (lee de .env)
│   └── models.py          # Definición de modelos a sincronizar
├── etl/
│   ├── odoo_client.py     # Cliente XML-RPC para Odoo
│   ├── pg_loader.py       # Carga a PostgreSQL (upsert)
│   └── sync.py            # Orquestador de sincronización
├── sql/
│   ├── init_database.sql  # Crear BD y usuarios
│   └── create_bi_views.sql# Vistas desnormalizadas para Power BI
├── scripts/
│   ├── setup_cron.sh      # Configurar cron cada 15 min
│   ├── setup_systemd.sh   # Configurar timer systemd
│   └── full_reset.sh      # Reset y carga desde cero
├── .env.example            # Plantilla de configuración
└── requirements.txt        # Dependencias Python
```

## Personalización

### Agregar un nuevo modelo

Editar `config/models.py` y agregar una entrada al dict `MODELS`:

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
