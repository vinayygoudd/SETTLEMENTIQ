from decimal import Decimal


def test_25_kpi_catalog_completeness_and_values(executed_context):
    kpis = {k["kpi_id"]: k for k in executed_context["kpi_bundle"]["kpi_catalog"]}
    assert len(kpis) >= 40
    assert kpis["KPI_VOL_02"]["actual_value"] == "9885"
    assert kpis["KPI_REC_01"]["actual_value"] == "93.07"
    assert kpis["KPI_EXC_01"]["actual_value"] == "705"
    assert kpis["KPI_EXC_02"]["actual_value"] == "95"
    assert kpis["KPI_EXC_03"]["actual_value"] == "25"
    assert Decimal(kpis["KPI_FIN_12"]["actual_value"]) == Decimal("3752510.63")
    assert Decimal(kpis["KPI_FIN_13"]["actual_value"]) == Decimal("126151.24")
