# SettlementIQ — Business Requirements Document (BRD)

## 1. Executive Summary
**SettlementIQ** is an end-to-end FinTech payment settlement, reconciliation, and financial leakage analytics solution built across **Advanced Microsoft Excel & VBA**, **Python**, **PostgreSQL**, and **Power BI**. It reconciles internal payment switch ledger transactions against payment gateway settlement reports, escrow/nodal bank statement entries, refund logs, and merchant fee contracts across a 100% synthetic 10,000-case ecosystem (`Seed=42`).

## 2. Business Problem
High-volume digital payment businesses experience daily operational discrepancies between captured customer payments, gateway payouts, bank statement credits, and refund deductions. Simple identifier-and-amount matching fails because:
1. **Contractual Fee Deductions & GST**: Gateways deduct merchant discount rates (MDR), fixed per-transaction fees, and 18% GST prior to payout.
2. **Legitimate Multi-Part Settlements**: Split captures and installment settlements legitimately span multiple payout lines (`MATCHED_PARTIAL`).
3. **Timing Asynchrony**: Standard `T+1` and `T+2` settlement cycles and bank clearing cutoffs create timing differences that must be separated from genuine missing funds.
4. **Operational & Data Defects**: Duplicate settlements, duplicate bank postings, unreversed failed refunds, ambiguous unlinked payouts, repeated file ingestions, and foreign-currency records create financial leakage risk if not systematically isolated.

## 3. Stakeholders & Target Users
- **Settlement Operations Analysts**: Investigate daily unmatched transactions, missing settlements, and duplicate payouts.
- **Reconciliation & Financial Controls Analysts**: Verify stage-by-stage monetary conservation and reconcile net discrepancies.
- **Merchant Operations Teams**: Track merchant-level exposure concentration and resolve contractual MDR/surcharge disputes.
- **Finance Managers & BI Analysts**: Monitor reconciliation rates, exception aging bands (`0-2`, `3-7`, `8-30`, `>30` days), unresolved exposure (`₹37,52,510.63`), and confirmed financial write-offs (`₹1,26,151.24`).

## 4. Functional Requirements & Traceability Matrix

| Req ID | Requirement Description | Responsible Layer | Verification Test ID | Status |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Generate reproducible 100% synthetic datasets (10,000 cases, 28 planted scenarios, `Seed=42`) | Python (`synthetic_data.py`) | `test_01`, `test_02`, `test_03` | VERIFIED |
| `FR-02` | Validate source file existence, required schemas, mandatory fields, dates, amounts, and single-currency INR rules | Python (`ingestion.py`, `validation.py`) & SQL (`04_data_quality.sql`) | `test_04` – `test_08` | VERIFIED |
| `FR-03` | Prevent repeated source file ingestion from duplicating validated records (`S20_REPEATED_INGESTION`) | Python (`validation.py`) & SQL (`ROW_NUMBER()`) | `test_09`, `test_10` | VERIFIED |
| `FR-04` | Implement deterministic matching rules `R1` through `R9` with explicit rule precedence and versioning (`RULE_SET_2026_10_v1`) | PostgreSQL / Relational SQL (`05_reconciliation.sql`) | `test_16` – `test_21` | VERIFIED |
| `FR-05` | Distinguish Signed Variance, Absolute Variance, Unresolved Discrepancy Exposure, and Confirmed Financial Loss using exact Decimal types | SQL (`NUMERIC(18,2)`) & Python (`Decimal`) | `test_22` – `test_24` | VERIFIED |
| `FR-06` | Deliver a 15-worksheet Excel operational workbook, Power Query M definitions, and 8 modular VBA automation modules | Excel (`SettlementIQ_Reconciliation_Dashboard.xlsx` & `vba_source/`) | `validate_excel.py` | VERIFIED |
| `FR-07` | Deliver Power BI Executive Overview and Exception Investigation designs, DAX measures, Power Query scripts, and verified visual previews | Power BI (`powerbi/`) | Cross-Platform Audit | VERIFIED |
| `FR-08` | Achieve `>= 95.0%` classification accuracy on the independently maintained ground-truth evaluation dataset | Python (`kpi_calculations.py`) | `test_26`, `test_27` (`100.00%`) | VERIFIED |

## 5. Non-Negotiable Scope & Exclusions
- **100% Synthetic Data**: Zero real customer PII, zero live bank credentials, zero public/hybrid datasets.
- **No Machine Learning or AI**: Deterministic rules and accounting controls only; no predictive fraud modeling or LLMs.
- **No Unnecessary Cloud/Web Frameworks**: Focused strictly on Excel/VBA, Python, PostgreSQL/SQL, and Power BI.
