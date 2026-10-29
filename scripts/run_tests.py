#!/usr/bin/env python3
"""Pytest-compatible Test Runner for SettlementIQ.

Executes all test functions across `python/tests/test_*.py` using the shared
`executed_context` session fixture, supporting `tmp_path` and `pytest.raises`.
"""
import contextlib
import importlib.util
import inspect
import pathlib
import re
import sys
import tempfile
import time
import traceback


class _RaisesContext:
    def __init__(self, expected_exc, match=None):
        self.expected_exc = expected_exc
        self.match = match

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        if exc_type is None:
            raise AssertionError(f"Expected {self.expected_exc.__name__} to be raised, but no exception occurred.")
        if not issubclass(exc_type, self.expected_exc):
            return False
        if self.match and not re.search(self.match, str(exc_val)):
            raise AssertionError(f"Exception '{exc_val}' did not match pattern '{self.match}'")
        return True


class _PytestShim:
    @staticmethod
    def fixture(scope="function"):
        def decorator(fn):
            fn._is_fixture = True
            return fn
        return decorator

    @staticmethod
    def raises(expected_exc, match=None):
        return _RaisesContext(expected_exc, match=match)


def run_test_suite() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    src_dir = root / "python" / "src"
    tests_dir = root / "python" / "tests"
    sys.path.insert(0, str(src_dir))
    sys.modules["pytest"] = _PytestShim()  # type: ignore

    from settlementiq.config import DEFAULT_CONFIG
    from settlementiq.ingestion import ingest_all_sources
    from settlementiq.validation import validate_and_separate_sources
    from settlementiq.data_quality import compute_data_quality_profile
    from settlementiq.database import init_and_load_database
    from settlementiq.reconciliation_runner import execute_sql_reconciliation
    from settlementiq.kpi_calculations import calculate_all_kpis_and_evaluation

    t_start = time.time()
    print("=" * 78)
    print("SettlementIQ — Automated Test Suite Execution (27 Test Assertions)")
    print("=" * 78)

    raw_data = ingest_all_sources(DEFAULT_CONFIG.project_root, DEFAULT_CONFIG)
    val_bundle = validate_and_separate_sources(raw_data, DEFAULT_CONFIG)
    dq_report = compute_data_quality_profile(raw_data, val_bundle)
    conn = init_and_load_database(raw_data, val_bundle, DEFAULT_CONFIG)
    recon_summary = execute_sql_reconciliation(conn, DEFAULT_CONFIG)
    kpi_bundle = calculate_all_kpis_and_evaluation(conn, raw_data, dq_report, DEFAULT_CONFIG)

    ctx = {
        "config": DEFAULT_CONFIG,
        "raw_data": raw_data,
        "val_bundle": val_bundle,
        "dq_report": dq_report,
        "conn": conn,
        "recon_summary": recon_summary,
        "kpi_bundle": kpi_bundle,
    }

    passed = 0
    failed = 0

    for test_file in sorted(tests_dir.glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(test_file.stem, test_file)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            t0 = time.time()
            sig = inspect.signature(obj)
            kwargs = {}
            with tempfile.TemporaryDirectory() as tmp_d:
                if "executed_context" in sig.parameters:
                    kwargs["executed_context"] = ctx
                if "tmp_path" in sig.parameters:
                    kwargs["tmp_path"] = pathlib.Path(tmp_d)
                try:
                    obj(**kwargs)
                    dt = time.time() - t0
                    print(f"PASSED  python/tests/{test_file.name}::{name} ({dt:.3f}s)")
                    passed += 1
                except Exception as exc:
                    dt = time.time() - t0
                    print(f"FAILED  python/tests/{test_file.name}::{name} ({dt:.3f}s) -> {exc}")
                    traceback.print_exc()
                    failed += 1

    conn.close()
    total_dt = time.time() - t_start
    print("-" * 78)
    print(f"Summary: {passed}/{passed + failed} tests passed, {failed} failed in {total_dt:.2f}s")
    print("=" * 78)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_test_suite())
