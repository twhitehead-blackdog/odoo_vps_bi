-- ============================================================================
-- Vistas SQL para Power BI
--
-- Estas vistas desnormalizan los datos sincronizados desde Odoo para
-- facilitar el consumo en Power BI (modelo estrella / tabular).
--
-- Ejecutar después de la primera sincronización completa:
--   psql -U bi_user -d odoo_bi -f sql/create_bi_views.sql
-- ============================================================================

-- --------------------------------------------------------------------------
-- Vista: Ventas con detalle de líneas
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_ventas AS
SELECT
    sol.id AS line_id,
    so.id AS order_id,
    so.name AS order_name,
    so.state AS order_state,
    so.date_order,
    so.commitment_date,

    -- Cliente
    rp.id AS partner_id,
    rp.name AS partner_name,
    rp.city AS partner_city,
    rp.country_id AS partner_country_id,
    rp.is_company,

    -- Producto
    sol.product_id,
    pt.name AS product_name,
    pt.categ_id AS product_categ_id,
    pc.name AS product_category,

    -- Métricas
    sol.product_uom_qty AS qty_ordered,
    sol.qty_delivered,
    sol.qty_invoiced,
    sol.price_unit,
    sol.discount,
    sol.price_subtotal,
    sol.price_tax,
    sol.price_total,

    -- Totales de orden
    so.amount_untaxed AS order_untaxed,
    so.amount_tax AS order_tax,
    so.amount_total AS order_total,

    -- Vendedor / Equipo
    so.user_id AS salesperson_id,
    ru.name AS salesperson_name,
    so.team_id,
    so.company_id,
    so.currency_id,
    so.invoice_status

FROM sale_order_line sol
JOIN sale_order so ON so.id = sol.order_id
LEFT JOIN res_partner rp ON rp.id = so.partner_id
LEFT JOIN product_product pp ON pp.id = sol.product_id
LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
LEFT JOIN product_category pc ON pc.id = pt.categ_id
LEFT JOIN res_users ru ON ru.id = so.user_id;


-- --------------------------------------------------------------------------
-- Vista: Compras con detalle de líneas
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_compras AS
SELECT
    pol.id AS line_id,
    po.id AS order_id,
    po.name AS order_name,
    po.state AS order_state,
    po.date_order,
    po.date_approve,

    -- Proveedor
    rp.id AS partner_id,
    rp.name AS partner_name,
    rp.country_id AS partner_country_id,

    -- Producto
    pol.product_id,
    pt.name AS product_name,
    pc.name AS product_category,

    -- Métricas
    pol.product_qty AS qty_ordered,
    pol.qty_received,
    pol.qty_invoiced,
    pol.price_unit,
    pol.price_subtotal,
    pol.price_total,

    -- Totales
    po.amount_untaxed AS order_untaxed,
    po.amount_total AS order_total,

    po.user_id AS buyer_id,
    po.company_id,
    po.currency_id,
    po.invoice_status

FROM purchase_order_line pol
JOIN purchase_order po ON po.id = pol.order_id
LEFT JOIN res_partner rp ON rp.id = po.partner_id
LEFT JOIN product_product pp ON pp.id = pol.product_id
LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
LEFT JOIN product_category pc ON pc.id = pt.categ_id;


-- --------------------------------------------------------------------------
-- Vista: Facturas (account.move) con datos de partner
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_facturas AS
SELECT
    am.id,
    am.name,
    am.state,
    am.move_type,
    am.date,
    am.invoice_date,
    am.invoice_date_due,

    -- Tipo legible
    CASE am.move_type
        WHEN 'out_invoice' THEN 'Factura Cliente'
        WHEN 'out_refund' THEN 'Nota Crédito Cliente'
        WHEN 'in_invoice' THEN 'Factura Proveedor'
        WHEN 'in_refund' THEN 'Nota Crédito Proveedor'
        WHEN 'entry' THEN 'Asiento Contable'
        ELSE am.move_type
    END AS move_type_label,

    -- Partner
    rp.id AS partner_id,
    rp.name AS partner_name,
    rp.country_id AS partner_country_id,

    -- Montos
    am.amount_untaxed,
    am.amount_tax,
    am.amount_total,
    am.amount_residual,
    am.amount_total_signed,
    am.amount_residual_signed,

    am.payment_state,
    am.journal_id,
    aj.name AS journal_name,
    am.company_id,
    am.currency_id,
    am.invoice_user_id,
    am.team_id,

    am.create_date,
    am.write_date

