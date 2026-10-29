"""Database Layer & Authoritative SQL Execution Engine for SettlementIQ.

Supports:
1. PostgreSQL via psycopg2/SQLAlchemy when a local PostgreSQL server is running.
2. Local Relational SQLite Engine (executing in `/tmp` with `journal_mode=MEMORY`
   to avoid FUSE file-locking issues, then exporting a binary backup to
   `data/processed/settlementiq_authoritative.sqlite`) so that authoritative
   SQL reconciliation queries execute deterministically in any environment.
"""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import pathlib
import shutil
import sqlite3
import tempfile
from typing import Any, Dict, List

from .config import DEFAULT_CONFIG, SettlementIQConfig

TWO_PLACES = Decimal("0.01")


def _sql_b_days(start_str: str | None, end_str: str | None) -> int:
    """SQLite custom function: count Mon-Fri business days between two ISO dates."""
    if not start_str or not end_str:
        return 0
    try:
        s_dt = date.fromisoformat(start_str[:10])
        e_dt = date.fromisoformat(end_str[:10])
    except ValueError:
        return 0
    if e_dt <= s_dt:
        return 0
    curr = s_dt
    cnt = 0
    while curr < e_dt:
        curr += timedelta(days=1)
        if curr.weekday() < 5:
            cnt += 1
    return cnt


def _sql_days_between(start_str: str | None, end_str: str | None) -> int:
    """SQLite custom function: count calendar days between start_str and end_str."""
    if not start_str or not end_str:
        return 0
    try:
        s_dt = date.fromisoformat(start_str[:10])
        e_dt = date.fromisoformat(end_str[:10])
    except ValueError:
        return 0
    return max(0, (e_dt - s_dt).days)


def _sql_dec_sub(a: str | float | int | None, b: str | float | int | None) -> str:
    """Exact Decimal subtraction formatted to 2 decimal places."""
    da = Decimal(str(a or "0.00"))
    db = Decimal(str(b or "0.00"))
    return f"{(da - db).quantize(TWO_PLACES, rounding=ROUND_HALF_UP):.2f}"


def _sql_dec_abs(a: str | float | int | None) -> str:
    """Exact Decimal absolute value formatted to 2 decimal places."""
    da = abs(Decimal(str(a or "0.00")))
    return f"{da.quantize(TWO_PLACES, rounding=ROUND_HALF_UP):.2f}"


