-- =============================================================================
-- SettlementIQ — Constraints & Performance Indexes
-- File: sql/02_constraints_indexes.sql
-- =============================================================================

BEGIN;

ALTER TABLE validated.merchants
    ADD CONSTRAINT chk_merch_rate CHECK (contractual_fee_rate BETWEEN 0.0000 AND 0.1500),
    ADD CONSTRAINT chk_merch_curr CHECK (currency = 'INR');

ALTER TABLE validated.transactions
    ADD CONSTRAINT chk_txn_gross_pos CHECK (transaction_amount > 0),
    ADD CONSTRAINT chk_txn_fee_nonneg CHECK (transaction_fee >= 0),
    ADD CONSTRAINT chk_txn_curr CHECK (currency = 'INR');

ALTER TABLE validated.settlements
    ADD CONSTRAINT chk_stl_gross_pos CHECK (gross_amount > 0),
    ADD CONSTRAINT chk_stl_lines CHECK (allocation_line_no >= 1 AND allocation_line_no <= total_allocation_lines),
    ADD CONSTRAINT chk_stl_curr CHECK (currency = 'INR');

ALTER TABLE validated.bank_entries
    ADD CONSTRAINT chk_bnk_cr_nonneg CHECK (credit_amount >= 0),
    ADD CONSTRAINT chk_bnk_dr_nonneg CHECK (debit_amount >= 0),
    ADD CONSTRAINT chk_bnk_curr CHECK (currency = 'INR');

ALTER TABLE validated.refunds
    ADD CONSTRAINT chk_ref_amt_pos CHECK (refund_amount > 0),
    ADD CONSTRAINT chk_ref_curr CHECK (currency = 'INR');

ALTER TABLE reconciliation.exceptions
    ADD CONSTRAINT chk_exc_status CHECK (resolution_status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'REOPENED')),
    ADD CONSTRAINT chk_exc_aging CHECK (aging_band IN ('0-2 Days', '3-7 Days', '8-30 Days', 'Over 30 Days'));

CREATE INDEX IF NOT EXISTS idx_val_txn_merchant ON validated.transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_val_txn_payref ON validated.transactions(payment_reference);
CREATE INDEX IF NOT EXISTS idx_val_txn_date ON validated.transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_val_stl_txn ON validated.settlements(transaction_id);
CREATE INDEX IF NOT EXISTS idx_val_stl_payref ON validated.settlements(payment_reference);
CREATE INDEX IF NOT EXISTS idx_val_stl_batch ON validated.settlements(settlement_batch_id);
CREATE INDEX IF NOT EXISTS idx_val_bnk_sref ON validated.bank_entries(settlement_reference);
CREATE INDEX IF NOT EXISTS idx_val_bnk_tref ON validated.bank_entries(transaction_reference);
CREATE INDEX IF NOT EXISTS idx_val_ref_txn ON validated.refunds(original_transaction_id);
CREATE INDEX IF NOT EXISTS idx_rec_mch_class ON reconciliation.reconciliation_matches(reconciliation_classification);
CREATE INDEX IF NOT EXISTS idx_rec_exc_cat ON reconciliation.exceptions(exception_category);
CREATE INDEX IF NOT EXISTS idx_rec_exc_status ON reconciliation.exceptions(resolution_status);

COMMIT;
