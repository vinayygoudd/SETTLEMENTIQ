# SettlementIQ — Power BI DAX Measures Catalog

```dax
// =============================================================================
// SettlementIQ — Authoritative Power BI DAX Measures Catalog
// File: powerbi/dax/SettlementIQ_Measures.dax
// Grain & Population Aligned 100% with PostgreSQL analytics.* Views
// =============================================================================

// --- 1. Volume Measures ---
Raw Transaction Count = COUNTROWS('stg_transactions')

Validated Ledger Transaction Count =
CALCULATE(
    COUNTROWS('Fact_Reconciliation_Matches'),
    'Fact_Reconciliation_Matches'[record_grain] = "TRANSACTION"
)

Distinct Customer Count = DISTINCTCOUNT('Fact_Transactions'[customer_id])

Distinct Merchant Count = DISTINCTCOUNT('Dim_Merchants'[merchant_id])

Validated Settlement Record Count = COUNTROWS('Fact_Settlements')

Validated Bank Entry Count = COUNTROWS('Fact_Bank_Entries')

Validated Refund Count = COUNTROWS('Fact_Refunds')

Evaluated Ecosystem Case Count = COUNTROWS('Fact_Reconciliation_Matches')

Total Exception Count = COUNTROWS('Fact_Exceptions')

Unresolved Exception Count =
CALCULATE(
    COUNTROWS('Fact_Exceptions'),
    'Fact_Exceptions'[resolution_status] IN {"OPEN", "REOPENED"}
)

Resolved Exception Count =
CALCULATE(
    COUNTROWS('Fact_Exceptions'),
    'Fact_Exceptions'[resolution_status] = "RESOLVED"
)

Reopened Exception Count =
CALCULATE(
    COUNTROWS('Fact_Exceptions'),
    'Fact_Exceptions'[resolution_status] = "REOPENED"
)

// --- 2. Financial Measures (INR Exact Decimal) ---
Total Gross Transaction Value INR = SUM('Fact_Transactions'[transaction_amount])

Total Gross Settlement Value INR = SUM('Fact_Settlements'[gross_amount])

Total Fee Value INR = SUM('Fact_Settlements'[fee_amount])

Total Net Settlement Value INR = SUM('Fact_Settlements'[net_settlement_amount])

Total Bank Credit Value INR = SUM('Fact_Bank_Entries'[credit_amount])

Total Bank Debit Value INR = SUM('Fact_Bank_Entries'[debit_amount])

Total Refund Value INR = SUM('Fact_Refunds'[refund_amount])

Expected Net Financial Value INR = SUM('Fact_Reconciliation_Matches'[expected_amount])

Observed Net Financial Value INR = SUM('Fact_Reconciliation_Matches'[observed_amount])

Net Signed Discrepancy INR = SUM('Fact_Reconciliation_Matches'[signed_variance])

Total Absolute Discrepancy INR = SUM('Fact_Reconciliation_Matches'[absolute_variance])

Outstanding Discrepancy Exposure INR =
CALCULATE(
    SUM('Fact_Exceptions'[outstanding_exposure]),
    'Fact_Exceptions'[resolution_status] IN {"OPEN", "REOPENED"}
)

Confirmed Financial Loss INR = SUM('Fact_Exceptions'[confirmed_loss])

// --- 3. Reconciliation Rate & Rule Outcome Measures ---
Matched Transaction Count =
CALCULATE(
    COUNTROWS('Fact_Reconciliation_Matches'),
    'Fact_Reconciliation_Matches'[is_matched] = 1
)

Ledger Reconciliation Rate % =
DIVIDE([Matched Transaction Count], [Validated Ledger Transaction Count], 0) * 100.0

Ecosystem Reconciliation Rate % =
DIVIDE([Matched Transaction Count], [Evaluated Ecosystem Case Count], 0) * 100.0

Exact Match Count (R1) =
CALCULATE(
    COUNTROWS('Fact_Reconciliation_Matches'),
    'Fact_Reconciliation_Matches'[reconciliation_classification] = "MATCHED_EXACT"
)

Exact Match Rate % =
DIVIDE([Exact Match Count (R1)], [Validated Ledger Transaction Count], 0) * 100.0

Tolerance Match Count (R2) =
CALCULATE(
    COUNTROWS('Fact_Reconciliation_Matches'),
    'Fact_Reconciliation_Matches'[reconciliation_classification] = "MATCHED_WITH_VARIANCE"
)

Fee Adjusted Match Count (R3) =
CALCULATE(
    COUNTROWS('Fact_Reconciliation_Matches'),
    'Fact_Reconciliation_Matches'[reconciliation_classification] = "MATCHED_FEE_ADJUSTED"
)

Multi-Part Complete Match Count (R5) =
CALCULATE(
    COUNTROWS('Fact_Reconciliation_Matches'),
    'Fact_Reconciliation_Matches'[reconciliation_classification] = "MATCHED_PARTIAL"
)

Confirmed Duplicate Count (R6) =
CALCULATE(
    COUNTROWS('Fact_Exceptions'),
    'Fact_Exceptions'[exception_category] = "DUPLICATE_CONFIRMED"
)

Confirmed Duplicate Rate % =
DIVIDE([Confirmed Duplicate Count (R6)], [Validated Settlement Record Count], 0) * 100.0

// --- 4. Exception Management & Concentration Measures ---
Exception Resolution Rate % =
DIVIDE([Resolved Exception Count], [Total Exception Count], 0) * 100.0

Average Resolution Time Days =
CALCULATE(
    AVERAGE('Fact_Exceptions'[exception_age_days]),
    'Fact_Exceptions'[resolution_status] = "RESOLVED"
)

Exposure Concentration Share % =
VAR CurrentSelectionExposure = [Outstanding Discrepancy Exposure INR]
VAR AllUnresolvedExposure =
    CALCULATE(
        [Outstanding Discrepancy Exposure INR],
        ALL('Dim_Merchants'),
        ALL('Fact_Exceptions'[exception_category]),
        ALL('Fact_Exceptions'[payment_gateway])
    )
RETURN
    DIVIDE(CurrentSelectionExposure, AllUnresolvedExposure, 0) * 100.0

Data Quality Pass Rate % =
DIVIDE([Validated Ledger Transaction Count], [Raw Transaction Count], 0) * 100.0

```
