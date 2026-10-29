# SettlementIQ — Troubleshooting & Diagnostic Guide

- **Missing CSV files**: Run `PYTHONPATH=python/src python3 -m settlementiq.cli` to generate all synthetic inputs.
- **LibreOffice headless profile**: Pass `HOME=/tmp -env:UserInstallation=file:///tmp/lo_profile`.
- **Foreign currency rows**: Check `quarantine_records` for the 8 quarantined `USD`/`EUR` records.
