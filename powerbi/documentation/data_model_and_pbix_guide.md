# SettlementIQ — Power BI Star Schema Model & Native `.pbix` Assembly Guide

## 1. Honest Disclosure Regarding Native `.pbix` Binary Generation
In accordance with Section 4.3, Section 13, and Section 22 of the project specification:
- Power BI Desktop (`PBIDesktop.exe`) is a Windows-only proprietary application and is not installed in the Linux container execution environment.
- Per the strict non-negotiable rule (*"Do not create an arbitrary file and rename it to `.pbix`"*), we have **not** created a fake or renamed `.pbix` binary.
- Instead, we have delivered 100% of the verified SQL analytical views (`sql/07_analytics_views.sql`), DAX measure definitions (`powerbi/dax/SettlementIQ_Measures.dax`), Power Query M scripts (`powerbi/power_query/SettlementIQ_PowerQuery.pq`), custom JSON report theme (`powerbi/documentation/settlementiq_theme.json`), and actual data-driven visual renders of Page 1 (`executive_dashboard_overview.png`) and Page 2 (`powerbi_page2_exception_investigation.png`).

## 2. Star Schema Data Model Specification
- **Dimension Tables**:
  - `Dim_Date` (Grain: 1 row per calendar day `2026-09-01` to `2026-10-31`, marking Mon–Fri business days)
  - `Dim_Merchants` (Grain: 1 row per `merchant_id`, 25 merchants across 4 gateways and 5 regions)
  - `Dim_Exception_Category` (Grain: 1 row per `exception_category` / `applied_rule_id`)
- **Fact Tables**:
  - `Fact_Reconciliation_Matches` (Grain: 1 row per evaluated case, 10,000 rows; 1:1 with `source_record_id`)
  - `Fact_Exceptions` (Grain: 1 row per detected exception, 800 rows; 1:1 with `exception_id`)
  - `Fact_Data_Quality` (Grain: 1 row per source dataset, 5 rows)
- **Relationships & Filter Propagation**:
  - `Dim_Merchants[merchant_id]` (1) -> (*) `Fact_Reconciliation_Matches[merchant_id]` (Single-direction filter)
  - `Dim_Merchants[merchant_id]` (1) -> (*) `Fact_Exceptions[merchant_id]` (Single-direction filter)
  - `Dim_Date[Date]` (1) -> (*) `Fact_Reconciliation_Matches[transaction_date]` (Active)
  - `Dim_Date[Date]` (1) -> (*) `Fact_Exceptions[first_detected_date]` (Active)
  - **Double-Counting Prevention**: Never join `Fact_Settlements` (multi-line) directly to `Fact_Bank_Entries` (multi-line) in a many-to-many relationship; all cross-layer aggregations are pre-reconciled at the authoritative `source_record_id` grain in `reconciliation.reconciliation_matches`.
