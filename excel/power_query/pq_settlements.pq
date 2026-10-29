let
    Source = Csv.Document(File.Contents( pSourceFolder & "settlements.csv" ), [Delimiter=",", Columns=19, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"settlement_date", type date},
        {"gross_amount", Currency.Type},
        {"fee_amount", Currency.Type},
        {"net_settlement_amount", Currency.Type},
        {"allocation_line_no", Int64.Type},
        {"total_allocation_lines", Int64.Type}
    }),
    Deduplicated = Table.Distinct(TypedColumns, {"settlement_id"})
in
    Deduplicated