FROM account_move am
LEFT JOIN res_partner rp ON rp.id = am.partner_id
LEFT JOIN account_journal aj ON aj.id = am.journal_id;


-- --------------------------------------------------------------------------
-- Vista: Líneas contables para análisis detallado
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_apuntes_contables AS
SELECT
    aml.id,
    aml.move_id,
    aml.move_name,
    aml.date,
    aml.date_maturity,

    -- Cuenta contable
    aa.id AS account_id,
    aa.code AS account_code,
    aa.name AS account_name,
    aa.account_type,

    -- Partner
    rp.id AS partner_id,
    rp.name AS partner_name,

    -- Producto
    aml.product_id,

    -- Montos
    aml.debit,
    aml.credit,
    aml.balance,
    aml.amount_currency,
    aml.amount_residual,

    aml.journal_id,
    aml.company_id,
    aml.currency_id,
    aml.parent_state

FROM account_move_line aml
LEFT JOIN account_account aa ON aa.id = aml.account_id
LEFT JOIN res_partner rp ON rp.id = aml.partner_id;


-- --------------------------------------------------------------------------
-- Vista: CRM Pipeline
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_crm AS
SELECT
    cl.id,
    cl.name,
    cl.type,
    cl.active,

    -- Stage
    cs.id AS stage_id,
    cs.name AS stage_name,
    cs.is_won,

    -- Partner
    rp.id AS partner_id,
    rp.name AS partner_name,

    -- Métricas
    cl.expected_revenue,
    cl.probability,
    cl.date_deadline,
    cl.date_closed,
    cl.date_open,
    cl.date_last_stage_update,

    -- Atribución
    cl.user_id,
    ru.name AS salesperson_name,
    cl.team_id,

    -- Origen
    cl.source_id,
    cl.medium_id,
    cl.campaign_id,

    -- Ubicación
    cl.city,
    cl.state_id,
    cl.country_id,

    cl.lost_reason_id,
    cl.company_id,
    cl.create_date,
    cl.write_date

FROM crm_lead cl
LEFT JOIN crm_stage cs ON cs.id = cl.stage_id
LEFT JOIN res_partner rp ON rp.id = cl.partner_id
LEFT JOIN res_users ru ON ru.id = cl.user_id;


-- --------------------------------------------------------------------------
-- Vista: Inventario actual (stock.quant)
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_inventario AS
SELECT
    sq.id,
    sq.product_id,
    pt.name AS product_name,
    pc.name AS product_category,
    sq.location_id,
    sl.name AS location_name,
    sl.complete_name AS location_complete_name,
    sl.usage AS location_usage,
    sq.lot_id,
    sq.quantity,
    sq.reserved_quantity,
    sq.quantity - sq.reserved_quantity AS available_quantity,
    sq.company_id,
    sq.in_date,
    sq.write_date

FROM stock_quant sq
LEFT JOIN product_product pp ON pp.id = sq.product_id
LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
LEFT JOIN product_category pc ON pc.id = pt.categ_id
LEFT JOIN stock_location sl ON sl.id = sq.location_id;


-- --------------------------------------------------------------------------
-- Vista: Pagos
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_pagos AS
SELECT
    ap.id,
    ap.name,
    ap.state,
    ap.payment_type,
    CASE ap.payment_type
        WHEN 'inbound' THEN 'Cobro'
        WHEN 'outbound' THEN 'Pago'
        ELSE ap.payment_type
    END AS payment_type_label,
    ap.partner_type,
    ap.date,
    ap.amount,

    rp.id AS partner_id,
    rp.name AS partner_name,

    ap.journal_id,
    aj.name AS journal_name,
    ap.currency_id,
    ap.company_id,
    ap.ref,

    ap.create_date,
    ap.write_date

FROM account_payment ap
LEFT JOIN res_partner rp ON rp.id = ap.partner_id
LEFT JOIN account_journal aj ON aj.id = ap.journal_id;


-- --------------------------------------------------------------------------
-- Vista: Resumen de estado de sincronización
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW bi_sync_status AS
SELECT
    model_name,
    pg_table,
    last_sync,
    records_synced,
    duration_seconds,
    status,
    error_message,
    NOW() - last_sync AS time_since_sync
FROM etl_sync_log
ORDER BY last_sync DESC;
