from decimal import Decimal
from settlementiq.synthetic_data import q2


def test_22_exact_decimal_rounding_half_up():
    assert q2("100.005") == Decimal("100.01")
    assert q2("100.004") == Decimal("100.00")
    assert q2("-100.005") == Decimal("-100.01")


def test_23_signed_and_absolute_variance_invariants(executed_context):
    conn = executed_context["conn"]
    rows = conn.execute("SELECT expected_amount, observed_amount, signed_variance, absolute_variance FROM reconciliation_matches").fetchall()
    for r in rows:
        exp = Decimal(str(r["expected_amount"]))
        obs = Decimal(str(r["observed_amount"]))
        s_var = Decimal(str(r["signed_variance"]))
        a_var = Decimal(str(r["absolute_variance"]))
        assert obs - exp == s_var
        assert abs(s_var) == a_var


def test_24_unresolved_exposure_excludes_resolved_exceptions(executed_context):
    conn = executed_context["conn"]
    resolved_exp = conn.execute("SELECT SUM(CAST(outstanding_exposure AS REAL)) FROM exceptions WHERE resolution_status = 'RESOLVED'").fetchone()[0]
    assert resolved_exp == 0.0
    open_reop_rows = conn.execute("SELECT absolute_variance, outstanding_exposure FROM exceptions WHERE resolution_status IN ('OPEN', 'REOPENED')").fetchall()
    for r in open_reop_rows:
        assert Decimal(str(r["absolute_variance"])) == Decimal(str(r["outstanding_exposure"]))
