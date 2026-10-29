-- =============================================================================
-- SettlementIQ — Automated SQL Test Suite & Invariant Assertions
-- File: sql/10_test_queries.sql
-- =============================================================================

SELECT 'SQL_TEST_01_TOTAL_CASES_10000' AS test_id,
       CASE WHEN COUNT(*) = 10000 THEN 'PASS' ELSE 'FAIL' END AS status
FROM reconciliation.reconciliation_matches
UNION ALL
SELECT 'SQL_TEST_02_MATCHED_9200' AS test_id,
       CASE WHEN COUNT(*) = 9200 THEN 'PASS' ELSE 'FAIL' END AS status
FROM reconciliation.reconciliation_matches WHERE is_matched = TRUE
UNION ALL
SELECT 'SQL_TEST_03_EXCEPTIONS_800' AS test_id,
       CASE WHEN COUNT(*) = 800 THEN 'PASS' ELSE 'FAIL' END AS status
FROM reconciliation.exceptions
UNION ALL
SELECT 'SQL_TEST_04_QUARANTINE_45' AS test_id,
       CASE WHEN COUNT(*) = 45 THEN 'PASS' ELSE 'FAIL' END AS status
FROM raw_staging.quarantine_records
UNION ALL
SELECT 'SQL_TEST_05_ZERO_VARIANCE_IDENTITY_ERROR' AS test_id,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM reconciliation.reconciliation_matches
WHERE (observed_amount - expected_amount) <> signed_variance;
