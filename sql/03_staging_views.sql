-- =============================================================================
-- SettlementIQ — Staging Views & Normalization Profiling
-- File: sql/03_staging_views.sql
-- =============================================================================

CREATE OR REPLACE VIEW raw_staging.vw_stg_transactions_profile AS
SELECT
    stg_id,
    TRIM(transaction_id) AS clean_txn_id,
    TRIM(customer_id) AS clean_customer_id,
    TRIM(merchant_id) AS clean_merchant_id,
    TRIM(payment_reference) AS clean_payment_ref,
    TRIM(transaction_date) AS raw_txn_date,
    TRIM(currency) AS clean_currency,
    CAST(NULLIF(TRIM(transaction_amount), '') AS NUMERIC(18, 2)) AS numeric_amount,
    CAST(NULLIF(TRIM(expected_net_amount), '') AS NUMERIC(18, 2)) AS numeric_expected_net,
    ROW_NUMBER() OVER (PARTITION BY TRIM(transaction_id) ORDER BY stg_id ASC) AS ingestion_occurrence_no
FROM raw_staging.stg_transactions;

CREATE OR REPLACE VIEW raw_staging.vw_stg_settlements_profile AS
SELECT
    stg_id,
    TRIM(settlement_id) AS clean_settlement_id,
    TRIM(settlement_reference) AS clean_settlement_ref,
    TRIM(transaction_id) AS clean_txn_id,
    TRIM(payment_reference) AS clean_payment_ref,
    TRIM(merchant_id) AS clean_merchant_id,
    CAST(NULLIF(TRIM(net_settlement_amount), '') AS NUMERIC(18, 2)) AS numeric_net_settlement,
    ROW_NUMBER() OVER (PARTITION BY TRIM(settlement_id) ORDER BY stg_id ASC) AS ingestion_occurrence_no
FROM raw_staging.stg_settlements;
