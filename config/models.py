"""
Definición de todos los modelos de Odoo a sincronizar.

Cada entrada define:
  - odoo_model:   nombre técnico del modelo en Odoo (e.g. "sale.order")
  - pg_table:     nombre de la tabla destino en PostgreSQL
  - fields:       lista de campos a extraer ([] = todos los campos del modelo)
  - domain:       filtro Odoo para limitar registros ([] = todos)
  - incremental:  si True, solo trae registros modificados desde la última sync
  - enabled:      si False, se omite en la sincronización
  - priority:     orden de ejecución (menor = primero). Modelos base primero.

IMPORTANTE: Los campos Many2one se almacenan como integer (ID).
            Los campos One2many/Many2many se omiten por defecto.
"""

MODELS = [
    # =======================================================================
    #  MAESTROS / CONFIGURACIÓN  (priority 1)
    # =======================================================================
    {
        "odoo_model": "res.company",
        "pg_table": "res_company",
        "fields": [
            "id", "name", "currency_id", "partner_id",
            "street", "city", "country_id", "vat",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },
    {
        "odoo_model": "res.currency",
        "pg_table": "res_currency",
        "fields": [
            "id", "name", "symbol", "active", "rate",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },
    {
        "odoo_model": "res.currency.rate",
        "pg_table": "res_currency_rate",
        "fields": [
            "id", "name", "rate", "currency_id", "company_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },
    {
        "odoo_model": "res.country",
        "pg_table": "res_country",
        "fields": [
            "id", "name", "code",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },
    {
        "odoo_model": "res.country.state",
        "pg_table": "res_country_state",
        "fields": [
            "id", "name", "code", "country_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },
    {
        "odoo_model": "res.users",
        "pg_table": "res_users",
        "fields": [
            "id", "name", "login", "active", "company_id",
            "partner_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },
    {
        "odoo_model": "account.journal",
        "pg_table": "account_journal",
        "fields": [
            "id", "name", "code", "type", "company_id",
            "currency_id", "active",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 1,
    },

    # =======================================================================
    #  CONTACTOS  (priority 2)
    # =======================================================================
    {
        "odoo_model": "res.partner",
        "pg_table": "res_partner",
        "fields": [
            "id", "name", "display_name", "ref", "vat",
            "email", "phone", "mobile",
            "street", "street2", "city", "state_id", "zip",
            "country_id", "company_id",
            "is_company", "customer_rank", "supplier_rank",
            "active", "type", "parent_id",
            "commercial_partner_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 2,
    },

    # =======================================================================
    #  PRODUCTOS  (priority 3)
    # =======================================================================
    {
        "odoo_model": "product.category",
        "pg_table": "product_category",
        "fields": [
            "id", "name", "complete_name", "parent_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 3,
    },
    {
        "odoo_model": "product.template",
        "pg_table": "product_template",
        "fields": [
            "id", "name", "default_code", "type",
            "categ_id", "list_price", "standard_price",
            "uom_id", "active", "sale_ok", "purchase_ok",
            "company_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 3,
    },
    {
        "odoo_model": "product.product",
        "pg_table": "product_product",
        "fields": [
            "id", "default_code", "barcode", "active",
            "product_tmpl_id", "combination_indices",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 3,
    },
    {
        "odoo_model": "uom.uom",
        "pg_table": "uom_uom",
        "fields": [
            "id", "name", "category_id", "factor", "uom_type",
            "active",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 3,
    },

    # =======================================================================
    #  VENTAS  (priority 10)
    # =======================================================================
    {
        "odoo_model": "sale.order",
        "pg_table": "sale_order",
        "fields": [
            "id", "name", "state", "date_order", "commitment_date",
            "partner_id", "partner_invoice_id", "partner_shipping_id",
            "pricelist_id", "currency_id",
            "user_id", "team_id", "company_id",
            "amount_untaxed", "amount_tax", "amount_total",
            "invoice_status", "delivery_status",
            "origin", "client_order_ref",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 10,
    },
    {
        "odoo_model": "sale.order.line",
        "pg_table": "sale_order_line",
        "fields": [
            "id", "order_id", "sequence", "product_id",
            "product_template_id", "name",
            "product_uom_qty", "qty_delivered", "qty_invoiced",
            "product_uom", "price_unit", "discount",
            "price_subtotal", "price_tax", "price_total",
            "currency_id", "company_id",
            "salesman_id", "state",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 10,
    },

    # =======================================================================
    #  COMPRAS  (priority 11)
    # =======================================================================
    {
        "odoo_model": "purchase.order",
        "pg_table": "purchase_order",
        "fields": [
            "id", "name", "state", "date_order", "date_approve",
            "date_planned",
            "partner_id", "currency_id",
            "user_id", "company_id",
            "amount_untaxed", "amount_tax", "amount_total",
            "invoice_status",
            "origin",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 11,
    },
    {
        "odoo_model": "purchase.order.line",
        "pg_table": "purchase_order_line",
        "fields": [
            "id", "order_id", "sequence", "product_id",
            "name", "product_qty", "qty_received", "qty_invoiced",
            "product_uom", "price_unit",
            "price_subtotal", "price_tax", "price_total",
            "currency_id", "company_id",
            "partner_id", "state",
            "date_planned",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 11,
    },

    # =======================================================================
    #  CONTABILIDAD / FACTURACIÓN  (priority 20)
    # =======================================================================
    {
        "odoo_model": "account.move",
        "pg_table": "account_move",
        "fields": [
            "id", "name", "state", "move_type",
            "date", "invoice_date", "invoice_date_due",
            "partner_id", "commercial_partner_id",
            "journal_id", "company_id", "currency_id",
            "amount_untaxed", "amount_tax", "amount_total",
            "amount_residual", "amount_untaxed_signed",
            "amount_total_signed", "amount_residual_signed",
            "payment_state", "invoice_origin",
            "ref", "narration",
            "invoice_user_id", "team_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 20,
    },
    {
        "odoo_model": "account.move.line",
        "pg_table": "account_move_line",
        "fields": [
            "id", "move_id", "move_name", "sequence",
            "account_id", "journal_id", "company_id",
            "currency_id", "partner_id",
            "product_id", "product_uom_id",
            "name", "quantity", "price_unit",
            "discount", "debit", "credit", "balance",
            "amount_currency", "amount_residual",
            "date", "date_maturity",
            "parent_state",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 20,
    },
    {
        "odoo_model": "account.account",
        "pg_table": "account_account",
        "fields": [
            "id", "code", "name", "account_type",
            "company_id", "currency_id",
            "deprecated", "reconcile",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 20,
    },

    # =======================================================================
    #  PAGOS  (priority 21)
    # =======================================================================
    {
        "odoo_model": "account.payment",
        "pg_table": "account_payment",
        "fields": [
            "id", "name", "state", "payment_type",
            "partner_type", "partner_id",
            "amount", "currency_id", "company_id",
            "journal_id", "date",
            "ref", "move_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 21,
    },

    # =======================================================================
    #  INVENTARIO  (priority 30)
    # =======================================================================
    {
        "odoo_model": "stock.warehouse",
        "pg_table": "stock_warehouse",
        "fields": [
            "id", "name", "code", "company_id", "partner_id",
            "active",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 30,
    },
    {
        "odoo_model": "stock.location",
        "pg_table": "stock_location",
        "fields": [
            "id", "name", "complete_name", "usage",
            "location_id", "company_id", "warehouse_id",
            "active",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 30,
    },
    {
        "odoo_model": "stock.picking",
        "pg_table": "stock_picking",
        "fields": [
            "id", "name", "state", "origin",
            "picking_type_id", "location_id", "location_dest_id",
            "partner_id", "company_id",
            "scheduled_date", "date_done",
            "sale_id", "purchase_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 30,
    },
    {
        "odoo_model": "stock.move",
        "pg_table": "stock_move",
        "fields": [
            "id", "name", "state", "origin",
            "product_id", "product_uom_qty", "quantity_done",
            "product_uom", "location_id", "location_dest_id",
            "picking_id", "company_id",
            "sale_line_id", "purchase_line_id",
            "price_unit", "date",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 30,
    },
    {
        "odoo_model": "stock.quant",
        "pg_table": "stock_quant",
        "fields": [
            "id", "product_id", "location_id", "lot_id",
            "quantity", "reserved_quantity",
            "company_id",
            "in_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 30,
    },

    # =======================================================================
    #  CRM  (priority 40)
    # =======================================================================
    {
        "odoo_model": "crm.lead",
        "pg_table": "crm_lead",
        "fields": [
            "id", "name", "type", "active",
            "stage_id", "partner_id", "company_id",
            "user_id", "team_id",
            "expected_revenue", "probability",
            "date_deadline", "date_closed",
            "date_open", "date_last_stage_update",
            "source_id", "medium_id", "campaign_id",
            "city", "state_id", "country_id",
            "lost_reason_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 40,
    },
    {
        "odoo_model": "crm.stage",
        "pg_table": "crm_stage",
        "fields": [
            "id", "name", "sequence", "is_won",
            "team_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 40,
    },

    # =======================================================================
    #  RRHH  (priority 50) — habilitado solo si el módulo está instalado
    # =======================================================================
    {
        "odoo_model": "hr.employee",
        "pg_table": "hr_employee",
        "fields": [
            "id", "name", "job_id", "job_title",
            "department_id", "parent_id", "company_id",
            "work_email", "work_phone",
            "active",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 50,
    },
    {
        "odoo_model": "hr.department",
        "pg_table": "hr_department",
        "fields": [
            "id", "name", "complete_name",
            "parent_id", "company_id", "manager_id",
            "active",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 50,
    },

    # =======================================================================
    #  POS — Punto de Venta  (priority 60)
    # =======================================================================
    {
        "odoo_model": "pos.session",
        "pg_table": "pos_session",
        "fields": [
            "id", "name", "state", "config_id",
            "user_id", "company_id",
            "start_at", "stop_at",
            "cash_register_balance_start", "cash_register_balance_end_real",
            "total_payments_amount", "order_count",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 60,
    },
    {
        "odoo_model": "pos.config",
        "pg_table": "pos_config",
        "fields": [
            "id", "name", "active", "company_id",
            "warehouse_id", "pricelist_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 60,
    },
    {
        "odoo_model": "pos.payment.method",
        "pg_table": "pos_payment_method",
        "fields": [
            "id", "name", "is_cash_count", "active",
            "company_id", "journal_id",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 60,
    },
    {
        "odoo_model": "pos.order",
        "pg_table": "pos_order",
        "fields": [
            "id", "name", "state", "date_order",
            "partner_id", "session_id", "config_id",
            "company_id", "user_id", "employee_id",
            "pricelist_id", "currency_id",
            "amount_total", "amount_tax", "amount_paid",
            "amount_return",
            "pos_reference", "note",
            "is_invoiced", "account_move",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 61,
    },
    {
        "odoo_model": "pos.order.line",
        "pg_table": "pos_order_line",
        "fields": [
            "id", "order_id", "product_id", "product_uom_id",
            "name", "full_product_name",
            "qty", "price_unit", "price_cost",
            "discount", "price_subtotal", "price_subtotal_incl",
            "company_id", "currency_id",
            "create_date", "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 61,
    },
    {
        "odoo_model": "pos.payment",
        "pg_table": "pos_payment",
        "fields": [
            "id", "name", "pos_order_id", "amount",
            "payment_method_id", "session_id",
            "company_id", "currency_id",
            "payment_date",
            "write_date",
        ],
        "domain": [],
        "incremental": True,
        "enabled": True,
        "priority": 61,
    },
    {
        "odoo_model": "report.pos.order",
        "pg_table": "report_pos_order",
        "fields": [
            "id", "date", "order_id", "partner_id",
            "product_id", "product_tmpl_id", "state",
            "user_id", "company_id", "session_id",
            "config_id",
            "price_total", "price_sub_total",
            "total_discount", "average_price",
            "product_qty", "nbr_lines",
            "delay_validation",
        ],
        "domain": [],
        "incremental": False,
        "enabled": True,
        "priority": 62,
    },
]


def get_enabled_models():
    """Retorna solo los modelos habilitados, ordenados por prioridad."""
    return sorted(
        [m for m in MODELS if m.get("enabled", True)],
        key=lambda m: m.get("priority", 99),
    )
