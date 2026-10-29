import sqlite3
import pytest
from settlementiq.database import _sql_b_days, get_sqlite_connection


def test_12_database_tables_and_row_counts(executed_context):
    conn = executed_context["conn"]
    assert conn.execute("SELECT COUNT(*) FROM merchants").fetchone()[0] == 25
    assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 9885
    assert conn.execute("SELECT COUNT(*) FROM settlements").fetchone()[0] == 10065
    assert conn.execute("SELECT COUNT(*) FROM bank_entries").fetchone()[0] == 10070
    assert conn.execute("SELECT COUNT(*) FROM refunds").fetchone()[0] == 250
    assert conn.execute("SELECT COUNT(*) FROM reconciliation_matches").fetchone()[0] == 10000
    assert conn.execute("SELECT COUNT(*) FROM exceptions").fetchone()[0] == 800


def test_13_exception_history_and_lifecycle_states(executed_context):
    conn = executed_context["conn"]
    res = dict(conn.execute("SELECT resolution_status, COUNT(*) FROM exceptions GROUP BY resolution_status").fetchall())
    assert res["OPEN"] == 680
    assert res["RESOLVED"] == 95
    assert res["REOPENED"] == 25
    hist_cnt = conn.execute("SELECT COUNT(*) FROM exception_history").fetchone()[0]
    assert hist_cnt == 800 + 95 + 25 + 25


def test_14_foreign_key_and_check_constraints_enforced(executed_context):
    conn = executed_context["conn"]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO transactions VALUES ('TXN_BAD','C1','MERCH_1001','P1','O1','2026-09-01','2026-09-01',-10.0,'INR','UPI','CAPTURED','GW','2026-09-03',1.0,10.0,'2026-10-25','SYS',1,'TRUE')"
        )


def test_15_business_day_calculation_function():
    # Friday 2026-09-04 to Tuesday 2026-09-08 is 2 business days (Mon + Tue)
    assert _sql_b_days("2026-09-04", "2026-09-08") == 2
    assert _sql_b_days("2026-09-08", "2026-09-04") == 0
