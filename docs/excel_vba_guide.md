# SettlementIQ — Advanced Excel & VBA Implementation Guide

## 1. Workbook Architecture (15 Worksheets)
File: `excel/SettlementIQ_Reconciliation_Dashboard.xlsx` (and `excel/settlementiq_workbook.xlsx`)

| Sheet # | Worksheet Name | Purpose & Formula Highlights | Row Count |
| :---: | :--- | :--- | ---: |
| `1` | `Control_Panel` | Operational status, run metadata, tolerance/SLA parameters, and audit status | `11` |
| `2` | `Executive_Dashboard` | Exception category breakdown, dynamic exposure share formulas (`=H2/$H$19`), and embedded column chart | `20` |
| `3` | `Transactions` | Sample 200 internal ledger records with formula fee verification (`=ROUND(G2-H2-I2, 2)`) and chart | `202` |
| `4` | `Settlements` | Sample 200 gateway settlement records with net payout verification (`=ROUND(G2-H2-I2, 2)`) and chart | `202` |
| `5` | `Bank_Entries` | Sample 200 bank statement entries with signed bank movement formula (`=ROUND(G2-H2, 2)`) and chart | `202` |
| `6` | `Refunds` | Sample 200 refund records with requested-vs-deducted variance formula (`=ROUND(H2-G2, 2)`) and chart | `202` |
| `7` | `Merchants` | All 25 merchants with MDR rates, fixed fees, exception counts, exposure totals, and chart | `27` |
| `8` | `Data_Quality` | Before-and-after cleaning counts, row conservation check (`=B2-(C2+D2+E2)`), and monetary conservation check | `7` |
| `9` | `Reconciliation` | 150 reconciliation cases with formula signed variance, absolute variance, and `Config!$B$2` tolerance check | `152` |
| `10` | `Exception_Register` | Top 250 prioritized exceptions with conditional unresolved exposure formula (`=IF(L2="RESOLVED",0,ABS(I2))`) | `252` |
| `11` | `KPI_Results` | All 42 verified KPIs across Volume, Financial, Reconciliation, Exception, DQ, and Ground-Truth QA | `43` |
| `12` | `Summary` | Unified reconciliation & exception summary table with totals and embedded chart | `23` |
| `13` | `Run_Log` | Timestamped audit trail of pipeline and workbook recalculation steps | `8` |
| `14` | `Config` | Central parameter registry (`TOLERANCE_INR = 1.00`, `SLA_BUSINESS_DAYS = 2`, `GST_TAX_RATE = 0.1800`) | `6` |
| `15` | `Data_Dictionary` | Schema and field definitions embedded inside the workbook | `15` |

## 2. VBA Modules (`excel/vba_source/*.bas`) & Honest `.xlsm` Disclosure
We provide 8 complete, modular VBA source files in `excel/vba_source/`:
1. `modMain.bas`: Master orchestrator (`RunFullSettlementIQWorkflow`).
2. `modImport.bas`: CSV file existence validation (`ImportSyntheticCSVFiles`).
3. `modValidation.bas`: Worksheet inventory and control-total verification (`VerifySourceRowCountsAndControlTotals`).
4. `modReconciliation.bas`: Formula rebuild and exception register refresh (`UpdateExceptionRegisterSummary`).
5. `modRefresh.bas`: Full workbook calculation and PivotCache refresh (`RefreshAllFormulasAndPivots`).
6. `modReporting.bas`: Timestamped PDF export of `Exception_Register` (`ExportTimestampedExceptionReport`).
7. `modLogging.bas`: Structured audit logging to `Run_Log` (`LogRunEvent`).
8. `modUtilities.bas`: Identifier normalization and variance helpers.

### How to Enable `.xlsm` Macros in Desktop Microsoft Excel (Windows/macOS)
Because Microsoft Excel's proprietary `vbaProject.bin` OLE compiler is not installed in the Linux container environment—and per the strict prompt rule (*"Do not substitute a normal `.xlsx` file renamed to `.xlsm`"*):
1. Open `excel/SettlementIQ_Reconciliation_Dashboard.xlsx` in Desktop Microsoft Excel.
2. Press `Alt + F11` to open the VBA Editor, select **File -> Import File...**, and import the 8 `.bas` modules from `excel/vba_source/`.
3. Save the workbook via **File -> Save As -> Excel Macro-Enabled Workbook (`SettlementIQ_Reconciliation_Dashboard.xlsm`)**.
