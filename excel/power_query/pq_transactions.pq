let
    Source = Csv.Document(File.Contents( pSourceFolder & "transactions.csv" ), [Delimiter=",", Columns=19, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TrimmedIds = Table.TransformColumns(PromotedHeaders, {
        {"transaction_id", Text.Trim, type text},
        {"merchant_id", Text.Trim, type text},
        {"payment_reference", Text.Trim, type text},
        {"currency", Text.Trim, type text}
    }),
    TypedColumns = Table.TransformColumnTypes(TrimmedIds, {
        {"transaction_amount", Currency.Type},
        {"transaction_fee", Currency.Type},
        {"expected_net_amount", Currency.Type}
    }),
    AddDQFlag = Table.AddColumn(TypedColumns, "DQ_Validation_Status", each
        if not Text.StartsWith([transaction_id], "TXN_") then "QUARANTINE_INVALID_ID"
        else if [merchant_id] = "" or [payment_reference] = "" then "QUARANTINE_MISSING_MANDATORY"
        else if [transaction_date] = "" then "QUARANTINE_MISSING_DATE"
        else if [currency] <> "INR" then "QUARANTINE_FOREIGN_CURRENCY"
        else if [transaction_amount] <= 0 then "QUARANTINE_INVALID_AMOUNT"
        else "VALID", type text)
in
    AddDQFlag
