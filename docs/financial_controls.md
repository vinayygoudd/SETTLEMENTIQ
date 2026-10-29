# SettlementIQ — Financial Controls & Accounting Governance

## 1. Verified Stage-by-Stage Financial Control Totals (`outputs/financial_controls.csv`)

| Control ID | Control Stage | Currency | Expected Control Total | Observed Reconstructed Total | Unexplained Diff | Status |
| --- | --- | --- | --- | --- | --- | --- |
| FC_01 | Raw vs Validated INR Ledger Gross Conservation | INR | 92603168.27 | 92603168.27 | 0.00 | PASS_ZERO_UNEXPLAINED_DIFF |
| FC_02 | Cross-Currency Isolation Control (USD Quarantined) | USD | 56925.52 | 56925.52 | 0.00 | PASS_ISOLATED |
| FC_03 | Cross-Currency Isolation Control (EUR Quarantined) | EUR | 56234.36 | 56234.36 | 0.00 | PASS_ISOLATED |
| FC_04 | Raw vs Validated Settlement Net Conservation | INR | 89957943.34 | 89957943.34 | 0.00 | PASS_ZERO_UNEXPLAINED_DIFF |
| FC_05 | Reconciliation Signed Variance Identity (Observed - Expected) | INR | -734467.72 | -734467.72 | 0.00 | PASS_EXACT_DECIMAL_IDENTITY |
| FC_06 | Unresolved Exposure vs Confirmed Financial Loss Separation | INR | 3752510.63 | 3752510.63 | 0.00 | PASS_SEPARATED |


## 2. Distinction Between Exposure and Confirmed Financial Loss
- **Net Signed Discrepancy (`-₹7,34,467.72`)**: Algebraic sum of `Observed Amount − Expected Amount` across all 10,000 cases.
- **Outstanding Discrepancy Exposure (`₹37,52,510.63`)**: Sum of `ABS(Signed Variance)` strictly for the **705 unresolved exceptions** (`680 OPEN` + `25 REOPENED`).
- **Confirmed Financial Loss (`₹1,26,151.24`)**: Restricted strictly to the **15 independently evidenced write-off cases**.
