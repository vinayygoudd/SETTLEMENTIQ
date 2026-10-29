# SettlementIQ — Deterministic Matching-Rule Specification (`RULE_SET_2026_10_v1`)

## 1. Explicit Rule Precedence Table
| Precedence Rank | Rule ID | Rule Family | Outcome Classifications | Verified Case Count |
| :---: | :--- | :--- | :--- | ---: |
| `1` | `DQ_VALIDATION` | Pre-Reconciliation Quarantine | `QUARANTINED_DATA_QUALITY` | `45` |
| `2` | `R6_DUPLICATE` | Duplicate Detection | `DUPLICATE_CONFIRMED` (`100`), `DUPLICATE_CANDIDATE` (`15`), `MANUAL_REVIEW` (`15`) | `130` |
| `3` | `R8_AMBIGUOUS` | Ambiguous Candidate Collision | `AMBIGUOUS_MATCH` | `35` |
| `4` | `R9_REFUND` | Refund Lifecycle Reconciliation | `REFUND_MISMATCH` (`40`), `UNREVERSED_REFUND` (`15`), `MISSING_REFUND_EVIDENCE` (`15`) | `70` |
| `5` | `R5_PARTIAL` | Multi-Line Partial Settlement | `MATCHED_PARTIAL` (`150`), `PARTIALLY_SETTLED` (`60`) | `210` |
| `6` | `R7_MISSING` | Missing Counterpart (Anti-Join) | `MISSING_SETTLEMENT` (`140`), `MISSING_LEDGER` (`70`), `MISSING_BANK_ENTRY` (`30`) | `240` |
| `7` | `R4_TIMING` | Business-Day SLA Window | `LATE_SETTLEMENT` (`160`), `TIMING_EXCEPTION` (`60`) | `220` |
| `8` | `R3_FEE_ADJUSTED` | Documented Fee Adjustment | `MATCHED_FEE_ADJUSTED` | `250` |
| `9` | `R1_EXACT` | Exact 1:1 Net & SLA Match | `MATCHED_EXACT` | `8,440` |
| `10` | `R2_TOLERANCE` | Minor Variance Within `±₹1.00` | `MATCHED_WITH_VARIANCE` | `360` |
| **Total** | **All Rules** | **Mutually Exclusive & Exhaustive** | **9,200 Matched + 800 Exceptions** | **10,000** |
