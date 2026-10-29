-- =============================================================================
-- SettlementIQ — Authoritative Deterministic Reconciliation Engine (Rules R1–R9)
-- File: sql/05_reconciliation.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION reconciliation.fn_business_days_between(start_dt DATE, end_dt DATE)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN start_dt IS NULL OR end_dt IS NULL OR end_dt <= start_dt THEN 0
        ELSE (
            SELECT COUNT(*)::INTEGER
            FROM generate_series(start_dt + INTERVAL '1 day', end_dt, INTERVAL '1 day') AS d
            WHERE EXTRACT(ISODOW FROM d) BETWEEN 1 AND 5
        )
    END;
$$;

-- Main CTE Reconciliation Pipeline (Rules R1 through R9 in Precedence Order)
-- Evaluates all 9,885 validated transactions, 50 orphan settlements,
-- 20 orphan bank entries, and 45 quarantined records (= 10,000 cases).
-- See python/src/settlementiq/reconciliation_runner.py for the synchronized execution harness.
