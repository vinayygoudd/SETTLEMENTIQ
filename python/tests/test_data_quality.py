from decimal import Decimal


def test_10_before_after_row_accounting_exact(executed_context):
    sm = executed_context["dq_report"]["summary_metrics"]
    assert sm["raw_transaction_rows"] == (
        sm["validated_transaction_rows"]
        + sm["quarantined_transaction_rows"]
        + sm["suppressed_duplicate_txn_rows"]
    )


def test_11_monetary_conservation_zero_unexplained_diff(executed_context):
    sm = executed_context["dq_report"]["summary_metrics"]
    assert Decimal(sm["txn_conservation_diff_inr"]) == Decimal("0.00")
    assert Decimal(sm["stl_conservation_diff_inr"]) == Decimal("0.00")
