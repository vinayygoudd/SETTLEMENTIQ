"""Source CSV Ingestion & Schema Verification for SettlementIQ."""
import csv
import pathlib
from typing import Any, Dict, List

from .config import DEFAULT_CONFIG, SettlementIQConfig

REQUIRED_SCHEMAS: Dict[str, List[str]] = {
    "merchants": [
        "merchant_id", "merchant_name", "merchant_category", "onboarding_date",
        "merchant_status", "settlement_frequency", "contractual_fee_rate",
        "contractual_fixed_fee", "currency", "region", "operational_classification",
        "default_payment_gateway", "settlement_sla_days", "is_synthetic"
    ],
    "transactions": [
        "transaction_id", "customer_id", "merchant_id", "payment_reference",
        "order_reference", "transaction_timestamp", "transaction_date",
        "transaction_amount", "currency", "payment_method", "payment_status",
        "payment_gateway", "settlement_expected_date", "transaction_fee",
        "expected_net_amount", "ingestion_timestamp", "source_system",
        "record_version", "is_synthetic"
    ],
    "settlements": [
        "settlement_id", "settlement_reference", "transaction_id",
        "payment_reference", "merchant_id", "settlement_batch_id",
        "settlement_timestamp", "settlement_date", "gross_amount",
        "fee_amount", "net_settlement_amount", "currency", "settlement_status",
        "settlement_type", "allocation_line_no", "total_allocation_lines",
        "source_system", "ingestion_timestamp", "is_synthetic"
    ],
    "bank_entries": [
        "bank_entry_id", "bank_reference", "settlement_reference",
        "transaction_reference", "merchant_id", "entry_timestamp", "value_date",
        "credit_amount", "debit_amount", "signed_bank_amount", "currency",
        "bank_description", "bank_status", "ingestion_timestamp", "is_synthetic"
    ],
    "refunds": [
        "refund_id", "original_transaction_id", "refund_reference",
        "merchant_id", "refund_timestamp", "refund_amount",
        "settled_refund_deduction", "currency", "refund_status",
        "refund_reason", "settlement_reference", "bank_reference",
        "ingestion_timestamp", "is_synthetic"
    ],
    "ground_truth": [
        "synthetic_case_id", "source_record_id", "merchant_id", "payment_gateway",
        "planted_scenario", "expected_classification", "expected_match_group",
        "expected_amount", "observed_amount", "expected_variance",
        "expected_abs_exposure", "expected_confirmed_loss",
        "expected_exception_type", "expected_severity",
        "expected_resolution_state", "is_planted_exception"
    ],
}


class SchemaValidationError(Exception):
    """Raised when a required CSV file or column is missing."""


def validate_file_schema(file_path: pathlib.Path, expected_columns: List[str]) -> List[str]:
    """Verify file existence, non-empty content, and required header columns."""
    if not file_path.exists():
        raise SchemaValidationError(f"Required input file not found: {file_path}")
    if file_path.stat().st_size == 0:
        raise SchemaValidationError(f"Input file is empty (0 bytes): {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration as exc:
            raise SchemaValidationError(f"Input file has no header row: {file_path}") from exc

    missing = [c for c in expected_columns if c not in headers]
    if missing:
        raise SchemaValidationError(
            f"File {file_path.name} is missing required columns: {missing}"
        )
    return headers


def load_raw_csv(file_path: pathlib.Path, entity_name: str) -> List[Dict[str, Any]]:
    """Validate schema and load raw CSV rows without modifying source values."""
    if entity_name in REQUIRED_SCHEMAS:
        validate_file_schema(file_path, REQUIRED_SCHEMAS[entity_name])
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def ingest_all_sources(base_dir: pathlib.Path | None = None, config: SettlementIQConfig = DEFAULT_CONFIG) -> Dict[str, List[Dict[str, Any]]]:
    """Load all raw synthetic CSV inputs and ground truth."""
    root = base_dir or config.project_root
    in_dir = root / "data" / "synthetic_inputs"
    gt_dir = root / "data" / "ground_truth"

    return {
        "merchants": load_raw_csv(in_dir / "merchants.csv", "merchants"),
        "transactions": load_raw_csv(in_dir / "transactions.csv", "transactions"),
        "settlements": load_raw_csv(in_dir / "settlements.csv", "settlements"),
        "bank_entries": load_raw_csv(in_dir / "bank_entries.csv", "bank_entries"),
        "refunds": load_raw_csv(in_dir / "refunds.csv", "refunds"),
        "ground_truth": load_raw_csv(gt_dir / "ground_truth.csv", "ground_truth"),
    }
