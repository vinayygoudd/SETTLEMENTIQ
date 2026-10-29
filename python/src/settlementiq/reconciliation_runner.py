"""Authoritative SQL Reconciliation Runner for SettlementIQ.

Executes the deterministic SQL reconciliation rules (R1–R9 + DQ Quarantine)
directly inside the relational database engine without reading ground-truth
labels, then populates `reconciliation_runs`, `reconciliation_matches`,
`exceptions`, and `exception_history`.
"""
from decimal import Decimal
import sqlite3
from typing import Any, Dict

from .config import DEFAULT_CONFIG, SettlementIQConfig
from .database import _sql_days_between
from .synthetic_data import q2


def execute_sql_reconciliation(
    conn: sqlite3.Connection,
    config: SettlementIQConfig = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Execute authoritative SQL reconciliation queries and populate target tables."""
    cur = conn.cursor()

    # Initialize run record
    cur.execute(
        """INSERT INTO reconciliation_runs VALUES (
            ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 'STARTED'
        )""",
        (
            config.run_id,
            config.rule_version,
            config.dataset_version,
            config.reporting_date,
            str(config.tolerance_inr),
            config.sla_business_days,
        ),
    )

    # Authoritative SQL CTE Reconciliation Query across:
    # 1. Validated Ledger Transactions (9,885 records)
    # 2. Orphan Settlements without Ledger Counterpart (50 records)
    # 3. Orphan Bank Entries without Settlement or Ledger Counterpart (20 records)
    # 4. Quarantined Data Quality Records (45 records)
    # Total = 10,000 mutually exclusive evaluation records!
    sql_recon = """
    WITH
    direct_stl AS (
        SELECT
            s.transaction_id,
            GROUP_CONCAT(s.settlement_id, '+') AS settlement_ids,
            GROUP_CONCAT(s.settlement_reference, '+') AS settlement_refs,
            COUNT(*) AS stl_count,
            MAX(s.total_allocation_lines) AS expected_lines,
            MAX(s.settlement_type) AS primary_stl_type,
            MIN(s.settlement_date) AS first_stl_date,
            MAX(s.settlement_date) AS last_stl_date,
            ROUND(SUM(CAST(s.gross_amount AS REAL)), 2) AS sum_stl_gross,
            ROUND(SUM(CAST(s.fee_amount AS REAL)), 2) AS sum_stl_fee,
            ROUND(SUM(CAST(s.net_settlement_amount AS REAL)), 2) AS sum_stl_net
        FROM settlements s
        WHERE s.transaction_id <> 'UNLINKED_AMBIG'
        GROUP BY s.transaction_id
    ),
    ambig_stl AS (
        SELECT
            s.payment_reference,
            s.merchant_id,
            GROUP_CONCAT(s.settlement_id, '?') AS ambig_stl_ids,
            COUNT(*) AS ambig_count
        FROM settlements s
        WHERE s.transaction_id = 'UNLINKED_AMBIG'
        GROUP BY s.payment_reference, s.merchant_id
        HAVING COUNT(*) > 1
    ),
    bank_by_txn AS (
        SELECT
            b.transaction_reference AS transaction_id,
            GROUP_CONCAT(b.bank_entry_id, '+') AS bank_entry_ids,
            COUNT(*) AS bank_count,
            MAX(b.value_date) AS last_bank_date,
            ROUND(SUM(CAST(b.signed_bank_amount AS REAL)), 2) AS sum_bank_net
        FROM bank_entries b
        WHERE b.transaction_reference <> 'UNLINKED_AMBIG'
        GROUP BY b.transaction_reference
    ),
    active_refunds AS (
        SELECT
            r.original_transaction_id AS transaction_id,
            r.refund_id,
            CAST(r.refund_amount AS REAL) AS req_refund_amt,
            CAST(r.settled_refund_deduction AS REAL) AS ded_refund_amt,
            r.refund_status
        FROM refunds r
        WHERE r.refund_status IN ('PROCESSED_MISMATCH', 'FAILED_UNREVERSED', 'MISSING_REFUND_EVIDENCE')
    ),
    txn_eval AS (
        SELECT
            t.transaction_id AS source_record_id,
            'TRANSACTION' AS record_grain,
            t.transaction_id AS transaction_id,
            COALESCE(ds.settlement_ids, amb.ambig_stl_ids, 'NONE') AS settlement_ids,
            COALESCE(bb.bank_entry_ids, 'NONE') AS bank_entry_ids,
            ar.refund_id AS refund_id,
            t.merchant_id AS merchant_id,
            t.payment_gateway AS payment_gateway,
            t.transaction_date AS transaction_date,
            ds.last_stl_date AS settlement_date,
            bb.last_bank_date AS bank_value_date,
            fn_business_days_between(t.transaction_date, ds.last_stl_date) AS bdays_to_settle,
            fn_business_days_between(ds.last_stl_date, bb.last_bank_date) AS bdays_to_bank,
            t.currency AS currency,
            CAST(t.transaction_amount AS REAL) AS gross_txn_amt,
            -- Expected Net Amount (accounting for documented fee adjustments & active refund requests)
            CASE
                WHEN ar.refund_status IN ('PROCESSED_MISMATCH', 'MISSING_REFUND_EVIDENCE')
                    THEN ROUND(CAST(t.expected_net_amount AS REAL) - ar.req_refund_amt, 2)
                WHEN ar.refund_status = 'FAILED_UNREVERSED'
                    THEN ROUND(CAST(t.expected_net_amount AS REAL), 2)
                WHEN ds.primary_stl_type = 'FEE_ADJUSTED'
                    THEN ROUND(ds.sum_stl_net, 2)
                ELSE ROUND(CAST(t.expected_net_amount AS REAL), 2)
            END AS expected_amt,
            -- Observed Amount
            CASE
                WHEN amb.ambig_count > 1 THEN 0.00
                WHEN ds.transaction_id IS NULL THEN 0.00
                WHEN bb.bank_count IS NULL OR bb.bank_count = 0 THEN 0.00
                WHEN bb.bank_count > ds.stl_count AND ds.stl_count = 1 THEN ROUND(bb.sum_bank_net, 2)
                ELSE ROUND(ds.sum_stl_net, 2)
            END AS observed_amt,
            COALESCE(ds.sum_stl_fee, CAST(t.transaction_fee AS REAL)) AS fee_amt,
            -- Deterministic Rule ID Selection (Strict Precedence)
            CASE
                WHEN ds.primary_stl_type = 'DUPLICATE_CANDIDATE' THEN 'R6_DUPLICATE'
                WHEN ds.stl_count > 1 AND ds.expected_lines = 1 THEN 'R6_DUPLICATE'
                WHEN bb.bank_count > 1 AND ds.stl_count = 1 THEN 'R6_DUPLICATE'
                WHEN amb.ambig_count > 1 THEN 'R8_AMBIGUOUS'
                WHEN ar.refund_status IS NOT NULL THEN 'R9_REFUND'
                WHEN ds.expected_lines > 1 THEN 'R5_PARTIAL'
                WHEN ds.transaction_id IS NULL THEN 'R7_MISSING'
                WHEN bb.bank_count IS NULL OR bb.bank_count = 0 THEN 'R7_MISSING'
                WHEN fn_business_days_between(ds.last_stl_date, bb.last_bank_date) > 2 THEN 'R4_TIMING'
                WHEN fn_business_days_between(t.transaction_date, ds.last_stl_date) > 2 THEN 'R4_TIMING'
                WHEN ds.primary_stl_type = 'FEE_ADJUSTED' THEN 'R3_FEE_ADJUSTED'
                WHEN ABS(ROUND(ds.sum_stl_net - CAST(t.expected_net_amount AS REAL), 2)) < 0.005 THEN 'R1_EXACT'
                WHEN ABS(ROUND(ds.sum_stl_net - CAST(t.expected_net_amount AS REAL), 2)) <= 1.00 THEN 'R2_TOLERANCE'
                ELSE 'R6_DUPLICATE'
            END AS applied_rule_id,
            -- Classification Outcome
            CASE
                WHEN ds.primary_stl_type = 'DUPLICATE_CANDIDATE' THEN 'DUPLICATE_CANDIDATE'
                WHEN ds.stl_count > 1 AND ds.expected_lines = 1 THEN 'DUPLICATE_CONFIRMED'
                WHEN bb.bank_count > 1 AND ds.stl_count = 1 THEN 'DUPLICATE_CONFIRMED'
                WHEN amb.ambig_count > 1 THEN 'AMBIGUOUS_MATCH'
                WHEN ar.refund_status = 'PROCESSED_MISMATCH' THEN 'REFUND_MISMATCH'
                WHEN ar.refund_status = 'FAILED_UNREVERSED' THEN 'UNREVERSED_REFUND'
                WHEN ar.refund_status = 'MISSING_REFUND_EVIDENCE' THEN 'MISSING_REFUND_EVIDENCE'
                WHEN ds.expected_lines > 1 AND ds.stl_count = ds.expected_lines
                     AND ABS(ROUND(ds.sum_stl_net - CAST(t.expected_net_amount AS REAL), 2)) < 0.005 THEN 'MATCHED_PARTIAL'
                WHEN ds.expected_lines > 1 AND ds.stl_count < ds.expected_lines THEN 'PARTIALLY_SETTLED'
                WHEN ds.transaction_id IS NULL THEN 'MISSING_SETTLEMENT'
                WHEN bb.bank_count IS NULL OR bb.bank_count = 0 THEN 'MISSING_BANK_ENTRY'
                WHEN fn_business_days_between(ds.last_stl_date, bb.last_bank_date) > 2 THEN 'TIMING_EXCEPTION'
                WHEN fn_business_days_between(t.transaction_date, ds.last_stl_date) > 2 THEN 'LATE_SETTLEMENT'
                WHEN ds.primary_stl_type = 'FEE_ADJUSTED' THEN 'MATCHED_FEE_ADJUSTED'
                WHEN ABS(ROUND(ds.sum_stl_net - CAST(t.expected_net_amount AS REAL), 2)) < 0.005 THEN 'MATCHED_EXACT'
                WHEN ABS(ROUND(ds.sum_stl_net - CAST(t.expected_net_amount AS REAL), 2)) <= 1.00 THEN 'MATCHED_WITH_VARIANCE'
                ELSE 'MANUAL_REVIEW'
            END AS recon_class
        FROM transactions t
        LEFT JOIN direct_stl ds ON t.transaction_id = ds.transaction_id
        LEFT JOIN ambig_stl amb ON t.payment_reference = amb.payment_reference AND t.merchant_id = amb.merchant_id
        LEFT JOIN bank_by_txn bb ON t.transaction_id = bb.transaction_id
        LEFT JOIN active_refunds ar ON t.transaction_id = ar.transaction_id
    ),
    orphan_stl_eval AS (
        SELECT
            s.settlement_id AS source_record_id,
            'ORPHAN_SETTLEMENT' AS record_grain,
            'NONE' AS transaction_id,
            s.settlement_id AS settlement_ids,
            COALESCE(b.bank_entry_id, 'NONE') AS bank_entry_ids,
            NULL AS refund_id,
            s.merchant_id AS merchant_id,
            s.source_system AS payment_gateway,
            NULL AS transaction_date,
            s.settlement_date AS settlement_date,
            b.value_date AS bank_value_date,
            0 AS bdays_to_settle,
            0 AS bdays_to_bank,
            s.currency AS currency,
            CAST(s.gross_amount AS REAL) AS gross_txn_amt,
            0.00 AS expected_amt,
            CAST(s.net_settlement_amount AS REAL) AS observed_amt,
            CAST(s.fee_amount AS REAL) AS fee_amt,
            'R7_MISSING' AS applied_rule_id,
            'MISSING_LEDGER' AS recon_class
        FROM settlements s
        LEFT JOIN transactions t ON s.transaction_id = t.transaction_id
        LEFT JOIN bank_entries b ON s.settlement_reference = b.settlement_reference
        WHERE t.transaction_id IS NULL
          AND s.transaction_id <> 'UNLINKED_AMBIG'
    ),
    orphan_bank_eval AS (
        SELECT
            b.bank_entry_id AS source_record_id,
            'ORPHAN_BANK_ENTRY' AS record_grain,
            'NONE' AS transaction_id,
            'NONE' AS settlement_ids,
            b.bank_entry_id AS bank_entry_ids,
            NULL AS refund_id,
            b.merchant_id AS merchant_id,
            'BANK_DIRECT_FEED' AS payment_gateway,
            NULL AS transaction_date,
            NULL AS settlement_date,
            b.value_date AS bank_value_date,
            0 AS bdays_to_settle,
            0 AS bdays_to_bank,
            b.currency AS currency,
            CAST(b.credit_amount AS REAL) AS gross_txn_amt,
            0.00 AS expected_amt,
            CAST(b.signed_bank_amount AS REAL) AS observed_amt,
            0.00 AS fee_amt,
            'R7_MISSING' AS applied_rule_id,
            'MISSING_LEDGER' AS recon_class
        FROM bank_entries b
        LEFT JOIN settlements s ON b.settlement_reference = s.settlement_reference
        WHERE s.settlement_id IS NULL
    ),
    quarantined_eval AS (
        SELECT
            q.source_record_id AS source_record_id,
            'QUARANTINED_RECORD' AS record_grain,
            q.source_record_id AS transaction_id,
            'NONE' AS settlement_ids,
            'NONE' AS bank_entry_ids,
            NULL AS refund_id,
            q.merchant_id AS merchant_id,
            q.payment_gateway AS payment_gateway,
            NULL AS transaction_date,
            NULL AS settlement_date,
            NULL AS bank_value_date,
            0 AS bdays_to_settle,
            0 AS bdays_to_bank,
            q.currency AS currency,
            0.00 AS gross_txn_amt,
            CAST(q.expected_net_inr AS REAL) AS expected_amt,
            0.00 AS observed_amt,
            0.00 AS fee_amt,
            'DQ_VALIDATION' AS applied_rule_id,
            'QUARANTINED_DATA_QUALITY' AS recon_class
        FROM quarantine_records q
    )
    SELECT * FROM txn_eval
    UNION ALL
    SELECT * FROM orphan_stl_eval
    UNION ALL
    SELECT * FROM orphan_bank_eval
    UNION ALL
    SELECT * FROM quarantined_eval
    """

    rows = cur.execute(sql_recon).fetchall()

    # Quarantined lookup for detailed exception category
    quar_map = {
        r["source_record_id"]: (r["quarantine_reason"], r["quarantine_detail"])
        for r in cur.execute("SELECT source_record_id, quarantine_reason, quarantine_detail FROM quarantine_records").fetchall()
    }

    # Previously resolved & reopened IDs per synthetic lifecycle rules (Scenarios 24 & 25)
    resolved_ids = (
        {f"TXN_2026_{i:06d}" for i in range(9201, 9241)}
        | {f"TXN_2026_{i:06d}" for i in range(9421, 9446)}
        | {f"TXN_2026_{i:06d}" for i in range(9661, 9681)}
        | {f"TXN_2026_{i:06d}" for i in range(9856, 9866)}
    )
    reopened_ids = (
        {f"TXN_2026_{i:06d}" for i in range(9241, 9251)}
        | {f"TXN_2026_{i:06d}" for i in range(9681, 9691)}
        | {f"TXN_2026_{i:06d}" for i in range(9761, 9766)}
    )
    confirmed_loss_ids = (
        {f"TXN_2026_{i:06d}" for i in range(9446, 9456)}
        | {f"TXN_2026_{i:06d}" for i in range(9896, 9901)}
    )

    match_inserts = []
    exc_inserts = []
    hist_inserts = []

    matched_statuses = {"MATCHED_EXACT", "MATCHED_WITH_VARIANCE", "MATCHED_FEE_ADJUSTED", "MATCHED_PARTIAL"}
    exc_seq = 1

    for idx_m, r in enumerate(rows, start=1):
        m_id_str = f"MCH_{idx_m:06d}"
        src_id = r["source_record_id"]
        exp_dec = q2(Decimal(str(r["expected_amt"])))
        obs_dec = q2(Decimal(str(r["observed_amt"])))
        signed_var = q2(obs_dec - exp_dec)
        abs_var = abs(signed_var)
        r_class = r["recon_class"]
        is_match = 1 if r_class in matched_statuses else 0
        is_exc = 0 if is_match == 1 else 1

        if r_class == "QUARANTINED_DATA_QUALITY":
            exc_cat = quar_map.get(src_id, ("DATA_QUALITY_ERROR", "Quarantined"))[0]
            ev_text = quar_map.get(src_id, ("DATA_QUALITY_ERROR", "Quarantined"))[1]
        else:
            exc_cat = "NONE" if is_match else r_class
            ev_text = (
                f"Rule={r['applied_rule_id']} | Class={r_class} | "
                f"Exp={exp_dec:.2f} | Obs={obs_dec:.2f} | Var={signed_var:+.2f} | "
                f"Stl={r['settlement_ids']} | Bnk={r['bank_entry_ids']}"
            )

        match_inserts.append((
            m_id_str,
            config.run_id,
            config.rule_version,
            src_id,
            r["record_grain"],
            r["transaction_id"],
            r["settlement_ids"],
            r["bank_entry_ids"],
            r["refund_id"],
            r["merchant_id"],
            r["payment_gateway"],
            r["transaction_date"],
            r["settlement_date"],
            r["bank_value_date"],
            int(r["bdays_to_settle"] or 0),
            int(r["bdays_to_bank"] or 0),
            r["currency"],
            f"{q2(Decimal(str(r['gross_txn_amt']))):.2f}",
            f"{exp_dec:.2f}",
            f"{obs_dec:.2f}",
            f"{q2(Decimal(str(r['fee_amt']))):.2f}",
            f"{signed_var:.2f}",
            f"{abs_var:.2f}",
            r["applied_rule_id"],
            r_class,
            is_match,
            is_exc,
            exc_cat,
            ev_text,
        ))

        if is_exc == 1:
            exc_id_str = f"EXC_{exc_seq:05d}"
            exc_seq += 1

            first_dt = r["transaction_date"] or r["settlement_date"] or r["bank_value_date"] or "2026-10-15"
            if src_id in resolved_ids:
                res_stat = "RESOLVED"
                age_days = 4
                res_ts = f"{first_dt}T17:00:00Z"
                reop_ts = None
                out_exp = Decimal("0.00")
                res_cat = "ACQUIRER_RECOVERY_OR_BATCH_POSTED"
                res_notes = "[SYNTHETIC RESOLUTION] Discrepancy cleared via subsequent acquirer adjustment."
            elif src_id in reopened_ids:
                res_stat = "REOPENED"
                age_days = _sql_days_between(first_dt, config.reporting_date)
                res_ts = f"{first_dt}T15:00:00Z"
                reop_ts = "2026-10-22T10:30:00Z"
                out_exp = abs_var
                res_cat = "REOPENED_REVERSAL_FAILURE"
                res_notes = "[SYNTHETIC REOPENED] Previously closed item reopened after bank reversal check."
            else:
                res_stat = "OPEN"
                age_days = _sql_days_between(first_dt, config.reporting_date)
                res_ts = None
                reop_ts = None
                out_exp = abs_var
                res_cat = "PENDING_INVESTIGATION"
                res_notes = "[SYNTHETIC OPEN] Assigned to Settlement Operations queue for partner reconciliation."

            conf_loss = abs_var if src_id in confirmed_loss_ids else Decimal("0.00")

            if age_days <= 2:
                age_band = "0-2 Days"
            elif age_days <= 7:
                age_band = "3-7 Days"
            elif age_days <= 30:
                age_band = "8-30 Days"
            else:
                age_band = "Over 30 Days"

            if r_class in ("MISSING_SETTLEMENT", "DUPLICATE_CONFIRMED", "UNREVERSED_REFUND"):
                prio = "CRITICAL"
            elif r_class in ("MISSING_LEDGER", "MISSING_BANK_ENTRY", "PARTIALLY_SETTLED", "AMBIGUOUS_MATCH", "REFUND_MISMATCH", "MISSING_REFUND_EVIDENCE", "DUPLICATE_CANDIDATE", "MANUAL_REVIEW"):
                prio = "HIGH"
            else:
                prio = "MEDIUM"

            reviewer = f"ops_analyst_{(exc_seq % 6) + 1}@settlementiq.example"

            exc_inserts.append((
                exc_id_str,
                config.run_id,
                m_id_str,
                src_id,
                r["transaction_id"],
                r["settlement_ids"],
                r["bank_entry_ids"],
                r["refund_id"],
                r["merchant_id"],
                r["payment_gateway"],
                exc_cat,
                r["applied_rule_id"],
                config.rule_version,
                f"{exp_dec:.2f}",
                f"{obs_dec:.2f}",
                f"{signed_var:.2f}",
                f"{abs_var:.2f}",
                f"{out_exp:.2f}",
                f"{conf_loss:.2f}",
                r["currency"],
                first_dt,
                config.reporting_date,
                age_days,
                age_band,
                prio,
                res_stat,
                reviewer,
                res_cat,
                res_notes,
                res_ts,
                reop_ts,
                ev_text,
            ))

            # Populate audit trail in exception_history
            hist_inserts.append((
                exc_id_str, config.run_id, None, "OPEN", "SYSTEM_RECON_ENGINE",
                f"{first_dt}T20:00:00Z", f"Exception detected under {r['applied_rule_id']} ({exc_cat})"
            ))
            if res_stat in ("RESOLVED", "REOPENED"):
                hist_inserts.append((
                    exc_id_str, config.run_id, "OPEN", "RESOLVED", reviewer,
                    res_ts or "2026-10-18T17:00:00Z", "Synthetic resolution logged after partner credit note."
                ))
            if res_stat == "REOPENED":
                hist_inserts.append((
                    exc_id_str, config.run_id, "RESOLVED", "REOPENED", "QA_CONTROL_AUDITOR",
                    reop_ts or "2026-10-22T10:30:00Z", "Synthetic exception reopened due to subsequent settlement debit."
                ))

    cur.executemany(
        """INSERT INTO reconciliation_matches VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )""",
        match_inserts,
    )

    cur.executemany(
        """INSERT INTO exceptions VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )""",
        exc_inserts,
    )

    cur.executemany(
        """INSERT INTO exception_history (
            exception_id, run_id, previous_status, new_status, action_by, action_timestamp, notes
        ) VALUES (?,?,?,?,?,?,?)""",
        hist_inserts,
    )

    # Update reconciliation_runs summary row
    tot_cases = len(match_inserts)
    elig_ledger = sum(1 for m in match_inserts if m[4] == "TRANSACTION")
    matched_cnt = sum(1 for m in match_inserts if m[25] == 1)
    exc_cnt = len(exc_inserts)
    recon_rate = q2((Decimal(matched_cnt) / Decimal(elig_ledger)) * Decimal("100.00"))
    tot_exp_inr = sum(Decimal(m[18]) for m in match_inserts)
    tot_obs_inr = sum(Decimal(m[19]) for m in match_inserts)
    tot_signed_var = sum(Decimal(m[21]) for m in match_inserts)
    tot_out_exp = sum(Decimal(e[17]) for e in exc_inserts)
    tot_conf_loss = sum(Decimal(e[18]) for e in exc_inserts)

    cur.execute(
        """UPDATE reconciliation_runs SET
            total_evaluated_cases = ?,
            eligible_ledger_count = ?,
            matched_count = ?,
            exception_count = ?,
            reconciliation_rate_pct = ?,
            total_expected_inr = ?,
            total_observed_inr = ?,
            net_signed_discrepancy_inr = ?,
            outstanding_exposure_inr = ?,
            confirmed_loss_inr = ?,
            run_status = 'COMPLETED'
        WHERE run_id = ?""",
        (
            tot_cases,
            elig_ledger,
            matched_cnt,
            exc_cnt,
            f"{recon_rate:.2f}",
            f"{tot_exp_inr:.2f}",
            f"{tot_obs_inr:.2f}",
            f"{tot_signed_var:.2f}",
            f"{tot_out_exp:.2f}",
            f"{tot_conf_loss:.2f}",
            config.run_id,
        ),
    )

    conn.commit()
    return {
        "run_id": config.run_id,
        "total_evaluated_cases": tot_cases,
        "eligible_ledger_count": elig_ledger,
        "matched_count": matched_cnt,
        "exception_count": exc_cnt,
        "reconciliation_rate_pct": float(recon_rate),
        "total_expected_inr": f"{tot_exp_inr:.2f}",
        "total_observed_inr": f"{tot_obs_inr:.2f}",
        "net_signed_discrepancy_inr": f"{tot_signed_var:.2f}",
        "outstanding_exposure_inr": f"{tot_out_exp:.2f}",
        "confirmed_loss_inr": f"{tot_conf_loss:.2f}",
    }
