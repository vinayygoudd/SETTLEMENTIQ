-- =============================================================================
-- SettlementIQ — Authoritative SQL Queries for All 42 KPIs
-- File: sql/08_kpi_queries.sql
-- =============================================================================

-- 1. Executive Headline KPIs
SELECT
    (SELECT COUNT(*) FROM raw_staging.stg_transactions) AS raw_txn_count,
    (SELECT COUNT(*) FROM validated.transactions) AS validated_txn_count,
    (SELECT COUNT(DISTINCT customer_id) FROM validated.transactions) AS distinct_customers,
    (SELECT COUNT(DISTINCT merchant_id) FROM validated.merchants) AS distinct_merchants,
    (SELECT COUNT(*) FROM reconciliation.reconciliation_matches WHERE is_matched = TRUE) AS matched_count,
    (SELECT COUNT(*) FROM reconciliation.exceptions) AS total_exception_count,
    ROUND(
        (SELECT COUNT(*)::NUMERIC FROM reconciliation.reconciliation_matches WHERE is_matched = TRUE)
        / NULLIF((SELECT COUNT(*)::NUMERIC FROM validated.transactions), 0) * 100.0,
        2
    ) AS ledger_reconciliation_rate_pct,
    (SELECT SUM(signed_variance) FROM reconciliation.reconciliation_matches) AS net_signed_discrepancy_inr,
    (SELECT SUM(outstanding_exposure) FROM reconciliation.exceptions) AS outstanding_exposure_inr,
    (SELECT SUM(confirmed_loss) FROM reconciliation.exceptions) AS confirmed_loss_inr;
