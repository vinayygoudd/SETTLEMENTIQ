def test_26_ground_truth_classification_exceeds_95_pct_target(executed_context):
    gt = executed_context["kpi_bundle"]["ground_truth_summary"]
    assert gt["overall_classification_accuracy_pct"] >= 95.0
    assert gt["planted_exception_recall_pct"] >= 95.0
    assert gt["planted_exception_precision_pct"] >= 95.0
    assert gt["overall_classification_accuracy_pct"] == 100.0


def test_27_zero_clean_record_false_positives(executed_context):
    gt = executed_context["kpi_bundle"]["ground_truth_summary"]
    assert gt["clean_baseline_cases"] == 9200
    assert gt["false_positives"] == 0
    assert gt["clean_record_false_positive_rate_pct"] == 0.0
    assert gt["variance_calculation_errors"] == 0
