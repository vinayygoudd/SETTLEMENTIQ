# SettlementIQ — System & Data Architecture

## 1. Component Architecture Diagram

```mermaid
flowchart TD
    subgraph Gen["1. Synthetic Data Generator (Python Seed=42)"]
        M["merchants.csv (25)"]
        T["transactions.csv (9,955)"]
        S["settlements.csv (10,090)"]
        B["bank_entries.csv (10,070)"]
        R["refunds.csv (250)"]
        GT["ground_truth.csv (10,000 Isolated)"]
    end

    subgraph Val["2. Staging, Validation & Quarantine Layer"]
        STG["raw_staging.stg_* Tables"]
        QUAR["raw_staging.quarantine_records (45 Rows)"]
        DEDUP["Idempotent Replay Suppression (50 Rows)"]
    end

    subgraph DB["3. Authoritative Relational Database (PostgreSQL / SQLite)"]
        VAL_T["validated.transactions (9,885)"]
        VAL_S["validated.settlements (10,065)"]
        VAL_B["validated.bank_entries (10,070)"]
        VAL_R["validated.refunds (250)"]
        REC_E["SQL Reconciliation Engine (Rules R1–R9)"]
        REC_M["reconciliation_matches (10,000 Cases)"]
        EXC["exceptions (800) & exception_history (945)"]
    end

    subgraph BI["4. Downstream Analytics, BI & QA Verification"]
        EVAL["Python Ground-Truth Evaluator (100.00% Match)"]
        XLS["Excel 15-Sheet Workbook & 8 VBA Modules"]
        PBI["Power BI Star Schema, DAX & Visual Views"]
        PPT["16-Slide Executive Presentation (.pptx)"]
    end

    M & T & S & B & R --> STG
    STG --> QUAR
    STG --> DEDUP
    DEDUP --> VAL_T & VAL_S & VAL_B & VAL_R
    VAL_T & VAL_S & VAL_B & VAL_R & QUAR --> REC_E
    REC_E --> REC_M --> EXC
    REC_M & EXC & GT --> EVAL
    REC_M & EXC --> XLS & PBI & PPT
```

## 2. Authoritative Data Ownership & Ground-Truth Isolation
- **PostgreSQL / Relational SQL** owns all reconciliation classifications, matching evidence, exception aging, and KPI source views.
- **Python** orchestrates ingestion, pre-load schema/monetary validation, database execution, and post-run evaluation against `ground_truth.csv`. Python never overrides SQL matching results.
- **Ground-Truth Isolation**: `data/ground_truth/ground_truth.csv` is never loaded into the reconciliation engine tables and is never referenced by `reconciliation_runner.py` or `05_reconciliation.sql`.
