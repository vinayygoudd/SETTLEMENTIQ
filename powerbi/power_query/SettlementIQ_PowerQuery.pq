// =============================================================================
// SettlementIQ — Power BI Power Query M Data Model Loader
// Connects to PostgreSQL analytics & reconciliation schemas (or CSV baseline exports)
// =============================================================================
let
    // Option A: PostgreSQL Authoritative Database Connection
    // SourceDB = PostgreSQL.Database("localhost:5432", "settlementiq"),
    // Fact_Exceptions = SourceDB{[Schema="reconciliation",Item="exceptions"]}[Data],

    // Option B: Portable Baseline CSV Connection (Reproducible Offline Mode)
     loadCsv = (fileName as text) =>
        let
            Raw = Csv.Document(File.Contents(pProjectRoot & fileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
            Promoted = Table.PromoteHeaders(Raw, [PromoteAllScalars=true])
        in
            Promoted,

    Dim_Merchants = loadCsv("data/synthetic_inputs/merchants.csv"),
    Fact_Reconciliation_Summary = loadCsv("outputs/reconciliation_summary.csv"),
    Fact_Exceptions = loadCsv("data/sample_outputs/exceptions_register_full.csv"),
    Fact_KPI_Results = loadCsv("outputs/kpi_results.csv"),
    Fact_Data_Quality = loadCsv("outputs/data_quality_before_after.csv")
in
    Fact_Exceptions
