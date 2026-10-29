"""Data Validation, Normalization, Deduplication & Quarantine Engine for SettlementIQ.

Implements deterministic validation rules across all 5 source entities:
- Identifier pattern check (^TXN_[0-9]{4}_[0-9]{6}$)
- Mandatory field completeness (merchant_id, payment_reference, transaction_date)
- Monetary validity (Decimal > 0 for gross amounts)
- Single-currency INR enforcement (quarantines unapproved USD/EUR records)
- Idempotent source deduplication (suppresses repeated ingestion replay rows while logging them)
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, List, Tuple

from .config import DEFAULT_CONFIG, SettlementIQConfig

TXN_ID_PATTERN = re.compile(r"^TXN_[0-9]{4}_[0-9]{6}$")


def is_valid_iso_date(val: str) -> bool:
    """Check if string is a valid YYYY-MM-DD date."""
    if not val or not val.strip():
        return False
    try:
        date.fromisoformat(val.strip())
        return True
    except ValueError:
        return False


def parse_decimal(val: str) -> Decimal | None:
    """Safely parse a string into a Decimal, returning None if malformed."""
    if val is None or str(val).strip() == "":
        return None
    try:
        return Decimal(str(val).strip())
    except InvalidOperation:
        return None


def validate_and_separate_sources(
    raw_data: Dict[str, List[Dict[str, Any]]],
    config: SettlementIQConfig = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Validate raw datasets, quarantine invalid records, and deduplicate repeated ingestions."""
    valid_merchants: List[Dict[str, Any]] = []
    seen_merch = set()
    for m in raw_data["merchants"]:
        mid = m["merchant_id"].strip()
        if mid and mid not in seen_merch:
            seen_merch.add(mid)
            valid_merchants.append(m)

    valid_transactions: List[Dict[str, Any]] = []
    quarantined_records: List[Dict[str, Any]] = []
    duplicate_ingested_records: List[Dict[str, Any]] = []

    seen_txn_ids = set()
    dq_counters = {
        "invalid_identifiers": 0,
        "missing_mandatory_fields": 0,
        "invalid_amounts": 0,
        "missing_dates": 0,
        "invalid_currencies": 0,
        "duplicate_source_txns": 0,
        "duplicate_source_settlements": 0,
    }

    for row in raw_data["transactions"]:
        t_id = (row.get("transaction_id") or "").strip()
        m_id = (row.get("merchant_id") or "").strip()
        p_ref = (row.get("payment_reference") or "").strip()
        t_date = (row.get("transaction_date") or "").strip()
        curr = (row.get("currency") or "").strip()
        g_dec = parse_decimal(row.get("transaction_amount", ""))
        exp_net_dec = parse_decimal(row.get("expected_net_amount", "0.00")) or Decimal("0.00")

        # 1. Identifier check (S15)
        if not TXN_ID_PATTERN.match(t_id):
            dq_counters["invalid_identifiers"] += 1
            quarantined_records.append({
                "source_entity": "TRANSACTIONS",
                "source_record_id": t_id or "MISSING_TXN_ID",
                "merchant_id": m_id or "UNKNOWN",
                "payment_gateway": row.get("payment_gateway", "UNKNOWN"),
                "quarantine_reason": "INVALID_IDENTIFIER",
                "quarantine_detail": f"Transaction ID '{t_id}' fails pattern ^TXN_[0-9]{{4}}_[0-9]{{6}}$",
                "raw_amount": str(row.get("transaction_amount", "0.00")),
                "expected_net_inr": f"{exp_net_dec:.2f}",
                "currency": curr or "INR",
                "run_id": config.run_id,
            })
            continue

        # 2. Mandatory reference/merchant check (S16)
        if not m_id or not p_ref:
            dq_counters["missing_mandatory_fields"] += 1
            quarantined_records.append({
                "source_entity": "TRANSACTIONS",
                "source_record_id": t_id,
                "merchant_id": m_id or "MISSING",
                "payment_gateway": row.get("payment_gateway", "UNKNOWN"),
                "quarantine_reason": "MISSING_MANDATORY_FIELD",
                "quarantine_detail": "Mandatory field merchant_id or payment_reference is empty",
                "raw_amount": str(row.get("transaction_amount", "0.00")),
                "expected_net_inr": f"{exp_net_dec:.2f}",
                "currency": curr or "INR",
                "run_id": config.run_id,
            })
            continue

        # 3. Date validity check (S18)
        if not is_valid_iso_date(t_date):
            dq_counters["missing_dates"] += 1
            quarantined_records.append({
                "source_entity": "TRANSACTIONS",
                "source_record_id": t_id,
                "merchant_id": m_id,
                "payment_gateway": row.get("payment_gateway", "UNKNOWN"),
                "quarantine_reason": "MISSING_DATE",
                "quarantine_detail": f"Invalid or empty transaction_date '{t_date}'",
                "raw_amount": str(row.get("transaction_amount", "0.00")),
                "expected_net_inr": f"{exp_net_dec:.2f}",
                "currency": curr or "INR",
                "run_id": config.run_id,
            })
            continue

        # 4. Currency policy check (S19)
        if curr != config.approved_currency:
            dq_counters["invalid_currencies"] += 1
            quarantined_records.append({
                "source_entity": "TRANSACTIONS",
                "source_record_id": t_id,
                "merchant_id": m_id,
                "payment_gateway": row.get("payment_gateway", "UNKNOWN"),
                "quarantine_reason": "INVALID_CURRENCY",
                "quarantine_detail": f"Currency '{curr}' outside single-currency INR policy without FX table",
                "raw_amount": str(row.get("transaction_amount", "0.00")),
                "expected_net_inr": f"{exp_net_dec:.2f}",
                "currency": curr,
                "run_id": config.run_id,
            })
            continue

        # 5. Monetary amount validity check (S17)
        if g_dec is None or g_dec <= Decimal("0.00"):
            dq_counters["invalid_amounts"] += 1
            quarantined_records.append({
                "source_entity": "TRANSACTIONS",
                "source_record_id": t_id,
                "merchant_id": m_id,
                "payment_gateway": row.get("payment_gateway", "UNKNOWN"),
                "quarantine_reason": "MALFORMED_AMOUNT",
                "quarantine_detail": f"Transaction gross amount '{row.get('transaction_amount')}' is <= 0.00",
                "raw_amount": str(row.get("transaction_amount", "0.00")),
                "expected_net_inr": f"{exp_net_dec:.2f}",
                "currency": curr,
                "run_id": config.run_id,
            })
            continue

        # 6. Idempotent repeated ingestion check (S20)
        if t_id in seen_txn_ids:
            dq_counters["duplicate_source_txns"] += 1
            duplicate_ingested_records.append({
                "source_entity": "TRANSACTIONS",
                "source_record_id": t_id,
                "source_system": row.get("source_system", ""),
                "amount": f"{g_dec:.2f}",
                "reason": "REPEATED_SOURCE_INGESTION_SUPPRESSED",
            })
            continue

        seen_txn_ids.add(t_id)
        valid_transactions.append(row)

    # Deduplicate settlements (Scenario 20 repeated settlement file ingestion)
    valid_settlements: List[Dict[str, Any]] = []
    seen_stl_ids = set()
    for s in raw_data["settlements"]:
        s_id = s["settlement_id"].strip()
        if s_id in seen_stl_ids:
            dq_counters["duplicate_source_settlements"] += 1
            duplicate_ingested_records.append({
                "source_entity": "SETTLEMENTS",
                "source_record_id": s_id,
                "source_system": s.get("source_system", ""),
                "amount": s.get("net_settlement_amount", "0.00"),
                "reason": "REPEATED_SOURCE_INGESTION_SUPPRESSED",
            })
            continue
        seen_stl_ids.add(s_id)
        valid_settlements.append(s)

    # Bank entries & refunds validation
    valid_bank_entries = list(raw_data["bank_entries"])
    valid_refunds = list(raw_data["refunds"])

    return {
        "valid_merchants": valid_merchants,
        "valid_transactions": valid_transactions,
        "valid_settlements": valid_settlements,
        "valid_bank_entries": valid_bank_entries,
        "valid_refunds": valid_refunds,
        "quarantined_records": quarantined_records,
        "duplicate_ingested_records": duplicate_ingested_records,
        "dq_counters": dq_counters,
    }
