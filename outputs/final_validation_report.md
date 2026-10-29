# SettlementIQ — Final Verification & Ground-Truth Evaluation Report

## 1. Run Summary & Reconciliation Results (`RUN_20261025_001`)
- **Total Evaluated Ecosystem Cases**: `10,000`
- **Validated Eligible Ledger Transactions**: `9,885`
- **Successfully Reconciled (Matched) Transactions**: `9,200` (`93.07%` of validated ledger; `92.00%` of all 10,000 cases)
- **Total Detected Exceptions**: `800` (`8.00%` of all 10,000 cases)
- **Total Expected Financial Value (INR)**: `₹90541356.02`
- **Total Observed Financial Value (INR)**: `₹89806888.30`
- **Net Signed Discrepancy (INR)**: `₹-734467.72`
- **Outstanding Unresolved Discrepancy Exposure (INR)**: `₹3752510.63` (`705` unresolved exceptions: `680 OPEN` + `25 REOPENED`)
- **Confirmed Financial Loss (INR)**: `₹126151.24` (`15` independently evidenced write-off cases)

## 2. Independent Ground-Truth Classification Performance
- **Total Ground-Truth Cases Evaluated**: `10,000`
- **Planted Exception Cases**: `800`
- **Clean Baseline Cases**: `9,200`
- **Correctly Classified Cases**: `10,000` / `10,000` (`100.00%`)
- **Planted Exception Recall (Detection Rate)**: `100.00%` (Target: `>= 95.00%`)
- **Planted Exception Precision**: `100.00%`
- **Clean-Record False-Positive Rate**: `0.00%` (`0` false positives)
- **Variance Calculation Errors**: `0`

## 3. Scenario-Level Ground-Truth Verification Table

| Planted Scenario | Expected Classification | Planted Exception? | Expected Count | Detected & Correctly Classified | False Positives | False Negatives | Variance Errors | Accuracy (%) |
| :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `S01_EXACT_TXN_STL_MATCH` | `MATCHED_EXACT` | FALSE | 3,987 | 3,987 | 0 | 0 | 0 | 100.00% |
| `S02_EXACT_STL_BANK_MATCH` | `MATCHED_EXACT` | FALSE | 3,988 | 3,988 | 0 | 0 | 0 | 100.00% |
| `S03_SMALL_VARIANCE_TOLERANCE` | `MATCHED_WITH_VARIANCE` | FALSE | 300 | 300 | 0 | 0 | 0 | 100.00% |
| `S04_FEE_ADJUSTED_SETTLEMENT` | `MATCHED_FEE_ADJUSTED` | FALSE | 250 | 250 | 0 | 0 | 0 | 100.00% |
| `S05_LATE_SETTLEMENT` | `LATE_SETTLEMENT` | TRUE | 110 | 110 | 0 | 0 | 0 | 100.00% |
| `S06_MISSING_SETTLEMENT` | `MISSING_SETTLEMENT` | TRUE | 115 | 115 | 0 | 0 | 0 | 100.00% |
| `S07_SETTLEMENT_WITHOUT_LEDGER` | `MISSING_LEDGER` | TRUE | 50 | 50 | 0 | 0 | 0 | 100.00% |
| `S08_BANK_WITHOUT_SETTLEMENT` | `MISSING_LEDGER` | TRUE | 20 | 20 | 0 | 0 | 0 | 100.00% |
| `S08_MISSING_BANK_COUNTERPART` | `MISSING_BANK_ENTRY` | TRUE | 30 | 30 | 0 | 0 | 0 | 100.00% |
| `S09_DUPLICATE_SETTLEMENT_CONFIRMED` | `DUPLICATE_CONFIRMED` | TRUE | 40 | 40 | 0 | 0 | 0 | 100.00% |
| `S10_DUPLICATE_BANK_ENTRY` | `DUPLICATE_CONFIRMED` | TRUE | 30 | 30 | 0 | 0 | 0 | 100.00% |
| `S11_LEGITIMATE_REPEATED_IDENTIFIER` | `MATCHED_EXACT` | FALSE | 80 | 80 | 0 | 0 | 0 | 100.00% |
| `S12_PARTIAL_SETTLEMENT_SHORTFALL` | `PARTIALLY_SETTLED` | TRUE | 55 | 55 | 0 | 0 | 0 | 100.00% |
| `S13_LEGITIMATE_MULTI_PART_SETTLEMENT` | `MATCHED_PARTIAL` | FALSE | 150 | 150 | 0 | 0 | 0 | 100.00% |
| `S14_AMBIGUOUS_CANDIDATE_MATCH` | `AMBIGUOUS_MATCH` | TRUE | 35 | 35 | 0 | 0 | 0 | 100.00% |
| `S15_MISSING_INVALID_TXN_ID` | `QUARANTINED_DATA_QUALITY` | TRUE | 10 | 10 | 0 | 0 | 0 | 100.00% |
| `S16_MISSING_MANDATORY_REFERENCE` | `QUARANTINED_DATA_QUALITY` | TRUE | 10 | 10 | 0 | 0 | 0 | 100.00% |
| `S17_INVALID_MALFORMED_AMOUNT` | `QUARANTINED_DATA_QUALITY` | TRUE | 10 | 10 | 0 | 0 | 0 | 100.00% |
| `S18_MISSING_DATE` | `QUARANTINED_DATA_QUALITY` | TRUE | 7 | 7 | 0 | 0 | 0 | 100.00% |
| `S19_INVALID_CURRENCY` | `QUARANTINED_DATA_QUALITY` | TRUE | 8 | 8 | 0 | 0 | 0 | 100.00% |
| `S20_REPEATED_INGESTION` | `MATCHED_EXACT` | FALSE | 25 | 25 | 0 | 0 | 0 | 100.00% |
| `S21_REFUND_AMOUNT_MISMATCH` | `REFUND_MISMATCH` | TRUE | 30 | 30 | 0 | 0 | 0 | 100.00% |
| `S22_MISSING_REFUND_EVIDENCE` | `MISSING_REFUND_EVIDENCE` | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| `S22_UNREVERSED_REFUND` | `UNREVERSED_REFUND` | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| `S23_LATE_ARRIVING_BANK_RECORD` | `TIMING_EXCEPTION` | TRUE | 60 | 60 | 0 | 0 | 0 | 100.00% |
| `S24_PREVIOUSLY_RESOLVED_EXCEPTION` | `LATE_SETTLEMENT` | TRUE | 95 | 95 | 0 | 0 | 0 | 100.00% |
| `S25_REOPENED_EXCEPTION` | `LATE_SETTLEMENT` | TRUE | 25 | 25 | 0 | 0 | 0 | 100.00% |
| `S26_DUPLICATE_CANDIDATE_REVIEW` | `DUPLICATE_CANDIDATE` | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| `S26_MANUAL_REVIEW_VARIANCE` | `MANUAL_REVIEW` | TRUE | 15 | 15 | 0 | 0 | 0 | 100.00% |
| `S27_CLEAN_RECORD_NO_FALSE_POSITIVE` | `MATCHED_EXACT` | FALSE | 300 | 300 | 0 | 0 | 0 | 100.00% |
| `S28_BOUNDARY_SLA_2BDAYS` | `MATCHED_EXACT` | FALSE | 60 | 60 | 0 | 0 | 0 | 100.00% |
| `S28_BOUNDARY_TOLERANCE_1INR` | `MATCHED_WITH_VARIANCE` | FALSE | 60 | 60 | 0 | 0 | 0 | 100.00% |
