# SettlementIQ — Python Analytics, Validation & Orchestration Package

This package (`settlementiq`) implements:
1. Deterministic synthetic dataset generation (`synthetic_data.py`, Seed=42, 10,000 cases across 28 scenarios).
2. Schema & file verification (`ingestion.py`).
3. Record-level monetary/currency/date/identifier validation, quarantine, and idempotency (`validation.py`).
4. Before-and-after data quality profiling (`data_quality.py`).
5. Relational database loading & authoritative SQL reconciliation execution (`database.py`, `reconciliation_runner.py`).
6. Complete KPI calculation & isolated ground-truth evaluation (`kpi_calculations.py`).
7. High-resolution financial chart generation (`visualization.py`) and CSV/JSON/Markdown reporting (`export.py`).

## Quick Execution
```bash
PYTHONPATH=python/src python3 -m settlementiq.cli
PYTHONPATH=python/src pytest python/tests -v
```
