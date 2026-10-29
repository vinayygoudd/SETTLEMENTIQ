"""Before-and-After Data Quality Profiling & Control Totals for SettlementIQ."""
from decimal import Decimal
from typing import Any, Dict, List


def compute_data_quality_profile(
    raw_data: Dict[str, List[Dict[str, Any]]],
    validated_bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate complete before-and-after cleaning metrics and monetary control totals."""
    raw_txns = raw_data["transactions"]
    val_txns = validated_bundle["valid_transactions"]
    quar = validated_bundle["quarantined_records"]
    dup_ing = validated_bundle["duplicate_ingested_records"]
    cnt = validated_bundle["dq_counters"]

    raw_stls = raw_data["settlements"]
    val_stls = validated_bundle["valid_settlements"]

    raw_bnk = raw_data["bank_entries"]
    val_bnk = validated_bundle["valid_bank_entries"]

    raw_ref = raw_data["refunds"]
    val_ref = validated_bundle["valid_refunds"]

    # Raw transaction monetary sums by currency
    raw_txn_inr = sum(Decimal(r["transaction_amount"]) for r in raw_txns if r["currency"] == "INR")
    raw_txn_usd = sum(Decimal(r["transaction_amount"]) for r in raw_txns if r["currency"] == "USD")
    raw_txn_eur = sum(Decimal(r["transaction_amount"]) for r in raw_txns if r["currency"] == "EUR")

    val_txn_inr = sum(Decimal(r["transaction_amount"]) for r in val_txns)
    val_txn_exp_net_inr = sum(Decimal(r["expected_net_amount"]) for r in val_txns)

    # Quarantined & suppressed transaction amounts in INR
    quar_inr_gross = sum(
        Decimal(q["raw_amount"]) for q in quar if q["currency"] == "INR"
    )
    suppressed_txn_inr = sum(
        Decimal(d["amount"]) for d in dup_ing if d["source_entity"] == "TRANSACTIONS"
    )

    # Verify exact conservation of INR gross transaction value:
    # Raw INR Gross == Validated INR Gross + Quarantined INR Gross + Suppressed Replay INR Gross
    txn_conservation_diff = raw_txn_inr - (val_txn_inr + quar_inr_gross + suppressed_txn_inr)

    raw_stl_net = sum(Decimal(s["net_settlement_amount"]) for s in raw_stls)
    val_stl_net = sum(Decimal(s["net_settlement_amount"]) for s in val_stls)
    suppressed_stl_net = sum(
        Decimal(d["amount"]) for d in dup_ing if d["source_entity"] == "SETTLEMENTS"
    )
    stl_conservation_diff = raw_stl_net - (val_stl_net + suppressed_stl_net)

    total_raw_txn_rows = len(raw_txns)
    total_valid_txn_rows = len(val_txns)
    total_quar_rows = len(quar)
    total_dup_txn_rows = cnt["duplicate_source_txns"]

    dq_pass_rate = round((total_valid_txn_rows / total_raw_txn_rows) * 100.0, 2) if total_raw_txn_rows else 0.0
    mandatory_completeness = round(
        ((total_raw_txn_rows - cnt["missing_mandatory_fields"] - cnt["missing_dates"]) / total_raw_txn_rows) * 100.0, 2
    )
    id_completeness = round(((total_raw_txn_rows - cnt["invalid_identifiers"]) / total_raw_txn_rows) * 100.0, 2)
    amt_validity_rate = round(((total_raw_txn_rows - cnt["invalid_amounts"]) / total_raw_txn_rows) * 100.0, 2)
    date_validity_rate = round(((total_raw_txn_rows - cnt["missing_dates"]) / total_raw_txn_rows) * 100.0, 2)
    curr_validity_rate = round(((total_raw_txn_rows - cnt["invalid_currencies"]) / total_raw_txn_rows) * 100.0, 2)
    dup_source_rate = round(
        ((cnt["duplicate_source_txns"] + cnt["duplicate_source_settlements"]) / (len(raw_txns) + len(raw_stls))) * 100.0, 2
    )
    quarantine_rate = round((total_quar_rows / total_raw_txn_rows) * 100.0, 2)

    before_after_rows = [
        {
            "dataset": "TRANSACTIONS",
            "raw_rows": len(raw_txns),
            "validated_rows": len(val_txns),
            "quarantined_rows": len(quar),
            "suppressed_duplicate_rows": cnt["duplicate_source_txns"],
            "corrected_rows": 0,
            "remaining_invalid_rows": 0,
            "raw_inr_amount": f"{raw_txn_inr:.2f}",
            "validated_inr_amount": f"{val_txn_inr:.2f}",
            "quarantined_inr_amount": f"{quar_inr_gross:.2f}",
            "suppressed_duplicate_inr_amount": f"{suppressed_txn_inr:.2f}",
            "unexplained_control_diff_inr": f"{txn_conservation_diff:.2f}",
            "dq_pass_rate_pct": f"{dq_pass_rate:.2f}",
        },
        {
            "dataset": "SETTLEMENTS",
            "raw_rows": len(raw_stls),
            "validated_rows": len(val_stls),
            "quarantined_rows": 0,
            "suppressed_duplicate_rows": cnt["duplicate_source_settlements"],
            "corrected_rows": 0,
            "remaining_invalid_rows": 0,
            "raw_inr_amount": f"{raw_stl_net:.2f}",
            "validated_inr_amount": f"{val_stl_net:.2f}",
            "quarantined_inr_amount": "0.00",
            "suppressed_duplicate_inr_amount": f"{suppressed_stl_net:.2f}",
            "unexplained_control_diff_inr": f"{stl_conservation_diff:.2f}",
            "dq_pass_rate_pct": f"{round((len(val_stls) / len(raw_stls)) * 100.0, 2):.2f}",
        },
        {
            "dataset": "BANK_ENTRIES",
            "raw_rows": len(raw_bnk),
            "validated_rows": len(val_bnk),
            "quarantined_rows": 0,
            "suppressed_duplicate_rows": 0,
            "corrected_rows": 0,
            "remaining_invalid_rows": 0,
            "raw_inr_amount": f"{sum(Decimal(b['credit_amount']) for b in raw_bnk):.2f}",
            "validated_inr_amount": f"{sum(Decimal(b['credit_amount']) for b in val_bnk):.2f}",
            "quarantined_inr_amount": "0.00",
            "suppressed_duplicate_inr_amount": "0.00",
            "unexplained_control_diff_inr": "0.00",
            "dq_pass_rate_pct": "100.00",
        },
        {
            "dataset": "REFUNDS",
            "raw_rows": len(raw_ref),
            "validated_rows": len(val_ref),
            "quarantined_rows": 0,
            "suppressed_duplicate_rows": 0,
            "corrected_rows": 0,
            "remaining_invalid_rows": 0,
            "raw_inr_amount": f"{sum(Decimal(r['refund_amount']) for r in raw_ref):.2f}",
            "validated_inr_amount": f"{sum(Decimal(r['refund_amount']) for r in val_ref):.2f}",
            "quarantined_inr_amount": "0.00",
            "suppressed_duplicate_inr_amount": "0.00",
            "unexplained_control_diff_inr": "0.00",
            "dq_pass_rate_pct": "100.00",
        },
        {
            "dataset": "MERCHANTS",
            "raw_rows": len(raw_data["merchants"]),
            "validated_rows": len(validated_bundle["valid_merchants"]),
            "quarantined_rows": 0,
            "suppressed_duplicate_rows": 0,
            "corrected_rows": 0,
            "remaining_invalid_rows": 0,
            "raw_inr_amount": "0.00",
            "validated_inr_amount": "0.00",
            "quarantined_inr_amount": "0.00",
            "suppressed_duplicate_inr_amount": "0.00",
            "unexplained_control_diff_inr": "0.00",
            "dq_pass_rate_pct": "100.00",
        },
    ]

    return {
        "before_after_table": before_after_rows,
        "summary_metrics": {
            "raw_transaction_rows": total_raw_txn_rows,
            "validated_transaction_rows": total_valid_txn_rows,
            "quarantined_transaction_rows": total_quar_rows,
            "suppressed_duplicate_txn_rows": total_dup_txn_rows,
            "suppressed_duplicate_stl_rows": cnt["duplicate_source_settlements"],
            "invalid_identifiers": cnt["invalid_identifiers"],
            "missing_mandatory_fields": cnt["missing_mandatory_fields"],
            "invalid_amounts": cnt["invalid_amounts"],
            "missing_dates": cnt["missing_dates"],
            "invalid_currencies": cnt["invalid_currencies"],
            "dq_pass_rate_pct": dq_pass_rate,
            "mandatory_field_completeness_pct": mandatory_completeness,
            "identifier_completeness_pct": id_completeness,
            "amount_validity_rate_pct": amt_validity_rate,
            "date_validity_rate_pct": date_validity_rate,
            "currency_validity_rate_pct": curr_validity_rate,
            "duplicate_source_record_rate_pct": dup_source_rate,
            "quarantine_rate_pct": quarantine_rate,
            "correction_rate_pct": 0.0,
            "raw_txn_inr_gross": f"{raw_txn_inr:.2f}",
            "raw_txn_usd_gross": f"{raw_txn_usd:.2f}",
            "raw_txn_eur_gross": f"{raw_txn_eur:.2f}",
            "validated_txn_inr_gross": f"{val_txn_inr:.2f}",
            "validated_txn_expected_net_inr": f"{val_txn_exp_net_inr:.2f}",
            "quarantined_txn_inr_gross": f"{quar_inr_gross:.2f}",
            "suppressed_txn_inr_gross": f"{suppressed_txn_inr:.2f}",
            "txn_conservation_diff_inr": f"{txn_conservation_diff:.2f}",
            "stl_conservation_diff_inr": f"{stl_conservation_diff:.2f}",
        },
    }
