# SettlementIQ — Before-and-After Data Quality Report

## 1. Executive Summary of Data Quality & Cleaning
- **Dataset Version**: `v1.0.0-SYNTHETIC-10K` (Seed `42`)
- **Raw Transaction Rows Ingested**: `9,955`
- **Validated INR Ledger Transactions**: `9,885` (`99.30%` Pass Rate)
- **Quarantined Invalid Records**: `45` (`0.45%` Quarantine Rate)
- **Suppressed Repeated Ingestion Replay Rows**: `25` transactions + `25` settlements (`50` total duplicate replay rows suppressed idempotently)
- **Monetary Conservation Variance (INR)**: `₹0.00` (Zero unexplained difference)

## 2. Before-and-After Dataset Measurements

| Dataset | Raw Rows | Validated Rows | Quarantined Rows | Suppressed Replay Rows | Raw INR Value (₹) | Validated INR Value (₹) | Quarantined INR Value (₹) | Suppressed Replay INR (₹) | Unexplained Diff (₹) | DQ Pass Rate (%) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TRANSACTIONS | 9,955 | 9,885 | 45 | 25 | 92603168.27 | 92279608.45 | 261072.57 | 62487.25 | 0.00 | 99.30% |
| SETTLEMENTS | 10,090 | 10,065 | 0 | 25 | 89957943.34 | 89896891.06 | 0.00 | 61052.28 | 0.00 | 99.75% |
| BANK_ENTRIES | 10,070 | 10,070 | 0 | 0 | 90147315.46 | 90147315.46 | 0.00 | 0.00 | 0.00 | 100.00% |
| REFUNDS | 250 | 250 | 0 | 0 | 473860.24 | 473860.24 | 0.00 | 0.00 | 0.00 | 100.00% |
| MERCHANTS | 25 | 25 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 100.00% |

## 3. Quarantined Defect Breakdown (45 Records Preserved in `raw_staging.quarantine_records`)
- **Invalid Identifiers (`S15_MISSING_INVALID_TXN_ID`)**: `10` records failing `^TXN_[0-9]{4}_[0-9]{6}$`
- **Missing Mandatory References (`S16_MISSING_MANDATORY_REFERENCE`)**: `10` records missing `merchant_id` or `payment_reference`
- **Invalid / Non-Positive Amounts (`S17_INVALID_MALFORMED_AMOUNT`)**: `10` records with negative gross amounts (`-450.00 INR`)
- **Missing Dates (`S18_MISSING_DATE`)**: `7` records with blank `transaction_date`
- **Unapproved Foreign Currencies (`S19_INVALID_CURRENCY`)**: `8` records (`4 USD` totaling `$56,925.52`, `4 EUR` totaling `€56,234.36`) isolated to prevent cross-currency aggregation
