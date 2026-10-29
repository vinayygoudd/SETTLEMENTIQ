-- =============================================================================
-- SettlementIQ — Data Quality Validation, Quarantine & Validated Loading
-- File: sql/04_data_quality.sql
-- =============================================================================

BEGIN;

-- 1. Quarantine Invalid Transactions (Scenarios S15, S16, S17, S18, S19)
INSERT INTO raw_staging.quarantine_records (
    source_entity, source_record_id, merchant_id, payment_gateway,
    quarantine_reason, quarantine_detail, raw_amount, expected_net_inr,
    currency, run_id
)
SELECT
    'TRANSACTIONS',
    COALESCE(NULLIF(TRIM(transaction_id), ''), 'MISSING_TXN_ID'),
    COALESCE(NULLIF(TRIM(merchant_id), ''), 'MISSING'),
    COALESCE(NULLIF(TRIM(payment_gateway), ''), 'UNKNOWN'),
    CASE
        WHEN TRIM(transaction_id) !~ '^TXN_[0-9]{4}_[0-9]{6}$' THEN 'INVALID_IDENTIFIER'
        WHEN TRIM(merchant_id) = '' OR TRIM(payment_reference) = '' THEN 'MISSING_MANDATORY_FIELD'
        WHEN TRIM(transaction_date) = '' THEN 'MISSING_DATE'
        WHEN TRIM(currency) <> 'INR' THEN 'INVALID_CURRENCY'
        WHEN CAST(transaction_amount AS NUMERIC(18, 2)) <= 0 THEN 'MALFORMED_AMOUNT'
        ELSE 'SCHEMA_DEFECT'
    END,
    'Quarantined during staging validation prior to reconciliation',
    COALESCE(transaction_amount, '0.00'),
    CAST(COALESCE(NULLIF(expected_net_amount, ''), '0.00') AS NUMERIC(18, 2)),
    COALESCE(currency, 'INR'),
    'RUN_20261025_001'
FROM raw_staging.stg_transactions
WHERE TRIM(transaction_id) !~ '^TXN_[0-9]{4}_[0-9]{6}$'
   OR TRIM(merchant_id) = ''
   OR TRIM(payment_reference) = ''
   OR TRIM(transaction_date) = ''
   OR TRIM(currency) <> 'INR'
   OR CAST(transaction_amount AS NUMERIC(18, 2)) <= 0;

-- 2. Load Deduplicated Validated Transactions (Suppressing Scenario S20 Replays via occurrence = 1)
WITH clean_txns AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY TRIM(transaction_id) ORDER BY stg_id ASC) AS rn
    FROM raw_staging.stg_transactions
    WHERE TRIM(transaction_id) ~ '^TXN_[0-9]{4}_[0-9]{6}$'
      AND TRIM(merchant_id) <> ''
      AND TRIM(payment_reference) <> ''
      AND TRIM(transaction_date) <> ''
      AND TRIM(currency) = 'INR'
      AND CAST(transaction_amount AS NUMERIC(18, 2)) > 0
)
INSERT INTO validated.transactions
SELECT
    TRIM(transaction_id), TRIM(customer_id), TRIM(merchant_id),
    TRIM(payment_reference), TRIM(order_reference),
    CAST(transaction_timestamp AS TIMESTAMPTZ), CAST(transaction_date AS DATE),
    CAST(transaction_amount AS NUMERIC(18, 2)), TRIM(currency),
    TRIM(payment_method), TRIM(payment_status), TRIM(payment_gateway),
    CAST(settlement_expected_date AS DATE),
    CAST(transaction_fee AS NUMERIC(18, 2)),
    CAST(expected_net_amount AS NUMERIC(18, 2)),
    CAST(ingestion_timestamp AS TIMESTAMPTZ),
    TRIM(source_system), CAST(record_version AS INTEGER), TRUE
FROM clean_txns
WHERE rn = 1
ON CONFLICT (transaction_id) DO NOTHING;

COMMIT;
