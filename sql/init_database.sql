-- ============================================================================
-- Inicialización de la base de datos PostgreSQL para BI
--
-- Ejecutar como superusuario de PostgreSQL:
--   sudo -u postgres psql -f sql/init_database.sql
-- ============================================================================

-- Crear usuario para BI (cambiar contraseña)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bi_user') THEN
        CREATE ROLE bi_user WITH LOGIN PASSWORD 'CAMBIAR_ESTA_PASSWORD';
    END IF;
END
$$;

-- Crear base de datos
SELECT 'CREATE DATABASE odoo_bi OWNER bi_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'odoo_bi')\gexec

-- Permisos
GRANT ALL PRIVILEGES ON DATABASE odoo_bi TO bi_user;

-- Conectar a la base y dar permisos en schema
\c odoo_bi
GRANT ALL ON SCHEMA public TO bi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO bi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO bi_user;

-- Crear usuario de solo lectura para Power BI (más seguro)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'powerbi_reader') THEN
        CREATE ROLE powerbi_reader WITH LOGIN PASSWORD 'CAMBIAR_ESTA_PASSWORD_POWERBI';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE odoo_bi TO powerbi_reader;
GRANT USAGE ON SCHEMA public TO powerbi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO powerbi_reader;

-- Dar SELECT en tablas existentes (ejecutar después de la primera sync)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO powerbi_reader;
