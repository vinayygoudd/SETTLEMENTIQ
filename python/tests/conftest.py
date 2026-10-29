import pathlib
import pytest
from settlementiq.config import DEFAULT_CONFIG, SettlementIQConfig
from settlementiq.ingestion import ingest_all_sources
from settlementiq.validation import validate_and_separate_sources
from settlementiq.data_quality import compute_data_quality_profile
from settlementiq.database import init_and_load_database
from settlementiq.reconciliation_runner import execute_sql_reconciliation
from settlementiq.kpi_calculations import calculate_all_kpis_and_evaluation


@pytest.fixture(scope="session")
def executed_context():
    cfg = DEFAULT_CONFIG
    raw_data = ingest_all_sources(cfg.project_root, cfg)
    val_bundle = validate_and_separate_sources(raw_data, cfg)
    dq_report = compute_data_quality_profile(raw_data, val_bundle)
    conn = init_and_load_database(raw_data, val_bundle, cfg)
    recon_summary = execute_sql_reconciliation(conn, cfg)
    kpi_bundle = calculate_all_kpis_and_evaluation(conn, raw_data, dq_report, cfg)
    yield {
        "config": cfg,
        "raw_data": raw_data,
        "val_bundle": val_bundle,
        "dq_report": dq_report,
        "conn": conn,
        "recon_summary": recon_summary,
        "kpi_bundle": kpi_bundle,
    }
    conn.close()
