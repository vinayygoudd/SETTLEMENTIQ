-- =============================================================================
-- SettlementIQ — Financial Controls & Conservation Verification Queries
-- File: sql/09_financial_controls.sql
-- =============================================================================

-- Control Check 1: Signed Variance Identity (Observed - Expected = Signed Variance)
SELECT
    COUNT(*) AS identity_violations
FROM reconciliation.reconciliation_matches
WHERE (observed_amount - expected_amount) <> signed_variance
   OR ABS(signed_variance) <> absolute_variance;

-- Control Check 2: Resolved Exceptions Must Carry Zero Unresolved Exposure
SELECT
    COUNT(*) AS resolved_exposure_violations
FROM reconciliation.exceptions
WHERE resolution_status = 'RESOLVED'
  AND outstanding_exposure <> 0.00;

-- Control Check 3: Single-Currency Isolation in Validated Tables
SELECT
    (SELECT COUNT(*) FROM validated.transactions WHERE currency <> 'INR') +
    (SELECT COUNT(*) FROM validated.settlements WHERE currency <> 'INR') +
    (SELECT COUNT(*) FROM validated.bank_entries WHERE currency <> 'INR') +
    (SELECT COUNT(*) FROM validated.refunds WHERE currency <> 'INR') AS foreign_currency_leakage_count;
