"""Complete KPI Calculation & Ground-Truth Evaluation Engine for SettlementIQ.

Computes all 6 KPI families from the authoritative database tables and evaluates
reconciliation classifications against the isolated `ground_truth.csv` dataset.
"""
from decimal import Decimal
import sqlite3
from typing import Any, Dict, List

from .config import DEFAULT_CONFIG, SettlementIQConfig
from .synthetic_data import q2


def calculate_all_kpis_and_evaluation(
    conn: sqlite3.Connection,
    raw_data: Dict[str, List[Dict[str, Any]]],
    dq_report: Dict[str, Any],
    config: SettlementIQConfig = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Compute all volume, financial, reconciliation, exception, DQ, and ground-truth KPIs."""
    cur = conn.cursor()

    # 1. Volume KPIs
    raw_txn_count = len(raw_data["transactions"])
    valid_txn_count = cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    distinct_cust_count = cur.execute("SELECT COUNT(DISTINCT customer_id) FROM transactions").fetchone()[0]
    distinct_merch_count = cur.execute("SELECT COUNT(DISTINCT merchant_id) FROM merchants").fetchone()[0]
    stl_record_count = cur.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
    bnk_record_count = cur.execute("SELECT COUNT(*) FROM bank_entries").fetchone()[0]
    ref_record_count = cur.execute("SELECT COUNT(*) FROM refunds").fetchone()[0]
    recon_record_count = cur.execute("SELECT COUNT(*) FROM reconciliation_matches").fetchone()[0]
    exc_record_count = cur.execute("SELECT COUNT(*) FROM exceptions").fetchone()[0]
    quar_record_count = cur.execute("SELECT COUNT(*) FROM quarantine_records").fetchone()[0]
    suppressed_dup_count = (
        dq_report["summary_metrics"]["suppressed_duplicate_txn_rows"]
        + dq_report["summary_metrics"]["suppressed_duplicate_stl_rows"]
    )

    # 2. Financial KPIs (exact Decimal summation from database rows)
    matches = cur.execute("SELECT * FROM reconciliation_matches").fetchall()
    excs = cur.execute("SELECT * FROM exceptions").fetchall()
    stls = cur.execute("SELECT * FROM settlements").fetchall()
    bnks = cur.execute("SELECT * FROM bank_entries").fetchall()
    refs = cur.execute("SELECT * FROM refunds").fetchall()
    txns = cur.execute("SELECT * FROM transactions").fetchall()

    gross_txn_val = sum(Decimal(str(r["transaction_amount"])) for r in txns)
    gross_stl_val = sum(Decimal(str(r["gross_amount"])) for r in stls)
    total_fee_val = sum(Decimal(str(r["fee_amount"])) for r in stls)
    net_stl_val = sum(Decimal(str(r["net_settlement_amount"])) for r in stls)
    bank_credit_val = sum(Decimal(str(r["credit_amount"])) for r in bnks)
    bank_debit_val = sum(Decimal(str(r["debit_amount"])) for r in bnks)
    refund_val = sum(Decimal(str(r["refund_amount"])) for r in refs)

    expected_fin_val = sum(Decimal(str(m["expected_amount"])) for m in matches)
    observed_fin_val = sum(Decimal(str(m["observed_amount"])) for m in matches)
    net_signed_discrepancy = sum(Decimal(str(m["signed_variance"])) for m in matches)
    total_abs_discrepancy = sum(Decimal(str(m["absolute_variance"])) for m in matches)
    outstanding_exposure = sum(Decimal(str(e["outstanding_exposure"])) for e in excs)
    confirmed_loss = sum(Decimal(str(e["confirmed_loss"])) for e in excs)

    # 3. Reconciliation Outcome Counts & Rates
    class_counts: Dict[str, int] = {}
    for m in matches:
        c = m["reconciliation_classification"]
        class_counts[c] = class_counts.get(c, 0) + 1

    matched_total = sum(1 for m in matches if m["is_matched"] == 1)
    eligible_ledger = valid_txn_count  # 9,885 validated ledger transactions
    total_eval_pop = len(matches)      # 10,000 total evaluated cases

    def pct(n: int, d: int) -> float:
        return float(q2((Decimal(n) / Decimal(d)) * Decimal("100.00"))) if d else 0.0

    recon_rate_ledger = pct(matched_total, eligible_ledger)
    recon_rate_all = pct(matched_total, total_eval_pop)
    exact_match_rate = pct(class_counts.get("MATCHED_EXACT", 0), eligible_ledger)
    tolerance_match_rate = pct(class_counts.get("MATCHED_WITH_VARIANCE", 0), eligible_ledger)
    fee_adj_match_rate = pct(class_counts.get("MATCHED_FEE_ADJUSTED", 0), eligible_ledger)
    partial_match_rate = pct(class_counts.get("MATCHED_PARTIAL", 0), eligible_ledger)
    partial_shortfall_rate = pct(class_counts.get("PARTIALLY_SETTLED", 0), eligible_ledger)
    late_stl_rate = pct(class_counts.get("LATE_SETTLEMENT", 0), eligible_ledger)
    timing_exc_rate = pct(class_counts.get("TIMING_EXCEPTION", 0), eligible_ledger)
    missing_stl_rate = pct(class_counts.get("MISSING_SETTLEMENT", 0), eligible_ledger)
    missing_ledger_rate = pct(class_counts.get("MISSING_LEDGER", 0), total_eval_pop)
    missing_bank_rate = pct(class_counts.get("MISSING_BANK_ENTRY", 0), eligible_ledger)
    ambig_match_rate = pct(class_counts.get("AMBIGUOUS_MATCH", 0), eligible_ledger)
    dup_cand_rate = pct(class_counts.get("DUPLICATE_CANDIDATE", 0), stl_record_count)
    dup_conf_rate = pct(class_counts.get("DUPLICATE_CONFIRMED", 0), stl_record_count)
    refund_mismatch_rate = pct(
        class_counts.get("REFUND_MISMATCH", 0)
        + class_counts.get("UNREVERSED_REFUND", 0)
        + class_counts.get("MISSING_REFUND_EVIDENCE", 0),
        ref_record_count,
    )
    manual_review_rate = pct(class_counts.get("MANUAL_REVIEW", 0), eligible_ledger)

    # 4. Exception Management KPIs
    open_exc_count = sum(1 for e in excs if e["resolution_status"] == "OPEN")
    reopened_exc_count = sum(1 for e in excs if e["resolution_status"] == "REOPENED")
    unresolved_exc_count = open_exc_count + reopened_exc_count
    resolved_exc_count = sum(1 for e in excs if e["resolution_status"] == "RESOLVED")
    exc_resolution_rate = pct(resolved_exc_count, exc_record_count)

    resolved_ages = [int(e["exception_age_days"]) for e in excs if e["resolution_status"] == "RESOLVED"]
    avg_res_days = round(sum(resolved_ages) / len(resolved_ages), 2) if resolved_ages else 0.0
    sorted_ages = sorted(resolved_ages)
    median_res_days = float(sorted_ages[len(sorted_ages) // 2]) if sorted_ages else 0.0

    # Aging distribution & exposure by aging band
    aging_summary: Dict[str, Dict[str, Any]] = {}
    for band in ["0-2 Days", "3-7 Days", "8-30 Days", "Over 30 Days"]:
        band_rows = [e for e in excs if e["aging_band"] == band]
        aging_summary[band] = {
            "total_count": len(band_rows),
            "unresolved_count": sum(1 for e in band_rows if e["resolution_status"] in ("OPEN", "REOPENED")),
            "resolved_count": sum(1 for e in band_rows if e["resolution_status"] == "RESOLVED"),
            "outstanding_exposure_inr": f"{sum(Decimal(str(e['outstanding_exposure'])) for e in band_rows):.2f}",
        }

    # Exposure by exception category
    cat_summary: Dict[str, Dict[str, Any]] = {}
    for e in excs:
        cat = e["exception_category"]
        if cat not in cat_summary:
            cat_summary[cat] = {
                "exception_category": cat,
                "applied_rule_id": e["applied_rule_id"],
                "total_count": 0,
                "unresolved_count": 0,
                "resolved_count": 0,
                "reopened_count": 0,
                "expected_amount_inr": Decimal("0.00"),
                "observed_amount_inr": Decimal("0.00"),
                "signed_variance_inr": Decimal("0.00"),
                "outstanding_exposure_inr": Decimal("0.00"),
                "confirmed_loss_inr": Decimal("0.00"),
            }
        cs = cat_summary[cat]
        cs["total_count"] += 1
        if e["resolution_status"] in ("OPEN", "REOPENED"):
            cs["unresolved_count"] += 1
        if e["resolution_status"] == "RESOLVED":
            cs["resolved_count"] += 1
        if e["resolution_status"] == "REOPENED":
            cs["reopened_count"] += 1
        cs["expected_amount_inr"] += Decimal(str(e["expected_amount"]))
        cs["observed_amount_inr"] += Decimal(str(e["observed_amount"]))
        cs["signed_variance_inr"] += Decimal(str(e["signed_variance"]))
        cs["outstanding_exposure_inr"] += Decimal(str(e["outstanding_exposure"]))
        cs["confirmed_loss_inr"] += Decimal(str(e["confirmed_loss"]))

    # Exposure by merchant
    merch_names = {m["merchant_id"]: m["merchant_name"] for m in raw_data["merchants"]}
    merch_exposure: Dict[str, Dict[str, Any]] = {}
    for m in matches:
        mid = m["merchant_id"]
        if mid not in merch_exposure:
            merch_exposure[mid] = {
                "merchant_id": mid,
                "merchant_name": merch_names.get(mid, "Quarantined / Missing Merchant"),
                "payment_gateway": m["payment_gateway"],
                "total_records": 0,
                "matched_count": 0,
                "exception_count": 0,
                "gross_txn_inr": Decimal("0.00"),
                "expected_net_inr": Decimal("0.00"),
                "observed_net_inr": Decimal("0.00"),
                "outstanding_exposure_inr": Decimal("0.00"),
            }
        me = merch_exposure[mid]
        me["total_records"] += 1
        me["matched_count"] += int(m["is_matched"])
        me["exception_count"] += int(m["is_exception"])
        me["gross_txn_inr"] += Decimal(str(m["gross_transaction_amount"]))
        me["expected_net_inr"] += Decimal(str(m["expected_amount"]))
        me["observed_net_inr"] += Decimal(str(m["observed_amount"]))

    for e in excs:
        mid = e["merchant_id"]
        if mid in merch_exposure:
            merch_exposure[mid]["outstanding_exposure_inr"] += Decimal(str(e["outstanding_exposure"]))

    # 5. Independent Ground-Truth Evaluation (10,000 Cases)
    gt_rows = raw_data["ground_truth"]
    match_by_src = {m["source_record_id"]: m for m in matches}
    exc_by_src = {e["source_record_id"]: e for e in excs}

    gt_eval_rows: List[Dict[str, Any]] = []
    scen_eval: Dict[str, Dict[str, Any]] = {}

    correct_class_count = 0
    planted_exc_total = 0
    planted_exc_detected = 0
    clean_total = 0
    clean_false_positives = 0
    false_negatives = 0
    variance_errors = 0

    for g in gt_rows:
        src_id = g["source_record_id"]
        scen = g["planted_scenario"]
        exp_cls = g["expected_classification"]
        is_planted_exc = g["is_planted_exception"] == "TRUE"
        exp_var = Decimal(g["expected_variance"])

        obs_m = match_by_src.get(src_id)
        obs_e = exc_by_src.get(src_id)

        act_cls = obs_m["reconciliation_classification"] if obs_m else "UNCLASSIFIED"
        act_is_exc = (obs_m["is_exception"] == 1) if obs_m else False
        act_var = Decimal(str(obs_m["signed_variance"])) if obs_m else Decimal("0.00")
        act_exc_type = obs_e["exception_category"] if obs_e else "NONE"

        cls_ok = act_cls == exp_cls
        var_ok = act_var == exp_var
        if cls_ok:
            correct_class_count += 1
        if not var_ok:
            variance_errors += 1

        if is_planted_exc:
            planted_exc_total += 1
            if act_is_exc and cls_ok:
                planted_exc_detected += 1
            elif not act_is_exc:
                false_negatives += 1
        else:
            clean_total += 1
            if act_is_exc:
                clean_false_positives += 1

        if scen not in scen_eval:
            scen_eval[scen] = {
                "planted_scenario": scen,
                "expected_classification": exp_cls,
                "is_planted_exception": "TRUE" if is_planted_exc else "FALSE",
                "expected_count": 0,
                "detected_correct_count": 0,
                "incorrect_count": 0,
                "false_positive_count": 0,
                "false_negative_count": 0,
                "variance_error_count": 0,
            }
        se = scen_eval[scen]
        se["expected_count"] += 1
        if cls_ok:
            se["detected_correct_count"] += 1
        else:
            se["incorrect_count"] += 1
        if not is_planted_exc and act_is_exc:
            se["false_positive_count"] += 1
        if is_planted_exc and not act_is_exc:
            se["false_negative_count"] += 1
        if not var_ok:
            se["variance_error_count"] += 1

        gt_eval_rows.append({
            "synthetic_case_id": g["synthetic_case_id"],
            "source_record_id": src_id,
            "planted_scenario": scen,
            "expected_classification": exp_cls,
            "actual_classification": act_cls,
            "classification_match": "PASS" if cls_ok else "FAIL",
            "expected_exception_type": g["expected_exception_type"],
            "actual_exception_type": act_exc_type,
            "expected_variance": f"{exp_var:.2f}",
            "actual_variance": f"{act_var:.2f}",
            "variance_match": "PASS" if var_ok else "FAIL",
        })

    for se in scen_eval.values():
        se["detection_accuracy_pct"] = f"{pct(se['detected_correct_count'], se['expected_count']):.2f}"

    overall_accuracy_pct = pct(correct_class_count, len(gt_rows))
    planted_exc_recall_pct = pct(planted_exc_detected, planted_exc_total)
    planted_exc_precision_pct = pct(planted_exc_detected, planted_exc_detected + clean_false_positives)
    clean_fp_rate_pct = pct(clean_false_positives, clean_total)

    # Assemble Master KPI List (All 6 KPI categories with full metadata)
    kpi_catalog = [
        # 11.1 Volume KPIs
        {"kpi_id": "KPI_VOL_01", "category": "Volume", "kpi_name": "Total Raw Transaction Count", "actual_value": str(raw_txn_count), "unit": "Records", "formula": "COUNT(*) FROM raw_staging.stg_transactions", "numerator": str(raw_txn_count), "denominator": "N/A", "population": "All raw ingested transaction rows", "source": "stg_transactions", "currency": "ALL"},
        {"kpi_id": "KPI_VOL_02", "category": "Volume", "kpi_name": "Validated Distinct Transaction Count", "actual_value": str(valid_txn_count), "unit": "Transactions", "formula": "COUNT(DISTINCT transaction_id) FROM validated.transactions", "numerator": str(valid_txn_count), "denominator": "N/A", "population": "Validated INR ledger transactions", "source": "validated.transactions", "currency": "INR"},
        {"kpi_id": "KPI_VOL_03", "category": "Volume", "kpi_name": "Distinct Customer Count", "actual_value": str(distinct_cust_count), "unit": "Customers", "formula": "COUNT(DISTINCT customer_id) FROM validated.transactions", "numerator": str(distinct_cust_count), "denominator": "N/A", "population": "Validated ledger transactions", "source": "validated.transactions", "currency": "INR"},
        {"kpi_id": "KPI_VOL_04", "category": "Volume", "kpi_name": "Distinct Merchant Count", "actual_value": str(distinct_merch_count), "unit": "Merchants", "formula": "COUNT(DISTINCT merchant_id) FROM validated.merchants", "numerator": str(distinct_merch_count), "denominator": "N/A", "population": "Active onboarded merchants", "source": "validated.merchants", "currency": "INR"},
        {"kpi_id": "KPI_VOL_05", "category": "Volume", "kpi_name": "Validated Settlement Record Count", "actual_value": str(stl_record_count), "unit": "Records", "formula": "COUNT(*) FROM validated.settlements", "numerator": str(stl_record_count), "denominator": "N/A", "population": "Deduplicated settlement lines", "source": "validated.settlements", "currency": "INR"},
        {"kpi_id": "KPI_VOL_06", "category": "Volume", "kpi_name": "Validated Bank-Entry Count", "actual_value": str(bnk_record_count), "unit": "Records", "formula": "COUNT(*) FROM validated.bank_entries", "numerator": str(bnk_record_count), "denominator": "N/A", "population": "Validated bank statement rows", "source": "validated.bank_entries", "currency": "INR"},
        {"kpi_id": "KPI_VOL_07", "category": "Volume", "kpi_name": "Validated Refund Count", "actual_value": str(ref_record_count), "unit": "Records", "formula": "COUNT(*) FROM validated.refunds", "numerator": str(ref_record_count), "denominator": "N/A", "population": "Validated refund records", "source": "validated.refunds", "currency": "INR"},
        {"kpi_id": "KPI_VOL_08", "category": "Volume", "kpi_name": "Reconciliation Evaluated Record Count", "actual_value": str(recon_record_count), "unit": "Cases", "formula": "COUNT(*) FROM reconciliation.reconciliation_matches", "numerator": str(recon_record_count), "denominator": "N/A", "population": "All 10,000 evaluated cases (txns + orphans + quarantined)", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_VOL_09", "category": "Volume", "kpi_name": "Total Distinct Exception Count", "actual_value": str(exc_record_count), "unit": "Exceptions", "formula": "COUNT(DISTINCT exception_id) FROM reconciliation.exceptions", "numerator": str(exc_record_count), "denominator": "N/A", "population": "All detected reconciliation & DQ exceptions", "source": "reconciliation.exceptions", "currency": "INR"},
        {"kpi_id": "KPI_VOL_10", "category": "Volume", "kpi_name": "Quarantined Source Record Count", "actual_value": str(quar_record_count), "unit": "Records", "formula": "COUNT(*) FROM raw_staging.quarantine_records", "numerator": str(quar_record_count), "denominator": "N/A", "population": "Records failing schema/currency/amount validation", "source": "quarantine_records", "currency": "ALL"},
        {"kpi_id": "KPI_VOL_11", "category": "Volume", "kpi_name": "Suppressed Duplicate Ingestion Count", "actual_value": str(suppressed_dup_count), "unit": "Records", "formula": "Raw rows minus deduplicated staging rows", "numerator": str(suppressed_dup_count), "denominator": "N/A", "population": "Replay rows suppressed at ingestion (25 txn + 25 stl)", "source": "staging_dedup", "currency": "INR"},

        # 11.2 Financial KPIs
        {"kpi_id": "KPI_FIN_01", "category": "Financial", "kpi_name": "Total Validated Gross Transaction Value", "actual_value": f"{gross_txn_val:.2f}", "unit": "INR", "formula": "SUM(transaction_amount) FROM validated.transactions", "numerator": f"{gross_txn_val:.2f}", "denominator": "N/A", "population": "9,885 validated INR ledger transactions", "source": "validated.transactions", "currency": "INR"},
        {"kpi_id": "KPI_FIN_02", "category": "Financial", "kpi_name": "Total Validated Gross Settlement Value", "actual_value": f"{gross_stl_val:.2f}", "unit": "INR", "formula": "SUM(gross_amount) FROM validated.settlements", "numerator": f"{gross_stl_val:.2f}", "denominator": "N/A", "population": "10,065 validated settlement lines", "source": "validated.settlements", "currency": "INR"},
        {"kpi_id": "KPI_FIN_03", "category": "Financial", "kpi_name": "Total Settlement Fee & Adjustment Value", "actual_value": f"{total_fee_val:.2f}", "unit": "INR", "formula": "SUM(fee_amount) FROM validated.settlements", "numerator": f"{total_fee_val:.2f}", "denominator": "N/A", "population": "10,065 validated settlement lines", "source": "validated.settlements", "currency": "INR"},
        {"kpi_id": "KPI_FIN_04", "category": "Financial", "kpi_name": "Total Validated Net Settlement Value", "actual_value": f"{net_stl_val:.2f}", "unit": "INR", "formula": "SUM(net_settlement_amount) FROM validated.settlements", "numerator": f"{net_stl_val:.2f}", "denominator": "N/A", "population": "10,065 validated settlement lines", "source": "validated.settlements", "currency": "INR"},
        {"kpi_id": "KPI_FIN_05", "category": "Financial", "kpi_name": "Total Bank Credit Value", "actual_value": f"{bank_credit_val:.2f}", "unit": "INR", "formula": "SUM(credit_amount) FROM validated.bank_entries", "numerator": f"{bank_credit_val:.2f}", "denominator": "N/A", "population": "10,070 validated bank entries", "source": "validated.bank_entries", "currency": "INR"},
        {"kpi_id": "KPI_FIN_06", "category": "Financial", "kpi_name": "Total Bank Debit Value", "actual_value": f"{bank_debit_val:.2f}", "unit": "INR", "formula": "SUM(debit_amount) FROM validated.bank_entries", "numerator": f"{bank_debit_val:.2f}", "denominator": "N/A", "population": "10,070 validated bank entries", "source": "validated.bank_entries", "currency": "INR"},
        {"kpi_id": "KPI_FIN_07", "category": "Financial", "kpi_name": "Total Requested Refund Value", "actual_value": f"{refund_val:.2f}", "unit": "INR", "formula": "SUM(refund_amount) FROM validated.refunds", "numerator": f"{refund_val:.2f}", "denominator": "N/A", "population": "250 validated refund records", "source": "validated.refunds", "currency": "INR"},
        {"kpi_id": "KPI_FIN_08", "category": "Financial", "kpi_name": "Total Expected Net Financial Value", "actual_value": f"{expected_fin_val:.2f}", "unit": "INR", "formula": "SUM(expected_amount) FROM reconciliation_matches", "numerator": f"{expected_fin_val:.2f}", "denominator": "N/A", "population": "All 10,000 reconciliation cases", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_FIN_09", "category": "Financial", "kpi_name": "Total Observed Net Financial Value", "actual_value": f"{observed_fin_val:.2f}", "unit": "INR", "formula": "SUM(observed_amount) FROM reconciliation_matches", "numerator": f"{observed_fin_val:.2f}", "denominator": "N/A", "population": "All 10,000 reconciliation cases", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_FIN_10", "category": "Financial", "kpi_name": "Net Signed Discrepancy", "actual_value": f"{net_signed_discrepancy:.2f}", "unit": "INR", "formula": "SUM(observed_amount - expected_amount)", "numerator": f"{net_signed_discrepancy:.2f}", "denominator": "N/A", "population": "All 10,000 reconciliation cases", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_FIN_11", "category": "Financial", "kpi_name": "Total Absolute Discrepancy (All Cases)", "actual_value": f"{total_abs_discrepancy:.2f}", "unit": "INR", "formula": "SUM(ABS(observed_amount - expected_amount))", "numerator": f"{total_abs_discrepancy:.2f}", "denominator": "N/A", "population": "All 10,000 reconciliation cases", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_FIN_12", "category": "Financial", "kpi_name": "Outstanding Discrepancy Exposure", "actual_value": f"{outstanding_exposure:.2f}", "unit": "INR", "formula": "SUM(ABS(signed_variance)) WHERE resolution_status IN ('OPEN', 'REOPENED')", "numerator": f"{outstanding_exposure:.2f}", "denominator": "N/A", "population": "Unresolved (OPEN + REOPENED) exceptions only", "source": "reconciliation.exceptions", "currency": "INR"},
        {"kpi_id": "KPI_FIN_13", "category": "Financial", "kpi_name": "Confirmed Financial Loss", "actual_value": f"{confirmed_loss:.2f}", "unit": "INR", "formula": "SUM(confirmed_loss) FROM reconciliation.exceptions", "numerator": f"{confirmed_loss:.2f}", "denominator": "N/A", "population": "Independently evidenced write-off cases (15 cases)", "source": "reconciliation.exceptions", "currency": "INR"},

        # 11.3 Reconciliation KPIs
        {"kpi_id": "KPI_REC_01", "category": "Reconciliation", "kpi_name": "Overall Ledger Reconciliation Rate", "actual_value": f"{recon_rate_ledger:.2f}", "unit": "%", "formula": "(Matched Validated Ledger Txns / Total Validated Ledger Txns) * 100", "numerator": str(matched_total), "denominator": str(eligible_ledger), "population": "9,885 validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_02", "category": "Reconciliation", "kpi_name": "Total Ecosystem Match Rate (10K Cases)", "actual_value": f"{recon_rate_all:.2f}", "unit": "%", "formula": "(Matched Cases / All 10,000 Evaluated Cases) * 100", "numerator": str(matched_total), "denominator": str(total_eval_pop), "population": "All 10,000 evaluated ecosystem cases", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_03", "category": "Reconciliation", "kpi_name": "Exact Match Rate (R1)", "actual_value": f"{exact_match_rate:.2f}", "unit": "%", "formula": "(MATCHED_EXACT Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MATCHED_EXACT", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_04", "category": "Reconciliation", "kpi_name": "Tolerance Match Rate (R2)", "actual_value": f"{tolerance_match_rate:.2f}", "unit": "%", "formula": "(MATCHED_WITH_VARIANCE Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MATCHED_WITH_VARIANCE", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_05", "category": "Reconciliation", "kpi_name": "Fee-Adjusted Match Rate (R3)", "actual_value": f"{fee_adj_match_rate:.2f}", "unit": "%", "formula": "(MATCHED_FEE_ADJUSTED Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MATCHED_FEE_ADJUSTED", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_06", "category": "Reconciliation", "kpi_name": "Multi-Part Complete Settlement Rate (R5)", "actual_value": f"{partial_match_rate:.2f}", "unit": "%", "formula": "(MATCHED_PARTIAL Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MATCHED_PARTIAL", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_07", "category": "Reconciliation", "kpi_name": "Partial Settlement Shortfall Rate (R5)", "actual_value": f"{partial_shortfall_rate:.2f}", "unit": "%", "formula": "(PARTIALLY_SETTLED Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("PARTIALLY_SETTLED", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_08", "category": "Reconciliation", "kpi_name": "Late Settlement Rate (R4)", "actual_value": f"{late_stl_rate:.2f}", "unit": "%", "formula": "(LATE_SETTLEMENT Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("LATE_SETTLEMENT", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_09", "category": "Reconciliation", "kpi_name": "Bank Timing Exception Rate (R4)", "actual_value": f"{timing_exc_rate:.2f}", "unit": "%", "formula": "(TIMING_EXCEPTION Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("TIMING_EXCEPTION", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_10", "category": "Reconciliation", "kpi_name": "Missing Settlement Rate (R7)", "actual_value": f"{missing_stl_rate:.2f}", "unit": "%", "formula": "(MISSING_SETTLEMENT Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MISSING_SETTLEMENT", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_11", "category": "Reconciliation", "kpi_name": "Missing Ledger Counterpart Rate (R7)", "actual_value": f"{missing_ledger_rate:.2f}", "unit": "%", "formula": "(MISSING_LEDGER Count / All Evaluated Cases) * 100", "numerator": str(class_counts.get("MISSING_LEDGER", 0)), "denominator": str(total_eval_pop), "population": "All 10,000 evaluated cases", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_12", "category": "Reconciliation", "kpi_name": "Missing Bank-Entry Rate (R7)", "actual_value": f"{missing_bank_rate:.2f}", "unit": "%", "formula": "(MISSING_BANK_ENTRY Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MISSING_BANK_ENTRY", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_13", "category": "Reconciliation", "kpi_name": "Ambiguous Match Rate (R8)", "actual_value": f"{ambig_match_rate:.2f}", "unit": "%", "formula": "(AMBIGUOUS_MATCH Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("AMBIGUOUS_MATCH", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_14", "category": "Reconciliation", "kpi_name": "Confirmed Duplicate Rate (R6)", "actual_value": f"{dup_conf_rate:.2f}", "unit": "%", "formula": "(DUPLICATE_CONFIRMED Count / Validated Settlements) * 100", "numerator": str(class_counts.get("DUPLICATE_CONFIRMED", 0)), "denominator": str(stl_record_count), "population": "10,065 validated settlement lines", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_15", "category": "Reconciliation", "kpi_name": "Duplicate Candidate Rate (R6)", "actual_value": f"{dup_cand_rate:.2f}", "unit": "%", "formula": "(DUPLICATE_CANDIDATE Count / Validated Settlements) * 100", "numerator": str(class_counts.get("DUPLICATE_CANDIDATE", 0)), "denominator": str(stl_record_count), "population": "10,065 validated settlement lines", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_16", "category": "Reconciliation", "kpi_name": "Refund Exception Rate (R9)", "actual_value": f"{refund_mismatch_rate:.2f}", "unit": "%", "formula": "(Refund Exceptions / Validated Refunds) * 100", "numerator": str(class_counts.get("REFUND_MISMATCH", 0) + class_counts.get("UNREVERSED_REFUND", 0) + class_counts.get("MISSING_REFUND_EVIDENCE", 0)), "denominator": str(ref_record_count), "population": "250 validated refund records", "source": "reconciliation_matches", "currency": "INR"},
        {"kpi_id": "KPI_REC_17", "category": "Reconciliation", "kpi_name": "Manual Review Rate", "actual_value": f"{manual_review_rate:.2f}", "unit": "%", "formula": "(MANUAL_REVIEW Count / Validated Ledger Txns) * 100", "numerator": str(class_counts.get("MANUAL_REVIEW", 0)), "denominator": str(eligible_ledger), "population": "Validated INR ledger transactions", "source": "reconciliation_matches", "currency": "INR"},

        # 11.4 Exception Management KPIs
        {"kpi_id": "KPI_EXC_01", "category": "Exception Management", "kpi_name": "Total Unresolved Exceptions (OPEN + REOPENED)", "actual_value": str(unresolved_exc_count), "unit": "Exceptions", "formula": "COUNT(*) WHERE resolution_status IN ('OPEN', 'REOPENED')", "numerator": str(unresolved_exc_count), "denominator": str(exc_record_count), "population": "800 total detected exceptions", "source": "reconciliation.exceptions", "currency": "INR"},
        {"kpi_id": "KPI_EXC_02", "category": "Exception Management", "kpi_name": "Total Resolved Exceptions", "actual_value": str(resolved_exc_count), "unit": "Exceptions", "formula": "COUNT(*) WHERE resolution_status = 'RESOLVED'", "numerator": str(resolved_exc_count), "denominator": str(exc_record_count), "population": "800 total detected exceptions", "source": "reconciliation.exceptions", "currency": "INR"},
        {"kpi_id": "KPI_EXC_03", "category": "Exception Management", "kpi_name": "Reopened Exception Count", "actual_value": str(reopened_exc_count), "unit": "Exceptions", "formula": "COUNT(*) WHERE resolution_status = 'REOPENED'", "numerator": str(reopened_exc_count), "denominator": str(exc_record_count), "population": "800 total detected exceptions", "source": "reconciliation.exceptions", "currency": "INR"},
        {"kpi_id": "KPI_EXC_04", "category": "Exception Management", "kpi_name": "Exception Resolution Rate", "actual_value": f"{exc_resolution_rate:.2f}", "unit": "%", "formula": "(Resolved Exceptions / Total Exceptions) * 100", "numerator": str(resolved_exc_count), "denominator": str(exc_record_count), "population": "800 total detected exceptions", "source": "reconciliation.exceptions", "currency": "INR"},
        {"kpi_id": "KPI_EXC_05", "category": "Exception Management", "kpi_name": "Average Resolution Time", "actual_value": f"{avg_res_days:.2f}", "unit": "Days", "formula": "AVG(exception_age_days) WHERE resolution_status = 'RESOLVED'", "numerator": str(sum(resolved_ages)), "denominator": str(len(resolved_ages)), "population": "95 resolved exceptions", "source": "reconciliation.exceptions", "currency": "N/A"},
        {"kpi_id": "KPI_EXC_06", "category": "Exception Management", "kpi_name": "Median Resolution Time", "actual_value": f"{median_res_days:.2f}", "unit": "Days", "formula": "MEDIAN(exception_age_days) WHERE resolution_status = 'RESOLVED'", "numerator": f"{median_res_days:.2f}", "denominator": "1", "population": "95 resolved exceptions", "source": "reconciliation.exceptions", "currency": "N/A"},

        # 11.5 Data Quality KPIs
        {"kpi_id": "KPI_DQ_01", "category": "Data Quality", "kpi_name": "Data Quality Pass Rate (Transactions)", "actual_value": f"{dq_report['summary_metrics']['dq_pass_rate_pct']:.2f}", "unit": "%", "formula": "(Validated Txns / Raw Ingested Txns) * 100", "numerator": str(valid_txn_count), "denominator": str(raw_txn_count), "population": "9,955 raw ingested transaction rows", "source": "data_quality_before_after", "currency": "ALL"},
        {"kpi_id": "KPI_DQ_02", "category": "Data Quality", "kpi_name": "Mandatory-Field Completeness Rate", "actual_value": f"{dq_report['summary_metrics']['mandatory_field_completeness_pct']:.2f}", "unit": "%", "formula": "((Raw Rows - Missing Mandatory/Date Rows) / Raw Rows) * 100", "numerator": str(raw_txn_count - 17), "denominator": str(raw_txn_count), "population": "9,955 raw ingested transaction rows", "source": "data_quality_before_after", "currency": "ALL"},
        {"kpi_id": "KPI_DQ_03", "category": "Data Quality", "kpi_name": "Quarantine Rate", "actual_value": f"{dq_report['summary_metrics']['quarantine_rate_pct']:.2f}", "unit": "%", "formula": "(Quarantined Rows / Raw Ingested Txns) * 100", "numerator": str(quar_record_count), "denominator": str(raw_txn_count), "population": "9,955 raw ingested transaction rows", "source": "quarantine_records", "currency": "ALL"},

        # 11.6 Ground-Truth Testing KPIs
        {"kpi_id": "KPI_GT_01", "category": "Ground Truth QA", "kpi_name": "Overall Classification Accuracy (10K Cases)", "actual_value": f"{overall_accuracy_pct:.2f}", "unit": "%", "formula": "(Correctly Classified Cases / 10,000 Total Cases) * 100", "numerator": str(correct_class_count), "denominator": str(len(gt_rows)), "population": "All 10,000 ground-truth cases", "source": "ground_truth_evaluation", "currency": "N/A"},
        {"kpi_id": "KPI_GT_02", "category": "Ground Truth QA", "kpi_name": "Planted Exception Recall (Detection Rate)", "actual_value": f"{planted_exc_recall_pct:.2f}", "unit": "%", "formula": "(True Positives / Total Planted Exceptions) * 100", "numerator": str(planted_exc_detected), "denominator": str(planted_exc_total), "population": "800 planted exception cases", "source": "ground_truth_evaluation", "currency": "N/A"},
        {"kpi_id": "KPI_GT_03", "category": "Ground Truth QA", "kpi_name": "Planted Exception Precision", "actual_value": f"{planted_exc_precision_pct:.2f}", "unit": "%", "formula": "(True Positives / (True Positives + False Positives)) * 100", "numerator": str(planted_exc_detected), "denominator": str(planted_exc_detected + clean_false_positives), "population": "All flagged exceptions", "source": "ground_truth_evaluation", "currency": "N/A"},
        {"kpi_id": "KPI_GT_04", "category": "Ground Truth QA", "kpi_name": "Clean-Record False-Positive Rate", "actual_value": f"{clean_fp_rate_pct:.2f}", "unit": "%", "formula": "(Clean Records Flagged as Exception / 9,200 Clean Cases) * 100", "numerator": str(clean_false_positives), "denominator": str(clean_total), "population": "9,200 clean match cases", "source": "ground_truth_evaluation", "currency": "N/A"},
    ]

    return {
        "kpi_catalog": kpi_catalog,
        "class_counts": class_counts,
        "aging_summary": aging_summary,
        "cat_summary": [
            {
                **v,
                "expected_amount_inr": f"{v['expected_amount_inr']:.2f}",
                "observed_amount_inr": f"{v['observed_amount_inr']:.2f}",
                "signed_variance_inr": f"{v['signed_variance_inr']:.2f}",
                "outstanding_exposure_inr": f"{v['outstanding_exposure_inr']:.2f}",
                "confirmed_loss_inr": f"{v['confirmed_loss_inr']:.2f}",
                "exposure_share_pct": f"{pct(int(v['outstanding_exposure_inr'] * 100), int(outstanding_exposure * 100)):.2f}",
            }
            for v in sorted(cat_summary.values(), key=lambda x: x["outstanding_exposure_inr"], reverse=True)
        ],
        "merch_exposure": [
            {
                **v,
                "gross_txn_inr": f"{v['gross_txn_inr']:.2f}",
                "expected_net_inr": f"{v['expected_net_inr']:.2f}",
                "observed_net_inr": f"{v['observed_net_inr']:.2f}",
                "outstanding_exposure_inr": f"{v['outstanding_exposure_inr']:.2f}",
                "exposure_share_pct": f"{pct(int(v['outstanding_exposure_inr'] * 100), int(outstanding_exposure * 100)):.2f}",
            }
            for v in sorted(merch_exposure.values(), key=lambda x: x["outstanding_exposure_inr"], reverse=True)
        ],
        "ground_truth_summary": {
            "total_evaluated_cases": len(gt_rows),
            "planted_exception_cases": planted_exc_total,
            "clean_baseline_cases": clean_total,
            "correctly_classified_cases": correct_class_count,
            "incorrectly_classified_cases": len(gt_rows) - correct_class_count,
            "planted_exceptions_detected": planted_exc_detected,
            "false_positives": clean_false_positives,
            "false_negatives": false_negatives,
            "variance_calculation_errors": variance_errors,
            "overall_classification_accuracy_pct": overall_accuracy_pct,
            "planted_exception_recall_pct": planted_exc_recall_pct,
            "planted_exception_precision_pct": planted_exc_precision_pct,
            "clean_record_false_positive_rate_pct": clean_fp_rate_pct,
        },
        "scenario_breakdown": list(sorted(scen_eval.values(), key=lambda x: x["planted_scenario"])),
        "ground_truth_row_details": gt_eval_rows,
    }
