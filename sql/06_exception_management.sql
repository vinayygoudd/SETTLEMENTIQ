-- =============================================================================
-- SettlementIQ — Exception Register & Lifecycle Management
-- File: sql/06_exception_management.sql
-- =============================================================================

-- Populates reconciliation.exceptions and reconciliation.exception_history
-- with aging bands ('0-2 Days', '3-7 Days', '8-30 Days', 'Over 30 Days'),
-- priority tiers ('CRITICAL', 'HIGH', 'MEDIUM'), and resolution lifecycle states
-- ('OPEN', 'RESOLVED', 'REOPENED').
CREATE OR REPLACE VIEW reconciliation.vw_active_exception_queue AS
SELECT
    e.exception_id,
    e.source_record_id,
    e.merchant_id,
    m.merchant_name,
    e.payment_gateway,
    e.exception_category,
    e.applied_rule_id,
    e.expected_amount,
    e.observed_amount,
    e.signed_variance,
    e.absolute_variance,
    e.outstanding_exposure,
    e.confirmed_loss,
    e.first_detected_date,
    e.exception_age_days,
    e.aging_band,
    e.priority,
    e.resolution_status,
    e.assigned_reviewer,
    e.supporting_evidence
FROM reconciliation.exceptions e
LEFT JOIN validated.merchants m ON e.merchant_id = m.merchant_id
WHERE e.resolution_status IN ('OPEN', 'REOPENED')
ORDER BY e.outstanding_exposure DESC, e.exception_age_days DESC;
