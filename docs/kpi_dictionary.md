# SettlementIQ — Central KPI Dictionary (All 42 Verified KPIs)

| KPI ID | Category | KPI Name | Actual Verified Value | Unit | Exact Formula | Eligible Population | Currency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KPI_VOL_01 | Volume | Total Raw Transaction Count | 9955 | Records | `COUNT(*) FROM raw_staging.stg_transactions` | All raw ingested transaction rows | ALL |
| KPI_VOL_02 | Volume | Validated Distinct Transaction Count | 9885 | Transactions | `COUNT(DISTINCT transaction_id) FROM validated.transactions` | Validated INR ledger transactions | INR |
| KPI_VOL_03 | Volume | Distinct Customer Count | 3200 | Customers | `COUNT(DISTINCT customer_id) FROM validated.transactions` | Validated ledger transactions | INR |
| KPI_VOL_04 | Volume | Distinct Merchant Count | 25 | Merchants | `COUNT(DISTINCT merchant_id) FROM validated.merchants` | Active onboarded merchants | INR |
| KPI_VOL_05 | Volume | Validated Settlement Record Count | 10065 | Records | `COUNT(*) FROM validated.settlements` | Deduplicated settlement lines | INR |
| KPI_VOL_06 | Volume | Validated Bank-Entry Count | 10070 | Records | `COUNT(*) FROM validated.bank_entries` | Validated bank statement rows | INR |
| KPI_VOL_07 | Volume | Validated Refund Count | 250 | Records | `COUNT(*) FROM validated.refunds` | Validated refund records | INR |
| KPI_VOL_08 | Volume | Reconciliation Evaluated Record Count | 10000 | Cases | `COUNT(*) FROM reconciliation.reconciliation_matches` | All 10,000 evaluated cases (txns + orphans + quarantined) | INR |
| KPI_VOL_09 | Volume | Total Distinct Exception Count | 800 | Exceptions | `COUNT(DISTINCT exception_id) FROM reconciliation.exceptions` | All detected reconciliation & DQ exceptions | INR |
| KPI_VOL_10 | Volume | Quarantined Source Record Count | 45 | Records | `COUNT(*) FROM raw_staging.quarantine_records` | Records failing schema/currency/amount validation | ALL |
| KPI_VOL_11 | Volume | Suppressed Duplicate Ingestion Count | 50 | Records | `Raw rows minus deduplicated staging rows` | Replay rows suppressed at ingestion (25 txn + 25 stl) | INR |
| KPI_FIN_01 | Financial | Total Validated Gross Transaction Value | 92279608.45 | INR | `SUM(transaction_amount) FROM validated.transactions` | 9,885 validated INR ledger transactions | INR |
| KPI_FIN_02 | Financial | Total Validated Gross Settlement Value | 92217404.68 | INR | `SUM(gross_amount) FROM validated.settlements` | 10,065 validated settlement lines | INR |
| KPI_FIN_03 | Financial | Total Settlement Fee & Adjustment Value | 2320513.65 | INR | `SUM(fee_amount) FROM validated.settlements` | 10,065 validated settlement lines | INR |
| KPI_FIN_04 | Financial | Total Validated Net Settlement Value | 89896891.06 | INR | `SUM(net_settlement_amount) FROM validated.settlements` | 10,065 validated settlement lines | INR |
| KPI_FIN_05 | Financial | Total Bank Credit Value | 90147315.46 | INR | `SUM(credit_amount) FROM validated.bank_entries` | 10,070 validated bank entries | INR |
| KPI_FIN_06 | Financial | Total Bank Debit Value | 0.00 | INR | `SUM(debit_amount) FROM validated.bank_entries` | 10,070 validated bank entries | INR |
| KPI_FIN_07 | Financial | Total Requested Refund Value | 473860.24 | INR | `SUM(refund_amount) FROM validated.refunds` | 250 validated refund records | INR |
| KPI_FIN_08 | Financial | Total Expected Net Financial Value | 90541356.02 | INR | `SUM(expected_amount) FROM reconciliation_matches` | All 10,000 reconciliation cases | INR |
| KPI_FIN_09 | Financial | Total Observed Net Financial Value | 89806888.30 | INR | `SUM(observed_amount) FROM reconciliation_matches` | All 10,000 reconciliation cases | INR |
| KPI_FIN_10 | Financial | Net Signed Discrepancy | -734467.72 | INR | `SUM(observed_amount - expected_amount)` | All 10,000 reconciliation cases | INR |
| KPI_FIN_11 | Financial | Total Absolute Discrepancy (All Cases) | 4203811.18 | INR | `SUM(ABS(observed_amount - expected_amount))` | All 10,000 reconciliation cases | INR |
| KPI_FIN_12 | Financial | Outstanding Discrepancy Exposure | 3752510.63 | INR | `SUM(ABS(signed_variance)) WHERE resolution_status IN ('OPEN', 'REOPENED')` | Unresolved (OPEN + REOPENED) exceptions only | INR |
| KPI_FIN_13 | Financial | Confirmed Financial Loss | 126151.24 | INR | `SUM(confirmed_loss) FROM reconciliation.exceptions` | Independently evidenced write-off cases (15 cases) | INR |
| KPI_REC_01 | Reconciliation | Overall Ledger Reconciliation Rate | 93.07 | % | `(Matched Validated Ledger Txns / Total Validated Ledger Txns) * 100` | 9,885 validated INR ledger transactions | INR |
| KPI_REC_02 | Reconciliation | Total Ecosystem Match Rate (10K Cases) | 92.00 | % | `(Matched Cases / All 10,000 Evaluated Cases) * 100` | All 10,000 evaluated ecosystem cases | INR |
| KPI_REC_03 | Reconciliation | Exact Match Rate (R1) | 85.38 | % | `(MATCHED_EXACT Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_04 | Reconciliation | Tolerance Match Rate (R2) | 3.64 | % | `(MATCHED_WITH_VARIANCE Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_05 | Reconciliation | Fee-Adjusted Match Rate (R3) | 2.53 | % | `(MATCHED_FEE_ADJUSTED Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_06 | Reconciliation | Multi-Part Complete Settlement Rate (R5) | 1.52 | % | `(MATCHED_PARTIAL Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_07 | Reconciliation | Partial Settlement Shortfall Rate (R5) | 0.61 | % | `(PARTIALLY_SETTLED Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_08 | Reconciliation | Late Settlement Rate (R4) | 1.62 | % | `(LATE_SETTLEMENT Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_09 | Reconciliation | Bank Timing Exception Rate (R4) | 0.61 | % | `(TIMING_EXCEPTION Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_10 | Reconciliation | Missing Settlement Rate (R7) | 1.42 | % | `(MISSING_SETTLEMENT Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_11 | Reconciliation | Missing Ledger Counterpart Rate (R7) | 0.70 | % | `(MISSING_LEDGER Count / All Evaluated Cases) * 100` | All 10,000 evaluated cases | INR |
| KPI_REC_12 | Reconciliation | Missing Bank-Entry Rate (R7) | 0.30 | % | `(MISSING_BANK_ENTRY Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_13 | Reconciliation | Ambiguous Match Rate (R8) | 0.35 | % | `(AMBIGUOUS_MATCH Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_REC_14 | Reconciliation | Confirmed Duplicate Rate (R6) | 0.99 | % | `(DUPLICATE_CONFIRMED Count / Validated Settlements) * 100` | 10,065 validated settlement lines | INR |
| KPI_REC_15 | Reconciliation | Duplicate Candidate Rate (R6) | 0.15 | % | `(DUPLICATE_CANDIDATE Count / Validated Settlements) * 100` | 10,065 validated settlement lines | INR |
| KPI_REC_16 | Reconciliation | Refund Exception Rate (R9) | 28.00 | % | `(Refund Exceptions / Validated Refunds) * 100` | 250 validated refund records | INR |
| KPI_REC_17 | Reconciliation | Manual Review Rate | 0.15 | % | `(MANUAL_REVIEW Count / Validated Ledger Txns) * 100` | Validated INR ledger transactions | INR |
| KPI_EXC_01 | Exception Management | Total Unresolved Exceptions (OPEN + REOPENED) | 705 | Exceptions | `COUNT(*) WHERE resolution_status IN ('OPEN', 'REOPENED')` | 800 total detected exceptions | INR |
| KPI_EXC_02 | Exception Management | Total Resolved Exceptions | 95 | Exceptions | `COUNT(*) WHERE resolution_status = 'RESOLVED'` | 800 total detected exceptions | INR |
| KPI_EXC_03 | Exception Management | Reopened Exception Count | 25 | Exceptions | `COUNT(*) WHERE resolution_status = 'REOPENED'` | 800 total detected exceptions | INR |
| KPI_EXC_04 | Exception Management | Exception Resolution Rate | 11.88 | % | `(Resolved Exceptions / Total Exceptions) * 100` | 800 total detected exceptions | INR |
| KPI_EXC_05 | Exception Management | Average Resolution Time | 4.00 | Days | `AVG(exception_age_days) WHERE resolution_status = 'RESOLVED'` | 95 resolved exceptions | N/A |
| KPI_EXC_06 | Exception Management | Median Resolution Time | 4.00 | Days | `MEDIAN(exception_age_days) WHERE resolution_status = 'RESOLVED'` | 95 resolved exceptions | N/A |
| KPI_DQ_01 | Data Quality | Data Quality Pass Rate (Transactions) | 99.30 | % | `(Validated Txns / Raw Ingested Txns) * 100` | 9,955 raw ingested transaction rows | ALL |
| KPI_DQ_02 | Data Quality | Mandatory-Field Completeness Rate | 99.83 | % | `((Raw Rows - Missing Mandatory/Date Rows) / Raw Rows) * 100` | 9,955 raw ingested transaction rows | ALL |
| KPI_DQ_03 | Data Quality | Quarantine Rate | 0.45 | % | `(Quarantined Rows / Raw Ingested Txns) * 100` | 9,955 raw ingested transaction rows | ALL |
| KPI_GT_01 | Ground Truth QA | Overall Classification Accuracy (10K Cases) | 100.00 | % | `(Correctly Classified Cases / 10,000 Total Cases) * 100` | All 10,000 ground-truth cases | N/A |
| KPI_GT_02 | Ground Truth QA | Planted Exception Recall (Detection Rate) | 100.00 | % | `(True Positives / Total Planted Exceptions) * 100` | 800 planted exception cases | N/A |
| KPI_GT_03 | Ground Truth QA | Planted Exception Precision | 100.00 | % | `(True Positives / (True Positives + False Positives)) * 100` | All flagged exceptions | N/A |
| KPI_GT_04 | Ground Truth QA | Clean-Record False-Positive Rate | 0.00 | % | `(Clean Records Flagged as Exception / 9,200 Clean Cases) * 100` | 9,200 clean match cases | N/A |

