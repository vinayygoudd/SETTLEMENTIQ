from settlementiq.config import SettlementIQConfig
from settlementiq.synthetic_data import generate_synthetic_ecosystem


def test_01_synthetic_data_volumes_and_entities(executed_context):
    raw = executed_context["raw_data"]
    assert len(raw["merchants"]) == 25
    assert len(raw["transactions"]) == 9955
    assert len(raw["settlements"]) == 10090
    assert len(raw["bank_entries"]) == 10070
    assert len(raw["refunds"]) == 250
    assert len(raw["ground_truth"]) == 10000
    assert all(r["is_synthetic"] == "TRUE" for r in raw["merchants"])


def test_02_deterministic_reproducibility_same_seed():
    cfg1 = SettlementIQConfig(random_seed=42, default_txn_count=10000)
    cfg2 = SettlementIQConfig(random_seed=42, default_txn_count=10000)
    d1 = generate_synthetic_ecosystem(cfg1)
    d2 = generate_synthetic_ecosystem(cfg2)
    assert d1["transactions"][:50] == d2["transactions"][:50]
    assert d1["settlements"][:50] == d2["settlements"][:50]
    assert d1["ground_truth"][:50] == d2["ground_truth"][:50]


def test_03_all_28_planted_scenarios_present(executed_context):
    gt = executed_context["raw_data"]["ground_truth"]
    scenarios = {r["planted_scenario"] for r in gt}
    assert len(scenarios) >= 28
    assert "S01_EXACT_TXN_STL_MATCH" in scenarios
    assert "S14_AMBIGUOUS_CANDIDATE_MATCH" in scenarios
    assert "S28_BOUNDARY_TOLERANCE_1INR" in scenarios
