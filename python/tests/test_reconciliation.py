def test_16_rule_r1_exact_and_r2_tolerance_matches(executed_context):
    cc = executed_context["kpi_bundle"]["class_counts"]
    assert cc["MATCHED_EXACT"] == 8440
    assert cc["MATCHED_WITH_VARIANCE"] == 360


def test_17_rule_r3_fee_adjusted_and_r5_partial_matches(executed_context):
    cc = executed_context["kpi_bundle"]["class_counts"]
    assert cc["MATCHED_FEE_ADJUSTED"] == 250
    assert cc["MATCHED_PARTIAL"] == 150
    assert cc["PARTIALLY_SETTLED"] == 60


def test_18_rule_r4_late_settlement_and_bank_timing_exceptions(executed_context):
    cc = executed_context["kpi_bundle"]["class_counts"]
    assert cc["LATE_SETTLEMENT"] == 160
    assert cc["TIMING_EXCEPTION"] == 60


def test_19_rule_r6_duplicates_and_legitimate_repeats(executed_context):
    cc = executed_context["kpi_bundle"]["class_counts"]
    assert cc["DUPLICATE_CONFIRMED"] == 100  # 70 duplicate settlements + 30 duplicate bank postings
    assert cc["DUPLICATE_CANDIDATE"] == 15
    # Verify all 80 S11 legitimate repeated customer order transactions matched cleanly as MATCHED_EXACT
    conn = executed_context["conn"]
    s11_matches = conn.execute(
        "SELECT COUNT(*) FROM reconciliation_matches WHERE source_record_id BETWEEN 'TXN_2026_008421' AND 'TXN_2026_008500' AND reconciliation_classification = 'MATCHED_EXACT'"
    ).fetchone()[0]
    assert s11_matches == 80


def test_20_rule_r7_missing_counterparts_and_r8_ambiguous(executed_context):
    cc = executed_context["kpi_bundle"]["class_counts"]
    assert cc["MISSING_SETTLEMENT"] == 140
    assert cc["MISSING_LEDGER"] == 70  # 50 orphan settlements + 20 orphan bank entries
    assert cc["MISSING_BANK_ENTRY"] == 30
    assert cc["AMBIGUOUS_MATCH"] == 35


def test_21_rule_r9_refund_reconciliation_outcomes(executed_context):
    cc = executed_context["kpi_bundle"]["class_counts"]
    assert cc["REFUND_MISMATCH"] == 40
    assert cc["UNREVERSED_REFUND"] == 15
    assert cc["MISSING_REFUND_EVIDENCE"] == 15
    assert cc["MANUAL_REVIEW"] == 15
