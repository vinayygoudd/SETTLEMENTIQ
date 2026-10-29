-- =============================================================================
-- SettlementIQ — Analytical Views for Power BI & Excel
-- File: sql/07_analytics_views.sql
-- =============================================================================

CREATE OR REPLACE VIEW analytics.vw_reconciliation_overview AS
SELECT
    reconciliation_classification,
    applied_rule_id,
    CASE WHEN is_matched THEN 'MATCHED' ELSE 'EXCEPTION' END AS outcome_group,
    COUNT(*) AS record_count,
    SUM(gross_transaction_amount) AS total_gross_inr,
    SUM(expected_amount) AS total_expected_net_inr,
    SUM(observed_amount) AS total_observed_net_inr,
    SUM(signed_variance) AS net_signed_variance_inr,
    SUM(absolute_variance) AS total_absolute_variance_inr
FROM reconciliation.reconciliation_matches
GROUP BY reconciliation_classification, applied_rule_id, is_matched
ORDER BY record_count DESC;

CREATE OR REPLACE VIEW analytics.vw_merchant_exposure AS
SELECT
    m.merchant_id,
    md.merchant_name,
    md.merchant_category,
    md.region,
    m.payment_gateway,
    COUNT(*) FILTER (WHERE m.record_grain = 'TRANSACTION') AS validated_txn_count,
    COUNT(*) FILTER (WHERE m.is_matched = TRUE) AS matched_count,
    COUNT(e.exception_id) AS exception_count,
    COUNT(e.exception_id) FILTER (WHERE e.resolution_status IN ('OPEN', 'REOPENED')) AS unresolved_exception_count,
    SUM(m.gross_transaction_amount) AS gross_txn_value_inr,
    SUM(m.expected_amount) AS expected_net_value_inr,
    SUM(m.observed_amount) AS observed_net_value_inr,
    COALESCE(SUM(e.outstanding_exposure), 0.00) AS outstanding_exposure_inr,
    COALESCE(SUM(e.confirmed_loss), 0.00) AS confirmed_loss_inr
FROM reconciliation.reconciliation_matches m
LEFT JOIN validated.merchants md ON m.merchant_id = md.merchant_id
LEFT JOIN reconciliation.exceptions e ON m.match_id = e.match_id
GROUP BY m.merchant_id, md.merchant_name, md.merchant_category, md.region, m.payment_gateway
ORDER BY outstanding_exposure_inr DESC;
