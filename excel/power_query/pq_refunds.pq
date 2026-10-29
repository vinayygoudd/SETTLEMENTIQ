let
    Source = Csv.Document(File.Contents( pSourceFolder & "refunds.csv" ), [Delimiter=",", Columns=14, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"refund_amount", Currency.Type},
        {"settled_refund_deduction", Currency.Type}
    })
in
    TypedColumns
