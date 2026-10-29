-- =============================================================================
-- SettlementIQ — PostgreSQL Database Creation & Role Setup Instructions
-- File: sql/00_create_database_instructions.sql
-- =============================================================================
-- Run as a PostgreSQL superuser (e.g., postgres) to initialize the database:
--
--   psql -U postgres -f sql/00_create_database_instructions.sql
--
-- Wait for database creation, then execute scripts 01 through 11 against the
-- `settlementiq` database:
--   psql -U settlementiq_role -d settlementiq -f sql/01_schema.sql
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'settlementiq_role') THEN
        CREATE ROLE settlementiq_role WITH LOGIN CREATEDB;
    END IF;
END
$$;

-- In psql interactive mode:
-- CREATE DATABASE settlementiq OWNER settlementiq_role ENCODING 'UTF8';
-- GRANT ALL PRIVILEGES ON DATABASE settlementiq TO settlementiq_role;
