# SettlementIQ — Technical Design Document (TDD)

## 1. End-to-End Execution Flow
1. **Deterministic Data Generation (`settlementiq.synthetic_data`)**:
   - Generates `merchants.csv` (25 rows), `transactions.csv` (9,955 rows), `settlements.csv` (10,090 rows), `bank_entries.csv` (10,070 rows), `refunds.csv` (250 rows), and isolated `ground_truth.csv` (10,000 rows).
2. **Schema & Record Validation (`settlementiq.ingestion`, `settlementiq.validation`)**:
   - Verifies required headers across all files.
   - Quarantines 45 defective transaction records (`10` invalid IDs, `10` missing mandatory references, `10` negative amounts, `7` missing dates, `8` foreign currency `USD`/`EUR` records) into `quarantine_records`.
   - Suppresses 50 exact replay rows (`25` transactions, `25` settlements) from `S20_REPEATED_INGESTION`.
3. **Database Loading & Authoritative SQL Reconciliation (`settlementiq.database`, `settlementiq.reconciliation_runner`)**:
   - Loads `9,885` validated transactions, `10,065` validated settlements, `10,070` bank entries, `250` refunds, and `25` merchants into relational tables with primary/foreign/check constraints.
   - Executes the CTE-based SQL reconciliation engine evaluating all `10,000` mutually exclusive cases (`9,885` ledger transactions + `50` orphan settlements + `20` orphan bank entries + `45` quarantined records).
4. **Independent Ground-Truth Verification & KPI Calculation (`settlementiq.kpi_calculations`)**:
   - Computes 42 KPIs across 6 families and compares actual SQL classifications against `ground_truth.csv`.
5. **Reporting, Visualization & Workbook Build (`settlementiq.export`, `settlementiq.visualization`)**:
   - Exports CSV/JSON/Markdown reports, generates high-resolution charts/dashboard previews, and builds the 15-sheet Excel workbook recalculated via headless LibreOffice Calc.

## 2. Authoritative Equations & Sign Conventions
- **Expected Net Settlement (`INR`)**:
  - `Expected MDR Fee = ROUND(Gross * Contractual Rate + Fixed Fee, 2)`
  - `Expected GST Tax = ROUND(Expected MDR Fee * 0.18, 2)`
  - `Expected Net Amount = Gross - Expected MDR Fee - Expected GST Tax - Valid Refund Request`
- **Signed Variance (`INR`)**:
  - `Signed Variance = Observed Amount - Expected Amount`
- **Absolute Variance (`INR`)**:
  - `Absolute Variance = ABS(Signed Variance)`
- **Outstanding Discrepancy Exposure (`INR`)**:
  - `Outstanding Exposure = SUM(ABS(Signed Variance))` strictly where `resolution_status IN ('OPEN', 'REOPENED')`.
