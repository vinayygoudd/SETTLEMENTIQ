"""End-to-End Pipeline Orchestrator & CLI Entry Point for SettlementIQ."""
import argparse
import json
import pathlib
import time
from typing import Any, Dict

from .config import DEFAULT_CONFIG, SettlementIQConfig
from .data_quality import compute_data_quality_profile
from .database import init_and_load_database, persist_sqlite_snapshot
from .export import export_all_results
from .ingestion import ingest_all_sources
from .kpi_calculations import calculate_all_kpis_and_evaluation
from .logging_config import get_logger
from .reconciliation_runner import execute_sql_reconciliation
from .synthetic_data import generate_and_save_all
from .validation import validate_and_separate_sources
from .visualization import generate_all_charts


def run_complete_pipeline(
    base_dir: pathlib.Path | None = None,
    config: SettlementIQConfig = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Execute the complete SettlementIQ workflow deterministically from start to finish."""
    root = base_dir or config.project_root
    log_path = root / "outputs" / "execution_log.txt"
    if log_path.exists():
        log_path.unlink()
    logger = get_logger("settlementiq.orchestrator", log_path)

    t0 = time.time()
    logger.info("======================================================================")
    logger.info("Starting SettlementIQ End-to-End Pipeline (Run ID: %s)", config.run_id)
    logger.info("Random Seed: %d | Rule Version: %s", config.random_seed, config.rule_version)
    logger.info("======================================================================")

    # Step 1: Generate Synthetic Datasets
    logger.info("[Step 1/7] Generating deterministic synthetic datasets (10,000 cases, 28 scenarios)...")
    gen_summary = generate_and_save_all(root, config)
    logger.info(
        "Generated %d transactions, %d settlements, %d bank entries, %d refunds, %d merchants.",
        gen_summary["row_counts"]["transactions_csv"],
        gen_summary["row_counts"]["settlements_csv"],
        gen_summary["row_counts"]["bank_entries_csv"],
        gen_summary["row_counts"]["refunds_csv"],
        gen_summary["row_counts"]["merchants_csv"],
    )

    # Step 2: Ingest & Validate Schema
    logger.info("[Step 2/7] Ingesting raw CSV files and validating required schemas...")
    raw_data = ingest_all_sources(root, config)
    logger.info("Schema validation passed for all 6 files.")

    # Step 3: Validate Records, Quarantine Defects & Deduplicate Replay Rows
    logger.info("[Step 3/7] Running record-level validation, quarantine, and idempotency checks...")
    val_bundle = validate_and_separate_sources(raw_data, config)
    dq_report = compute_data_quality_profile(raw_data, val_bundle)
    logger.info(
        "Validation complete: %d valid transactions, %d quarantined records, %d suppressed replay rows. Conservation diff: %s INR",
        len(val_bundle["valid_transactions"]),
        len(val_bundle["quarantined_records"]),
        len(val_bundle["duplicate_ingested_records"]),
        dq_report["summary_metrics"]["txn_conservation_diff_inr"],
    )

    # Step 4: Initialize Relational Database & Load Validated Layers
    logger.info("[Step 4/7] Initializing relational database and loading staging/validated tables...")
    conn = init_and_load_database(raw_data, val_bundle, config)

    # Step 5: Execute Authoritative SQL Reconciliation Engine (Rules R1–R9)
    logger.info("[Step 5/7] Executing authoritative SQL reconciliation rules (R1–R9)...")
    recon_summary = execute_sql_reconciliation(conn, config)
    persist_sqlite_snapshot(conn, root / "data" / "processed" / "settlementiq_authoritative.sqlite")
    logger.info(
        "Reconciliation complete: %d matched, %d exceptions, Recon Rate=%.2f%%, Unresolved Exposure=%s INR",
        recon_summary["matched_count"],
        recon_summary["exception_count"],
        recon_summary["reconciliation_rate_pct"],
        recon_summary["outstanding_exposure_inr"],
    )

    # Step 6: Calculate All KPIs & Evaluate Against Independent Ground Truth
    logger.info("[Step 6/7] Computing KPIs and evaluating against isolated ground truth...")
    kpi_bundle = calculate_all_kpis_and_evaluation(conn, raw_data, dq_report, config)
    gt_sum = kpi_bundle["ground_truth_summary"]
    logger.info(
        "Ground-Truth Evaluation: Overall Accuracy=%.2f%% (%d/%d), Exception Recall=%.2f%%, False Positives=%d",
        gt_sum["overall_classification_accuracy_pct"],
        gt_sum["correctly_classified_cases"],
        gt_sum["total_evaluated_cases"],
        gt_sum["planted_exception_recall_pct"],
        gt_sum["false_positives"],
    )

    # Step 7: Export All Machine-Readable Reports & Charts
    logger.info("[Step 7/7] Exporting CSV/JSON/Markdown reports and high-resolution charts...")
    exported_files = export_all_results(conn, gen_summary, dq_report, recon_summary, kpi_bundle, root, config)
    chart_files = generate_all_charts(dq_report, recon_summary, kpi_bundle, root, config)
    conn.close()

    elapsed = round(time.time() - t0, 2)
    logger.info("SettlementIQ pipeline completed in %.2f seconds.", elapsed)
    return {
        "generation_summary": gen_summary,
        "dq_report": dq_report,
        "reconciliation_summary": recon_summary,
        "ground_truth_summary": gt_sum,
        "exported_files": {k: str(v) for k, v in exported_files.items()},
        "charts": [str(p) for p in chart_files],
        "elapsed_seconds": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SettlementIQ End-to-End Orchestration CLI")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic data generation")
    args = parser.parse_args()
    cfg = SettlementIQConfig(random_seed=args.seed)
    res = run_complete_pipeline(config=cfg)
    print(json.dumps({
        "reconciliation_summary": res["reconciliation_summary"],
        "ground_truth_summary": res["ground_truth_summary"],
        "dq_summary": res["dq_report"]["summary_metrics"],
        "elapsed_seconds": res["elapsed_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
