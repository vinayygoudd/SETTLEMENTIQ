# SettlementIQ — Analytical Results Interpretation & Business Recommendations

## Exception Category Breakdown (`outputs/exception_summary.csv`)

| Exception Category | Rule ID | Total Excs | Unresolved | Resolved | Signed Variance (₹) | Unresolved Exposure (₹) | Share (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MISSING_SETTLEMENT | R7_MISSING | 140 | 115 | 25 | -1266745.19 | 1073397.69 | 28.60% |
| MISSING_LEDGER | R7_MISSING | 70 | 70 | 0 | 764719.96 | 764719.96 | 20.38% |
| DUPLICATE_CONFIRMED | R6_DUPLICATE | 100 | 80 | 20 | 917182.40 | 672762.41 | 17.93% |
| PARTIALLY_SETTLED | R5_PARTIAL | 60 | 60 | 0 | -280826.42 | 280826.42 | 7.48% |
| AMBIGUOUS_MATCH | R8_AMBIGUOUS | 35 | 35 | 0 | -170213.58 | 170213.58 | 4.54% |
| MISSING_BANK_ENTRY | R7_MISSING | 30 | 30 | 0 | -138177.61 | 138177.61 | 3.68% |
| MALFORMED_AMOUNT | DQ_VALIDATION | 10 | 10 | 0 | -111271.96 | 111271.96 | 2.97% |
| INVALID_CURRENCY | DQ_VALIDATION | 8 | 8 | 0 | -110638.90 | 110638.90 | 2.95% |
| MISSING_MANDATORY_FIELD | DQ_VALIDATION | 10 | 10 | 0 | -94338.84 | 94338.84 | 2.51% |
| MISSING_DATE | DQ_VALIDATION | 7 | 7 | 0 | -87951.19 | 87951.19 | 2.34% |
| INVALID_IDENTIFIER | DQ_VALIDATION | 10 | 10 | 0 | -77395.77 | 77395.77 | 2.06% |
| UNREVERSED_REFUND | R9_REFUND | 15 | 15 | 0 | -60823.03 | 60823.03 | 1.62% |
| REFUND_MISMATCH | R9_REFUND | 40 | 30 | 10 | -68771.96 | 55471.40 | 1.48% |
| MISSING_REFUND_EVIDENCE | R9_REFUND | 15 | 15 | 0 | 29491.84 | 29491.84 | 0.79% |
| DUPLICATE_CANDIDATE | R6_DUPLICATE | 15 | 15 | 0 | 23155.03 | 23155.03 | 0.62% |
| MANUAL_REVIEW | R6_DUPLICATE | 15 | 15 | 0 | -1875.00 | 1875.00 | 0.05% |
| LATE_SETTLEMENT | R4_TIMING | 160 | 120 | 40 | 0.00 | 0.00 | 0.00% |
| TIMING_EXCEPTION | R4_TIMING | 60 | 60 | 0 | 0.00 | 0.00 | 0.00% |

