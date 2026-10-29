# SettlementIQ — Reproducible Setup & Execution Guide

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r python/requirements.txt
cp .env.example .env
PYTHONPATH=python/src python3 -m settlementiq.cli
python3 scripts/run_tests.py
```
