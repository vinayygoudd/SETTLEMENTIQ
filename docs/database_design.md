# SettlementIQ — Relational Database Design (`sql/01_schema.sql` – `sql/11_performance_analysis.sql`)

## Four-Layer Relational Schema Architecture
1. **`raw_staging` Schema**: `stg_merchants`, `stg_transactions`, `stg_settlements`, `stg_bank_entries`, `stg_refunds`, `quarantine_records` (45 rows).
2. **`validated` Schema**: `merchants` (25), `transactions` (9,885), `settlements` (10,065), `bank_entries` (10,070), `refunds` (250).
3. **`reconciliation` Schema**: `reconciliation_runs`, `reconciliation_matches` (10,000), `match_evidence`, `exceptions` (800), `exception_history` (945).
4. **`analytics` Schema**: `data_quality_results`, `kpi_snapshots`, `vw_reconciliation_overview`, `vw_merchant_exposure`.