def get_sqlite_connection(db_path: pathlib.Path | str = ":memory:") -> sqlite3.Connection:
    """Open a relational SQLite connection with foreign keys and custom SQL functions."""
    if isinstance(db_path, pathlib.Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        path_str = str(db_path)
    else:
        path_str = db_path
    conn = sqlite3.connect(path_str)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = MEMORY;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.create_function("fn_business_days_between", 2, _sql_b_days)
    conn.create_function("fn_calendar_days_between", 2, _sql_days_between)
    conn.create_function("fn_dec_sub", 2, _sql_dec_sub)
    conn.create_function("fn_dec_abs", 1, _sql_dec_abs)
    return conn


def persist_sqlite_snapshot(conn: sqlite3.Connection, target_path: pathlib.Path) -> None:
    """Save the in-memory/tmp SQLite database to the target repository path."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_db = pathlib.Path(tempfile.gettempdir()) / "settlementiq_snapshot.sqlite"
    if tmp_db.exists():
        tmp_db.unlink()
    disk_conn = sqlite3.connect(str(tmp_db))
    conn.backup(disk_conn)
    disk_conn.close()
    shutil.copy2(tmp_db, target_path)


def init_and_load_database(
    raw_data: Dict[str, List[Dict[str, Any]]],
    validated_bundle: Dict[str, Any],
    config: SettlementIQConfig = DEFAULT_CONFIG,
) -> sqlite3.Connection:
    """Initialize relational database tables and load staging + validated records."""
    conn = get_sqlite_connection(":memory:")
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE stg_transactions (
        stg_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT,
        customer_id TEXT,
        merchant_id TEXT,
        payment_reference TEXT,
        order_reference TEXT,
        transaction_timestamp TEXT,
        transaction_date TEXT,
        transaction_amount TEXT,
        currency TEXT,
        payment_method TEXT,
        payment_status TEXT,
        payment_gateway TEXT,
        settlement_expected_date TEXT,
        transaction_fee TEXT,
        expected_net_amount TEXT,
        ingestion_timestamp TEXT,
        source_system TEXT,
        record_version TEXT,
        is_synthetic TEXT
    );

    CREATE TABLE quarantine_records (
        quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity TEXT NOT NULL,
        source_record_id TEXT NOT NULL,
        merchant_id TEXT NOT NULL,
        payment_gateway TEXT NOT NULL,
        quarantine_reason TEXT NOT NULL,
        quarantine_detail TEXT NOT NULL,
        raw_amount TEXT NOT NULL,
        expected_net_inr NUMERIC NOT NULL,
        currency TEXT NOT NULL,
        run_id TEXT NOT NULL
    );

    CREATE TABLE merchants (
        merchant_id TEXT PRIMARY KEY,
        merchant_name TEXT NOT NULL,
        merchant_category TEXT NOT NULL,
        onboarding_date TEXT NOT NULL,
        merchant_status TEXT NOT NULL,
        settlement_frequency TEXT NOT NULL,
        contractual_fee_rate NUMERIC NOT NULL,
        contractual_fixed_fee NUMERIC NOT NULL,
        currency TEXT NOT NULL CHECK (currency = 'INR'),
        region TEXT NOT NULL,
        operational_classification TEXT NOT NULL,
        default_payment_gateway TEXT NOT NULL,
        settlement_sla_days INTEGER NOT NULL,
        is_synthetic TEXT NOT NULL
    );

    CREATE TABLE transactions (
        transaction_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
        payment_reference TEXT NOT NULL,
        order_reference TEXT NOT NULL,
        transaction_timestamp TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        transaction_amount NUMERIC NOT NULL CHECK (transaction_amount > 0),
        currency TEXT NOT NULL CHECK (currency = 'INR'),
        payment_method TEXT NOT NULL,
        payment_status TEXT NOT NULL,
        payment_gateway TEXT NOT NULL,
        settlement_expected_date TEXT NOT NULL,
        transaction_fee NUMERIC NOT NULL CHECK (transaction_fee >= 0),
        expected_net_amount NUMERIC NOT NULL CHECK (expected_net_amount > 0),
        ingestion_timestamp TEXT NOT NULL,
        source_system TEXT NOT NULL,
        record_version INTEGER NOT NULL,
        is_synthetic TEXT NOT NULL
    );

    CREATE INDEX idx_txn_merch ON transactions(merchant_id);
    CREATE INDEX idx_txn_payref ON transactions(payment_reference);
    CREATE INDEX idx_txn_date ON transactions(transaction_date);

    CREATE TABLE settlements (
        settlement_id TEXT PRIMARY KEY,
        settlement_reference TEXT NOT NULL UNIQUE,
        transaction_id TEXT NOT NULL,
        payment_reference TEXT NOT NULL,
        merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
        settlement_batch_id TEXT NOT NULL,
        settlement_timestamp TEXT NOT NULL,
        settlement_date TEXT NOT NULL,
        gross_amount NUMERIC NOT NULL CHECK (gross_amount > 0),
        fee_amount NUMERIC NOT NULL CHECK (fee_amount >= 0),
        net_settlement_amount NUMERIC NOT NULL,
        currency TEXT NOT NULL CHECK (currency = 'INR'),
        settlement_status TEXT NOT NULL,
        settlement_type TEXT NOT NULL,
        allocation_line_no INTEGER NOT NULL,
        total_allocation_lines INTEGER NOT NULL,
        source_system TEXT NOT NULL,
        ingestion_timestamp TEXT NOT NULL,
        is_synthetic TEXT NOT NULL
    );

    CREATE INDEX idx_stl_txn ON settlements(transaction_id);
    CREATE INDEX idx_stl_payref ON settlements(payment_reference);
    CREATE INDEX idx_stl_batch ON settlements(settlement_batch_id);

    CREATE TABLE bank_entries (
        bank_entry_id TEXT PRIMARY KEY,
        bank_reference TEXT NOT NULL UNIQUE,
        settlement_reference TEXT NOT NULL,
        transaction_reference TEXT NOT NULL,
        merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
        entry_timestamp TEXT NOT NULL,
        value_date TEXT NOT NULL,
        credit_amount NUMERIC NOT NULL CHECK (credit_amount >= 0),
        debit_amount NUMERIC NOT NULL CHECK (debit_amount >= 0),
        signed_bank_amount NUMERIC NOT NULL,
        currency TEXT NOT NULL CHECK (currency = 'INR'),
        bank_description TEXT NOT NULL,
        bank_status TEXT NOT NULL,
        ingestion_timestamp TEXT NOT NULL,
        is_synthetic TEXT NOT NULL
    );

    CREATE INDEX idx_bnk_sref ON bank_entries(settlement_reference);
    CREATE INDEX idx_bnk_tref ON bank_entries(transaction_reference);

    CREATE TABLE refunds (
        refund_id TEXT PRIMARY KEY,
        original_transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
        refund_reference TEXT NOT NULL UNIQUE,
        merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
        refund_timestamp TEXT NOT NULL,
        refund_amount NUMERIC NOT NULL CHECK (refund_amount > 0),
        settled_refund_deduction NUMERIC NOT NULL CHECK (settled_refund_deduction >= 0),
        currency TEXT NOT NULL CHECK (currency = 'INR'),
        refund_status TEXT NOT NULL,
        refund_reason TEXT NOT NULL,
        settlement_reference TEXT,
        bank_reference TEXT,
        ingestion_timestamp TEXT NOT NULL,
        is_synthetic TEXT NOT NULL
    );

    CREATE INDEX idx_ref_txn ON refunds(original_transaction_id);

    CREATE TABLE reconciliation_runs (
        run_id TEXT PRIMARY KEY,
        rule_version TEXT NOT NULL,
        dataset_version TEXT NOT NULL,
        reporting_date TEXT NOT NULL,
        tolerance_inr NUMERIC NOT NULL,
        sla_business_days INTEGER NOT NULL,
        total_evaluated_cases INTEGER NOT NULL,
        eligible_ledger_count INTEGER NOT NULL,
        matched_count INTEGER NOT NULL,
        exception_count INTEGER NOT NULL,
        reconciliation_rate_pct NUMERIC NOT NULL,
        total_expected_inr NUMERIC NOT NULL,
        total_observed_inr NUMERIC NOT NULL,
        net_signed_discrepancy_inr NUMERIC NOT NULL,
        outstanding_exposure_inr NUMERIC NOT NULL,
        confirmed_loss_inr NUMERIC NOT NULL,
        run_status TEXT NOT NULL
    );

    CREATE TABLE reconciliation_matches (
        match_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES reconciliation_runs(run_id),
        rule_version TEXT NOT NULL,
        source_record_id TEXT NOT NULL UNIQUE,
        record_grain TEXT NOT NULL,
        transaction_id TEXT,
        settlement_ids TEXT,
        bank_entry_ids TEXT,
        refund_id TEXT,
        merchant_id TEXT NOT NULL,
        payment_gateway TEXT NOT NULL,
        transaction_date TEXT,
        settlement_date TEXT,
        bank_value_date TEXT,
        business_days_to_settle INTEGER NOT NULL,
        business_days_to_bank INTEGER NOT NULL,
        currency TEXT NOT NULL,
        gross_transaction_amount NUMERIC NOT NULL,
        expected_amount NUMERIC NOT NULL,
        observed_amount NUMERIC NOT NULL,
        fee_amount NUMERIC NOT NULL,
        signed_variance NUMERIC NOT NULL,
        absolute_variance NUMERIC NOT NULL,
        applied_rule_id TEXT NOT NULL,
        reconciliation_classification TEXT NOT NULL,
        is_matched INTEGER NOT NULL,
        is_exception INTEGER NOT NULL,
        exception_category TEXT NOT NULL,
        evidence_summary TEXT NOT NULL
    );

    CREATE INDEX idx_rm_class ON reconciliation_matches(reconciliation_classification);
    CREATE INDEX idx_rm_merch ON reconciliation_matches(merchant_id);

    CREATE TABLE exceptions (
        exception_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES reconciliation_runs(run_id),
        match_id TEXT NOT NULL REFERENCES reconciliation_matches(match_id),
        source_record_id TEXT NOT NULL UNIQUE,
        transaction_id TEXT,
        settlement_ids TEXT,
        bank_entry_ids TEXT,
        refund_id TEXT,
        merchant_id TEXT NOT NULL,
        payment_gateway TEXT NOT NULL,
        exception_category TEXT NOT NULL,
        applied_rule_id TEXT NOT NULL,
        rule_version TEXT NOT NULL,
        expected_amount NUMERIC NOT NULL,
        observed_amount NUMERIC NOT NULL,
        signed_variance NUMERIC NOT NULL,
        absolute_variance NUMERIC NOT NULL,
        outstanding_exposure NUMERIC NOT NULL,
        confirmed_loss NUMERIC NOT NULL,
        currency TEXT NOT NULL,
        first_detected_date TEXT NOT NULL,
        last_detected_date TEXT NOT NULL,
        exception_age_days INTEGER NOT NULL,
        aging_band TEXT NOT NULL,
        priority TEXT NOT NULL,
        resolution_status TEXT NOT NULL,
        assigned_reviewer TEXT NOT NULL,
        resolution_category TEXT NOT NULL,
        resolution_notes TEXT NOT NULL,
        resolved_timestamp TEXT,
        reopened_timestamp TEXT,
        supporting_evidence TEXT NOT NULL
    );

    CREATE INDEX idx_exc_cat ON exceptions(exception_category);
    CREATE INDEX idx_exc_stat ON exceptions(resolution_status);
    CREATE INDEX idx_exc_age ON exceptions(aging_band);

    CREATE TABLE exception_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        exception_id TEXT NOT NULL REFERENCES exceptions(exception_id),
        run_id TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT NOT NULL,
        action_by TEXT NOT NULL,
        action_timestamp TEXT NOT NULL,
        notes TEXT NOT NULL
    );
    """)

    cur.executemany(
        """INSERT INTO stg_transactions (
            transaction_id, customer_id, merchant_id, payment_reference, order_reference,
            transaction_timestamp, transaction_date, transaction_amount, currency,
            payment_method, payment_status, payment_gateway, settlement_expected_date,
            transaction_fee, expected_net_amount, ingestion_timestamp, source_system,
            record_version, is_synthetic
        ) VALUES (
            :transaction_id, :customer_id, :merchant_id, :payment_reference, :order_reference,
            :transaction_timestamp, :transaction_date, :transaction_amount, :currency,
            :payment_method, :payment_status, :payment_gateway, :settlement_expected_date,
            :transaction_fee, :expected_net_amount, :ingestion_timestamp, :source_system,
            :record_version, :is_synthetic
        )""",
        raw_data["transactions"],
    )

    cur.executemany(
        """INSERT INTO quarantine_records (
            source_entity, source_record_id, merchant_id, payment_gateway,
            quarantine_reason, quarantine_detail, raw_amount, expected_net_inr,
            currency, run_id
        ) VALUES (
            :source_entity, :source_record_id, :merchant_id, :payment_gateway,
            :quarantine_reason, :quarantine_detail, :raw_amount, :expected_net_inr,
            :currency, :run_id
        )""",
        validated_bundle["quarantined_records"],
    )

    cur.executemany(
        """INSERT INTO merchants VALUES (
            :merchant_id, :merchant_name, :merchant_category, :onboarding_date,
            :merchant_status, :settlement_frequency, :contractual_fee_rate,
            :contractual_fixed_fee, :currency, :region, :operational_classification,
            :default_payment_gateway, :settlement_sla_days, :is_synthetic
        )""",
        validated_bundle["valid_merchants"],
    )

    cur.executemany(
        """INSERT INTO transactions VALUES (
            :transaction_id, :customer_id, :merchant_id, :payment_reference,
            :order_reference, :transaction_timestamp, :transaction_date,
            :transaction_amount, :currency, :payment_method, :payment_status,
            :payment_gateway, :settlement_expected_date, :transaction_fee,
            :expected_net_amount, :ingestion_timestamp, :source_system,
            :record_version, :is_synthetic
        )""",
        validated_bundle["valid_transactions"],
    )

    cur.executemany(
        """INSERT INTO settlements VALUES (
            :settlement_id, :settlement_reference, :transaction_id,
            :payment_reference, :merchant_id, :settlement_batch_id,
            :settlement_timestamp, :settlement_date, :gross_amount,
            :fee_amount, :net_settlement_amount, :currency, :settlement_status,
            :settlement_type, :allocation_line_no, :total_allocation_lines,
            :source_system, :ingestion_timestamp, :is_synthetic
        )""",
        validated_bundle["valid_settlements"],
    )

    cur.executemany(
        """INSERT INTO bank_entries VALUES (
            :bank_entry_id, :bank_reference, :settlement_reference,
            :transaction_reference, :merchant_id, :entry_timestamp, :value_date,
            :credit_amount, :debit_amount, :signed_bank_amount, :currency,
            :bank_description, :bank_status, :ingestion_timestamp, :is_synthetic
        )""",
        validated_bundle["valid_bank_entries"],
    )

    cur.executemany(
        """INSERT INTO refunds VALUES (
            :refund_id, :original_transaction_id, :refund_reference,
            :merchant_id, :refund_timestamp, :refund_amount,
            :settled_refund_deduction, :currency, :refund_status,
            :refund_reason, :settlement_reference, :bank_reference,
            :ingestion_timestamp, :is_synthetic
        )""",
        validated_bundle["valid_refunds"],
    )

    conn.commit()
    return conn
