# SettlementIQ — Known Limitations & Honest Verification Disclosure

1. **100% Synthetic Data (`Seed=42`)**: Perfect `100.00%` classification on synthetic data verifies deterministic rule implementation, not production accuracy on unstructured bank narratives.
2. **Single-Currency INR Policy**: Foreign currency records (`4 USD`, `4 EUR`) are quarantined at staging rather than converted via live FX rates.
3. **Desktop Application Availability**: Native Desktop Microsoft Excel VBA runtime (`.xlsm` binary compilation) and Windows Power BI Desktop (`PBIDesktop.exe` `.pbix` binary compilation) are not installed in the Linux container; all VBA `.bas` modules, Power Query M scripts, DAX measures, and LibreOffice-recalculated `.xlsx` workbooks are delivered and verified.
