let
    Source = Csv.Document(File.Contents( pSourceFolder & "bank_entries.csv" ), [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"value_date", type date},
        {"credit_amount", Currency.Type},
        {"debit_amount", Currency.Type},
        {"signed_bank_amount", Currency.Type}
    })
in
    TypedColumns
