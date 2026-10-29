"""Configuration Management for SettlementIQ.

Provides deterministic settings, tolerance rules, SLA business-day windows,
rule precedence, and environment-safe database connection settings.
"""
from dataclasses import dataclass, field
from decimal import Decimal
import os
import pathlib
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class SettlementIQConfig:
    """Authoritative configuration for SettlementIQ."""

    # Core Reproducibility & Scale
    random_seed: int = int(os.environ.get("SETTLEMENTIQ_RANDOM_SEED", "42"))
    default_txn_count: int = int(os.environ.get("SETTLEMENTIQ_DEFAULT_TXN_COUNT", "10000"))
    dataset_version: str = "v1.0.0-SYNTHETIC-10K"
    ground_truth_version: str = "v1.0.0-GT-28SCENARIOS"
    rule_version: str = "RULE_SET_2026_10_v1"
    run_id: str = "RUN_20261025_001"
    reporting_date: str = os.environ.get("SETTLEMENTIQ_REPORTING_DATE", "2026-10-25")

    # Financial Control & Accounting Parameters
    approved_currency: str = "INR"
    tolerance_inr: Decimal = Decimal(os.environ.get("SETTLEMENTIQ_TOLERANCE_INR", "1.00"))
    sla_business_days: int = int(os.environ.get("SETTLEMENTIQ_SLA_BUSINESS_DAYS", "2"))
    gst_rate: Decimal = Decimal("0.1800")

    # Explicit Deterministic Rule Precedence Order
    rule_precedence: List[str] = field(default_factory=lambda: [
        "DQ_VALIDATION",    # Pre-matching data quality validation & quarantine
        "R6_DUPLICATE",     # Duplicate settlement / duplicate bank / manual review candidate detection
        "R8_AMBIGUOUS",     # Multi-candidate collision detection (never pick arbitrarily)
        "R9_REFUND",        # Refund mismatch / unreversed refund / missing refund evidence
        "R5_PARTIAL",       # Legitimate multi-part settlement & partial settlement shortfall
        "R7_MISSING",       # Missing settlement, missing ledger, or missing bank counterpart
        "R4_TIMING",        # Business-day window exception (late settlement / bank timing difference)
        "R3_FEE_ADJUSTED",  # Documented MDR + GST + gateway adjustment match
        "R1_EXACT",         # Exact net amount, currency, identifier, and SLA window match
        "R2_TOLERANCE",     # Minor rounding variance within +/- ₹1.00 (INR only)
    ])

    # Exception Aging Bands (Elapsed Calendar Days)
    aging_bands: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        "0-2 Days": (0, 2),
        "3-7 Days": (3, 7),
        "8-30 Days": (8, 30),
        "Over 30 Days": (31, 99999),
    })

    # PostgreSQL Connection Parameters (Never hardcode secrets)
    pg_host: str = os.environ.get("SETTLEMENTIQ_PG_HOST", "localhost")
    pg_port: int = int(os.environ.get("SETTLEMENTIQ_PG_PORT", "5432"))
    pg_db: str = os.environ.get("SETTLEMENTIQ_PG_DB", "settlementiq")
    pg_user: str = os.environ.get("SETTLEMENTIQ_PG_USER", "settlementiq_role")
    pg_password: str = os.environ.get("SETTLEMENTIQ_PG_PASSWORD", "")

    @property
    def project_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[3]

    @property
    def sqlite_path(self) -> pathlib.Path:
        rel = os.environ.get("SETTLEMENTIQ_SQLITE_PATH", "data/processed/settlementiq_authoritative.sqlite")
        return self.project_root / rel


DEFAULT_CONFIG = SettlementIQConfig()
