-- =============================================================================
-- SettlementIQ — Relational Schema Definition (4 Logical Layers, 12 Tables)
-- File: sql/01_schema.sql
-- Layers:
--   1. raw_staging     (Unmodified CSV ingestion landing tables & quarantine)
--   2. validated       (Type-checked, deduplicated, normalized financial records)
--   3. reconciliation  (Authoritative runs, matches, match_evidence, exceptions, history)
--   4. analytics       (KPI snapshots, data quality results & analytical views)
-- =============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS raw_staging;
CREATE SCHEMA IF NOT EXISTS validated;
CREATE SCHEMA IF NOT EXISTS reconciliation;
CREATE SCHEMA IF NOT EXISTS analytics;

-- -----------------------------------------------------------------------------
-- 1. RAW / STAGING LAYER
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS raw_staging.stg_merchants CASCADE;
CREATE TABLE raw_staging.stg_merchants (
    stg_id                      BIGSERIAL PRIMARY KEY,
    merchant_id                 TEXT,
    merchant_name               TEXT,
    merchant_category           TEXT,
    onboarding_date             TEXT,
    merchant_status             TEXT,
    settlement_frequency        TEXT,
    contractual_fee_rate        TEXT,
    contractual_fixed_fee       TEXT,
    currency                    TEXT,
    region                      TEXT,
    operational_classification  TEXT,
    default_payment_gateway     TEXT,
    settlement_sla_days         TEXT,
    is_synthetic                TEXT,
    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS raw_staging.stg_transactions CASCADE;
CREATE TABLE raw_staging.stg_transactions (
    stg_id                      BIGSERIAL PRIMARY KEY,
    transaction_id              TEXT,
    customer_id                 TEXT,
    merchant_id                 TEXT,
    payment_reference           TEXT,
    order_reference             TEXT,
    transaction_timestamp       TEXT,
    transaction_date            TEXT,
    transaction_amount          TEXT,
    currency                    TEXT,
    payment_method              TEXT,
    payment_status              TEXT,
    payment_gateway             TEXT,
    settlement_expected_date    TEXT,
    transaction_fee             TEXT,
    expected_net_amount         TEXT,
    ingestion_timestamp         TEXT,
    source_system               TEXT,
    record_version              TEXT,
    is_synthetic                TEXT,
    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS raw_staging.stg_settlements CASCADE;
CREATE TABLE raw_staging.stg_settlements (
    stg_id                      BIGSERIAL PRIMARY KEY,
    settlement_id               TEXT,
    settlement_reference        TEXT,
    transaction_id              TEXT,
    payment_reference           TEXT,
    merchant_id                 TEXT,
    settlement_batch_id         TEXT,
    settlement_timestamp        TEXT,
    settlement_date             TEXT,
    gross_amount                TEXT,
    fee_amount                  TEXT,
    net_settlement_amount       TEXT,
    currency                    TEXT,
    settlement_status           TEXT,
    settlement_type             TEXT,
    allocation_line_no          TEXT,
    total_allocation_lines      TEXT,
    source_system               TEXT,
    ingestion_timestamp         TEXT,
    is_synthetic                TEXT,
    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS raw_staging.stg_bank_entries CASCADE;
CREATE TABLE raw_staging.stg_bank_entries (
    stg_id                      BIGSERIAL PRIMARY KEY,
    bank_entry_id               TEXT,
    bank_reference              TEXT,
    settlement_reference        TEXT,
    transaction_reference       TEXT,
    merchant_id                 TEXT,
    entry_timestamp             TEXT,
    value_date                  TEXT,
    credit_amount               TEXT,
    debit_amount                TEXT,
    signed_bank_amount          TEXT,
    currency                    TEXT,
    bank_description            TEXT,
    bank_status                 TEXT,
    ingestion_timestamp         TEXT,
    is_synthetic                TEXT,
    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS raw_staging.stg_refunds CASCADE;
CREATE TABLE raw_staging.stg_refunds (
    stg_id                      BIGSERIAL PRIMARY KEY,
    refund_id                   TEXT,
    original_transaction_id     TEXT,
    refund_reference            TEXT,
    merchant_id                 TEXT,
    refund_timestamp            TEXT,
    refund_amount               TEXT,
    settled_refund_deduction    TEXT,
    currency                    TEXT,
    refund_status               TEXT,
    refund_reason               TEXT,
    settlement_reference        TEXT,
    bank_reference              TEXT,
    ingestion_timestamp         TEXT,
    is_synthetic                TEXT,
    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS raw_staging.quarantine_records CASCADE;
CREATE TABLE raw_staging.quarantine_records (
    quarantine_id               BIGSERIAL PRIMARY KEY,
    source_entity               VARCHAR(50) NOT NULL,
    source_record_id            VARCHAR(100) NOT NULL,
    merchant_id                 VARCHAR(50) NOT NULL,
    payment_gateway             VARCHAR(100) NOT NULL,
    quarantine_reason           VARCHAR(60) NOT NULL,
    quarantine_detail           TEXT NOT NULL,
    raw_amount                  VARCHAR(50) NOT NULL,
    expected_net_inr            NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    currency                    VARCHAR(10) NOT NULL,
    run_id                      VARCHAR(64) NOT NULL,
    quarantined_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 2. VALIDATED LAYER
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS validated.merchants CASCADE;
CREATE TABLE validated.merchants (
    merchant_id                 VARCHAR(32) PRIMARY KEY,
    merchant_name               VARCHAR(150) NOT NULL,
    merchant_category           VARCHAR(100) NOT NULL,
    onboarding_date             DATE NOT NULL,
    merchant_status             VARCHAR(30) NOT NULL,
    settlement_frequency        VARCHAR(16) NOT NULL,
    contractual_fee_rate        NUMERIC(8, 4) NOT NULL,
    contractual_fixed_fee       NUMERIC(18, 2) NOT NULL,
    currency                    CHAR(3) NOT NULL,
    region                      VARCHAR(40) NOT NULL,
    operational_classification  VARCHAR(50) NOT NULL,
    default_payment_gateway     VARCHAR(80) NOT NULL,
    settlement_sla_days         INTEGER NOT NULL,
    is_synthetic                BOOLEAN NOT NULL DEFAULT TRUE
);

DROP TABLE IF EXISTS validated.transactions CASCADE;
CREATE TABLE validated.transactions (
    transaction_id              VARCHAR(64) PRIMARY KEY,
    customer_id                 VARCHAR(64) NOT NULL,
    merchant_id                 VARCHAR(32) NOT NULL REFERENCES validated.merchants(merchant_id),
    payment_reference           VARCHAR(64) NOT NULL,
    order_reference             VARCHAR(64) NOT NULL,
    transaction_timestamp       TIMESTAMPTZ NOT NULL,
    transaction_date            DATE NOT NULL,
    transaction_amount          NUMERIC(18, 2) NOT NULL,
    currency                    CHAR(3) NOT NULL,
    payment_method              VARCHAR(40) NOT NULL,
    payment_status              VARCHAR(30) NOT NULL,
    payment_gateway             VARCHAR(80) NOT NULL,
    settlement_expected_date    DATE NOT NULL,
    transaction_fee             NUMERIC(18, 2) NOT NULL,
    expected_net_amount         NUMERIC(18, 2) NOT NULL,
    ingestion_timestamp         TIMESTAMPTZ NOT NULL,
    source_system               VARCHAR(80) NOT NULL,
    record_version              INTEGER NOT NULL DEFAULT 1,
    is_synthetic                BOOLEAN NOT NULL DEFAULT TRUE
);

DROP TABLE IF EXISTS validated.settlements CASCADE;
CREATE TABLE validated.settlements (
    settlement_id               VARCHAR(64) PRIMARY KEY,
    settlement_reference        VARCHAR(64) NOT NULL UNIQUE,
    transaction_id              VARCHAR(64) NOT NULL,
    payment_reference           VARCHAR(64) NOT NULL,
    merchant_id                 VARCHAR(32) NOT NULL REFERENCES validated.merchants(merchant_id),
    settlement_batch_id         VARCHAR(100) NOT NULL,
    settlement_timestamp        TIMESTAMPTZ NOT NULL,
    settlement_date             DATE NOT NULL,
    gross_amount                NUMERIC(18, 2) NOT NULL,
    fee_amount                  NUMERIC(18, 2) NOT NULL,
    net_settlement_amount       NUMERIC(18, 2) NOT NULL,
    currency                    CHAR(3) NOT NULL,
    settlement_status           VARCHAR(30) NOT NULL,
    settlement_type             VARCHAR(40) NOT NULL,
    allocation_line_no          INTEGER NOT NULL DEFAULT 1,
    total_allocation_lines      INTEGER NOT NULL DEFAULT 1,
    source_system               VARCHAR(80) NOT NULL,
    ingestion_timestamp         TIMESTAMPTZ NOT NULL,
    is_synthetic                BOOLEAN NOT NULL DEFAULT TRUE
);

DROP TABLE IF EXISTS validated.bank_entries CASCADE;
CREATE TABLE validated.bank_entries (
    bank_entry_id               VARCHAR(64) PRIMARY KEY,
    bank_reference              VARCHAR(64) NOT NULL UNIQUE,
    settlement_reference        VARCHAR(64) NOT NULL,
    transaction_reference       VARCHAR(64) NOT NULL,
    merchant_id                 VARCHAR(32) NOT NULL REFERENCES validated.merchants(merchant_id),
    entry_timestamp             TIMESTAMPTZ NOT NULL,
    value_date                  DATE NOT NULL,
    credit_amount               NUMERIC(18, 2) NOT NULL,
    debit_amount                NUMERIC(18, 2) NOT NULL,
    signed_bank_amount          NUMERIC(18, 2) NOT NULL,
    currency                    CHAR(3) NOT NULL,
    bank_description            VARCHAR(255) NOT NULL,
    bank_status                 VARCHAR(30) NOT NULL,
    ingestion_timestamp         TIMESTAMPTZ NOT NULL,
    is_synthetic                BOOLEAN NOT NULL DEFAULT TRUE
);

DROP TABLE IF EXISTS validated.refunds CASCADE;
CREATE TABLE validated.refunds (
    refund_id                   VARCHAR(64) PRIMARY KEY,
    original_transaction_id     VARCHAR(64) NOT NULL REFERENCES validated.transactions(transaction_id),
    refund_reference            VARCHAR(64) NOT NULL UNIQUE,
    merchant_id                 VARCHAR(32) NOT NULL REFERENCES validated.merchants(merchant_id),
    refund_timestamp            TIMESTAMPTZ NOT NULL,
    refund_amount               NUMERIC(18, 2) NOT NULL,
    settled_refund_deduction    NUMERIC(18, 2) NOT NULL,
    currency                    CHAR(3) NOT NULL,
    refund_status               VARCHAR(50) NOT NULL,
    refund_reason               VARCHAR(100) NOT NULL,
    settlement_reference        VARCHAR(64),
    bank_reference              VARCHAR(64),
    ingestion_timestamp         TIMESTAMPTZ NOT NULL,
    is_synthetic                BOOLEAN NOT NULL DEFAULT TRUE
);

-- -----------------------------------------------------------------------------
-- 3. RECONCILIATION LAYER
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS reconciliation.reconciliation_runs CASCADE;
CREATE TABLE reconciliation.reconciliation_runs (
    run_id                      VARCHAR(64) PRIMARY KEY,
    rule_version                VARCHAR(64) NOT NULL,
    dataset_version             VARCHAR(64) NOT NULL,
    reporting_date              DATE NOT NULL,
    tolerance_inr               NUMERIC(18, 2) NOT NULL,
    sla_business_days           INTEGER NOT NULL,
    total_evaluated_cases       INTEGER NOT NULL,
    eligible_ledger_count       INTEGER NOT NULL,
    matched_count               INTEGER NOT NULL,
    exception_count             INTEGER NOT NULL,
    reconciliation_rate_pct     NUMERIC(8, 2) NOT NULL,
    total_expected_inr          NUMERIC(18, 2) NOT NULL,
    total_observed_inr          NUMERIC(18, 2) NOT NULL,
    net_signed_discrepancy_inr  NUMERIC(18, 2) NOT NULL,
    outstanding_exposure_inr    NUMERIC(18, 2) NOT NULL,
    confirmed_loss_inr          NUMERIC(18, 2) NOT NULL,
    run_status                  VARCHAR(30) NOT NULL,
    executed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS reconciliation.reconciliation_matches CASCADE;
CREATE TABLE reconciliation.reconciliation_matches (
    match_id                    VARCHAR(64) PRIMARY KEY,
    run_id                      VARCHAR(64) NOT NULL REFERENCES reconciliation.reconciliation_runs(run_id),
    rule_version                VARCHAR(64) NOT NULL,
    source_record_id            VARCHAR(64) NOT NULL UNIQUE,
    record_grain                VARCHAR(30) NOT NULL,
    transaction_id              VARCHAR(64),
    settlement_ids              TEXT,
    bank_entry_ids              TEXT,
    refund_id                   VARCHAR(64),
    merchant_id                 VARCHAR(32) NOT NULL,
    payment_gateway             VARCHAR(80) NOT NULL,
    transaction_date            DATE,
    settlement_date             DATE,
    bank_value_date             DATE,
    business_days_to_settle     INTEGER NOT NULL DEFAULT 0,
    business_days_to_bank       INTEGER NOT NULL DEFAULT 0,
    currency                    CHAR(3) NOT NULL DEFAULT 'INR',
    gross_transaction_amount    NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    expected_amount             NUMERIC(18, 2) NOT NULL,
    observed_amount             NUMERIC(18, 2) NOT NULL,
    fee_amount                  NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    signed_variance             NUMERIC(18, 2) NOT NULL,
    absolute_variance           NUMERIC(18, 2) NOT NULL,
    applied_rule_id             VARCHAR(40) NOT NULL,
    reconciliation_classification VARCHAR(50) NOT NULL,
    is_matched                  BOOLEAN NOT NULL,
    is_exception                BOOLEAN NOT NULL,
    exception_category          VARCHAR(50) NOT NULL,
    evidence_summary            TEXT NOT NULL
);

DROP TABLE IF EXISTS reconciliation.match_evidence CASCADE;
CREATE TABLE reconciliation.match_evidence (
    evidence_id                 BIGSERIAL PRIMARY KEY,
    match_id                    VARCHAR(64) NOT NULL REFERENCES reconciliation.reconciliation_matches(match_id),
    run_id                      VARCHAR(64) NOT NULL,
    applied_rule_id             VARCHAR(40) NOT NULL,
    rule_version                VARCHAR(64) NOT NULL,
    evidence_strength           VARCHAR(30) NOT NULL,
    evidence_payload            TEXT NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TABLE IF EXISTS reconciliation.exceptions CASCADE;
CREATE TABLE reconciliation.exceptions (
    exception_id                VARCHAR(64) PRIMARY KEY,
    run_id                      VARCHAR(64) NOT NULL REFERENCES reconciliation.reconciliation_runs(run_id),
    match_id                    VARCHAR(64) NOT NULL REFERENCES reconciliation.reconciliation_matches(match_id),
    source_record_id            VARCHAR(64) NOT NULL UNIQUE,
    transaction_id              VARCHAR(64),
    settlement_ids              TEXT,
    bank_entry_ids              TEXT,
    refund_id                   VARCHAR(64),
    merchant_id                 VARCHAR(32) NOT NULL,
    payment_gateway             VARCHAR(80) NOT NULL,
    exception_category          VARCHAR(50) NOT NULL,
    applied_rule_id             VARCHAR(40) NOT NULL,
    rule_version                VARCHAR(64) NOT NULL,
    expected_amount             NUMERIC(18, 2) NOT NULL,
    observed_amount             NUMERIC(18, 2) NOT NULL,
    signed_variance             NUMERIC(18, 2) NOT NULL,
    absolute_variance           NUMERIC(18, 2) NOT NULL,
    outstanding_exposure        NUMERIC(18, 2) NOT NULL,
    confirmed_loss              NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    currency                    CHAR(3) NOT NULL DEFAULT 'INR',
    first_detected_date         DATE NOT NULL,
    last_detected_date          DATE NOT NULL,
    exception_age_days          INTEGER NOT NULL,
    aging_band                  VARCHAR(30) NOT NULL,
    priority                    VARCHAR(20) NOT NULL,
    resolution_status           VARCHAR(30) NOT NULL,
    assigned_reviewer           VARCHAR(100) NOT NULL,
    resolution_category         VARCHAR(60) NOT NULL,
    resolution_notes            TEXT NOT NULL,
    resolved_timestamp          TIMESTAMPTZ,
    reopened_timestamp          TIMESTAMPTZ,
    supporting_evidence         TEXT NOT NULL
);

DROP TABLE IF EXISTS reconciliation.exception_history CASCADE;
CREATE TABLE reconciliation.exception_history (
    history_id                  BIGSERIAL PRIMARY KEY,
    exception_id                VARCHAR(64) NOT NULL REFERENCES reconciliation.exceptions(exception_id),
    run_id                      VARCHAR(64) NOT NULL,
    previous_status             VARCHAR(30),
    new_status                  VARCHAR(30) NOT NULL,
    action_by                   VARCHAR(100) NOT NULL,
    action_timestamp            TIMESTAMPTZ NOT NULL,
    notes                       TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- 4. ANALYTICS LAYER TABLES
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS analytics.data_quality_results CASCADE;
CREATE TABLE analytics.data_quality_results (
    dq_result_id                BIGSERIAL PRIMARY KEY,
    run_id                      VARCHAR(64) NOT NULL,
    dataset_name                VARCHAR(50) NOT NULL,
    raw_rows                    INTEGER NOT NULL,
    validated_rows              INTEGER NOT NULL,
    quarantined_rows            INTEGER NOT NULL,
    suppressed_duplicate_rows   INTEGER NOT NULL,
    raw_inr_amount              NUMERIC(18, 2) NOT NULL,
    validated_inr_amount        NUMERIC(18, 2) NOT NULL,
    quarantined_inr_amount      NUMERIC(18, 2) NOT NULL,
    suppressed_duplicate_inr    NUMERIC(18, 2) NOT NULL,
    unexplained_diff_inr        NUMERIC(18, 2) NOT NULL,
    dq_pass_rate_pct            NUMERIC(8, 2) NOT NULL
);

DROP TABLE IF EXISTS analytics.kpi_snapshots CASCADE;
CREATE TABLE analytics.kpi_snapshots (
    snapshot_id                 BIGSERIAL PRIMARY KEY,
    run_id                      VARCHAR(64) NOT NULL,
    kpi_id                      VARCHAR(32) NOT NULL,
    category                    VARCHAR(50) NOT NULL,
    kpi_name                    VARCHAR(120) NOT NULL,
    actual_value                VARCHAR(64) NOT NULL,
    unit                        VARCHAR(32) NOT NULL,
    formula                     TEXT NOT NULL,
    population                  TEXT NOT NULL,
    captured_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
