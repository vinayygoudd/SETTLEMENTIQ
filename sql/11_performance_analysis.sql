-- =============================================================================
-- SettlementIQ — Query Performance Inspection (EXPLAIN / EXPLAIN ANALYZE)
-- File: sql/11_performance_analysis.sql
-- =============================================================================

-- Inspect execution plan for primary transaction-to-settlement reconciliation join:
EXPLAIN
SELECT
    t.transaction_id,
    t.merchant_id,
    t.expected_net_amount,
    COUNT(s.settlement_id) AS stl_lines,
    SUM(s.net_settlement_amount) AS observed_stl_net
FROM validated.transactions t
LEFT JOIN validated.settlements s ON t.transaction_id = s.transaction_id
GROUP BY t.transaction_id, t.merchant_id, t.expected_net_amount;

-- Inspect execution plan for anti-join detecting orphan settlements (Missing Ledger R7):
EXPLAIN
SELECT
    s.settlement_id,
    s.transaction_id,
    s.net_settlement_amount
FROM validated.settlements s
LEFT JOIN validated.transactions t ON s.transaction_id = t.transaction_id
WHERE t.transaction_id IS NULL;
