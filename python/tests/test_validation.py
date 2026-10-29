import pathlib
import pytest
from settlementiq.ingestion import SchemaValidationError, validate_file_schema, REQUIRED_SCHEMAS
from settlementiq.validation import is_valid_iso_date, parse_decimal


def test_04_required_schema_validation_passes(executed_context):
    root = executed_context["config"].project_root
    for name, cols in REQUIRED_SCHEMAS.items():
        sub = "ground_truth" if name == "ground_truth" else "synthetic_inputs"
        hdrs = validate_file_schema(root / "data" / sub / f"{name}.csv", cols)
        assert set(cols).issubset(set(hdrs))


def test_05_missing_file_raises_explicit_error(tmp_path):
    with pytest.raises(SchemaValidationError, match="Required input file not found"):
        validate_file_schema(tmp_path / "nonexistent.csv", ["transaction_id"])


def test_06_missing_columns_raises_explicit_error(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("col_a,col_b\n1,2\n", encoding="utf-8")
    with pytest.raises(SchemaValidationError, match="missing required columns"):
        validate_file_schema(bad_csv, ["transaction_id", "merchant_id"])


def test_07_quarantine_captures_missing_and_invalid_values(executed_context):
    cnt = executed_context["val_bundle"]["dq_counters"]
    assert cnt["invalid_identifiers"] == 10
    assert cnt["missing_mandatory_fields"] == 10
    assert cnt["invalid_amounts"] == 10
    assert cnt["missing_dates"] == 7
    assert cnt["invalid_currencies"] == 8
    assert len(executed_context["val_bundle"]["quarantined_records"]) == 45


def test_08_cross_currency_protection_quarantines_usd_and_eur(executed_context):
    val_txns = executed_context["val_bundle"]["valid_transactions"]
    assert all(r["currency"] == "INR" for r in val_txns)
    quar = executed_context["val_bundle"]["quarantined_records"]
    foreign_quar = [q for q in quar if q["quarantine_reason"] == "INVALID_CURRENCY"]
    assert len(foreign_quar) == 8
    assert {q["currency"] for q in foreign_quar} == {"USD", "EUR"}


def test_09_duplicate_ingestion_suppressed_idempotently(executed_context):
    cnt = executed_context["val_bundle"]["dq_counters"]
    assert cnt["duplicate_source_txns"] == 25
    assert cnt["duplicate_source_settlements"] == 25
    assert len(executed_context["val_bundle"]["duplicate_ingested_records"]) == 50
