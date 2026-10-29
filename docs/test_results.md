# SettlementIQ — Actual Test Execution & Validation Results Report

## 1. Automated Python & SQL Test Suite Output (`27 / 27 PASSED`)
```text
==============================================================================
SettlementIQ — Automated Test Suite Execution (27 Test Assertions)
==============================================================================
PASSED  python/tests/test_data_quality.py::test_10_before_after_row_accounting_exact (0.001s)
PASSED  python/tests/test_data_quality.py::test_11_monetary_conservation_zero_unexplained_diff (0.000s)
PASSED  python/tests/test_database.py::test_12_database_tables_and_row_counts (0.001s)
PASSED  python/tests/test_database.py::test_13_exception_history_and_lifecycle_states (0.001s)
PASSED  python/tests/test_database.py::test_14_foreign_key_and_check_constraints_enforced (0.000s)
PASSED  python/tests/test_database.py::test_15_business_day_calculation_function (0.000s)
PASSED  python/tests/test_financial_controls.py::test_22_exact_decimal_rounding_half_up (0.000s)
PASSED  python/tests/test_financial_controls.py::test_23_signed_and_absolute_variance_invariants (0.058s)
PASSED  python/tests/test_financial_controls.py::test_24_unresolved_exposure_excludes_resolved_exceptions (0.003s)
PASSED  python/tests/test_ground_truth.py::test_26_ground_truth_classification_exceeds_95_pct_target (0.000s)
PASSED  python/tests/test_ground_truth.py::test_27_zero_clean_record_false_positives (0.000s)
PASSED  python/tests/test_kpis.py::test_25_kpi_catalog_completeness_and_values (0.000s)
PASSED  python/tests/test_reconciliation.py::test_16_rule_r1_exact_and_r2_tolerance_matches (0.000s)
PASSED  python/tests/test_reconciliation.py::test_17_rule_r3_fee_adjusted_and_r5_partial_matches (0.000s)
PASSED  python/tests/test_reconciliation.py::test_18_rule_r4_late_settlement_and_bank_timing_exceptions (0.000s)
PASSED  python/tests/test_reconciliation.py::test_19_rule_r6_duplicates_and_legitimate_repeats (0.003s)
PASSED  python/tests/test_reconciliation.py::test_20_rule_r7_missing_counterparts_and_r8_ambiguous (0.000s)
PASSED  python/tests/test_reconciliation.py::test_21_rule_r9_refund_reconciliation_outcomes (0.000s)
PASSED  python/tests/test_synthetic_data.py::test_01_synthetic_data_volumes_and_entities (0.000s)
PASSED  python/tests/test_synthetic_data.py::test_02_deterministic_reproducibility_same_seed (1.079s)
PASSED  python/tests/test_synthetic_data.py::test_03_all_28_planted_scenarios_present (0.002s)
PASSED  python/tests/test_validation.py::test_04_required_schema_validation_passes (0.025s)
PASSED  python/tests/test_validation.py::test_05_missing_file_raises_explicit_error (0.001s)
PASSED  python/tests/test_validation.py::test_06_missing_columns_raises_explicit_error (0.002s)
PASSED  python/tests/test_validation.py::test_07_quarantine_captures_missing_and_invalid_values (0.000s)
PASSED  python/tests/test_validation.py::test_08_cross_currency_protection_quarantines_usd_and_eur (0.004s)
PASSED  python/tests/test_validation.py::test_09_duplicate_ingestion_suppressed_idempotently (0.000s)
------------------------------------------------------------------------------
Summary: 27/27 tests passed, 0 failed in 6.02s
==============================================================================

```

## 2. Ground-Truth Classification Results by Planted Scenario (`10,000 / 10,000 = 100.00%`)

| Planted Scenario | Expected Classification | Planted Exc? | Expected Count | Detected Correct | False Positives | False Negatives | Variance Errors | Accuracy (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01_EXACT_TXN_STL_MATCH | MATCHED_EXACT | FALSE | 3987 | 3987 | 0 | 0 | 0 | 100.00% |
| S02_EXACT_STL_BANK_MATCH | MATCHED_EXACT | FALSE | 3988 | 3988 | 0 | 0 | 0 | 100.00% |
| S03_SMALL_VARIANCE_TOLERANCE | MATCHED_WITH_VARIANCE | FALSE | 300 | 300 | 0 | 0 | 0 | 100.00% |
| S04_FEE_ADJUSTED_SETTLEMENT | MATCHED_FEE_ADJUSTED | FALSE | 250 | 250 | 0 | 0 | 0 | 100.00% |
| S05_LATE_SETTLEMENT | LATE_SETTLEMENT | TRUE | 110 | 110 | 0 | 0 | 0 | 100.00% |
| S06_MISSING_SETTLEMENT | MISSING_SETTLEMENT | TRUE | 115 | 115 | 0 | 0 | 0 | 100.00% |
| S07_SETTLEMENT_WITHOUT_LEDGER | MISSING_LEDGER | TRUE | 50 | 50 | 0 | 0 | 0 | 100.00% |
| S08_BANK_WITHOUT_SETTLEMENT | MISSING_LEDGER | TRUE | 20 | 20 | 0 | 0 | 0 | 100.00% |
| S08_MISSING_BANK_COUNTERPART | MISSING_BANK_ENTRY | TRUE | 30 | 30 | 0 | 0 | 0 | 100.00% |
| S09_DUPLICATE_SETTLEMENT_CONFIRMED | DUPLICATE_CONFIRMED | TRUE | 40 | 40 | 0 | 0 | 0 | 100.00% |
| S10_DUPLICATE_BANK_ENTRY | DUPLICATE_CONFIRMED | TRUE | 30 | 30 | 0 | 0 | 0 | 100.00% |
| S11_LEGITIMATE_REPEATED_IDENTIFIER | MATCHED_EXACT | FALSE | 80 | 80 | 0 | 0 | 0 | 100.00% |
| S12_PARTIAL_SETTLEMENT_SHORTFALL | PARTIALLY_SETTLED | TRUE | 55 | 55 | 0 | 0 | 0 | 100.00% |
| S13_LEGITIMATE_MULTI_PART_SETTLEMENT | MATCHED_PARTIAL | FALSE | 150 | 150 | 0 | 0 | 0 | 100.00% |
| S14_AMBIGUOUS_CANDIDATE_MATCH | AMBIGUOUS_MATCH | TRUE | 35 | 35 | 0 | 0 | 0 | 100.00% |
| S15_MISSING_INVALID_TXN_ID | QUARANTINED_DATA_QUALITY | TRUE | 10 | 10 | 0 | 0 | 0 | 100.00% |
| S16_MISSING_MANDATORY_REFERENCE | QUARANTINED_DATA_QUALITY | TRUE | 10 | 10 | 0 | 0 | 0 | 100.00% |
| S17_INVALID_MALFORMED_AMOUNT | QUARANTINED_DATA_QUALITY | TRUE | 10 | 10 | 0 | 0 | 0 | 100.00% |
| S18_MISSING_DATE | QUARANTINED_DATA_QUALITY | TRUE | 7 | 7 | 0 | 0 | 0 | 100.00% |
| S19_INVALID_CURRENCY | QUARANTINED_DATA_QUALITY | TRUE | 8 | 8 | 0 | 0 | 0 | 100.00% |
| S20_REPEATED_INGESTION | MATCHED_EXACT | FALSE | 25 | 25 | 0 | 0 | 0 | 100.00% |
| S21_REFUND_AMOUNT_MISMATCH | REFUND_MISMATCH | TRUE | 30 | 30 | 0 | 0 | 0 | 100.00% |
| S22_MISSING_REFUND_EVIDENCE | MISSING_REFUND_EVIDENCE | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| S22_UNREVERSED_REFUND | UNREVERSED_REFUND | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| S23_LATE_ARRIVING_BANK_RECORD | TIMING_EXCEPTION | TRUE | 60 | 60 | 0 | 0 | 0 | 100.00% |
| S24_PREVIOUSLY_RESOLVED_EXCEPTION | LATE_SETTLEMENT | TRUE | 95 | 95 | 0 | 0 | 0 | 100.00% |
| S25_REOPENED_EXCEPTION | LATE_SETTLEMENT | TRUE | 25 | 25 | 0 | 0 | 0 | 100.00% |
| S26_DUPLICATE_CANDIDATE_REVIEW | DUPLICATE_CANDIDATE | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| S26_MANUAL_REVIEW_VARIANCE | MANUAL_REVIEW | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| S27_CLEAN_RECORD_NO_FALSE_POSITIVE | MATCHED_EXACT | FALSE | 300 | 300 | 0 | 0 | 0 | 100.00% |
| S28_BOUNDARY_SLA_2BDAYS | MATCHED_EXACT | FALSE | 60 | 60 | 0 | 0 | 0 | 100.00% |
| S28_BOUNDARY_TOLERANCE_1INR | MATCHED_WITH_VARIANCE | FALSE | 60 | 60 | 0 | 0 | 0 | 100.00% |

