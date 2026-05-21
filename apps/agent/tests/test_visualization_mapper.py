from __future__ import annotations

from src.visualization_mapper import (
    build_component_calls,
    build_dataset,
    build_dataset_calls,
    extract_bullet_metrics,
    extract_markdown_table,
)

_DATASET_ANSWER = """
| Country | Exposure |
| --- | --- |
| ES | 100 |
| FR | 200 |
"""


def test_build_dataset_extracts_columns_and_rows() -> None:
    dataset = build_dataset("exposure by country", _DATASET_ANSWER, trace_id="risk-abc")
    assert dataset is not None
    assert dataset["id"] == "ds-risk-abc"
    roles = {column["key"]: column["role"] for column in dataset["columns"]}
    assert roles["Country"] == "dimension"
    assert roles["Exposure"] == "measure"
    assert len(dataset["rows"]) == 2


def test_build_dataset_carries_narrative_answer() -> None:
    dataset = build_dataset("exposure by country", _DATASET_ANSWER, trace_id="risk-abc")
    assert dataset is not None
    assert "| ES | 100 |" in dataset["answer"]


def test_build_dataset_calls_emit_cache_then_addvisual() -> None:
    calls = build_dataset_calls("exposure by country", _DATASET_ANSWER, trace_id="risk-abc")
    names = [call.name for call in calls]
    assert names[0] == "cacheDataset"
    assert "addVisual" in names
    add = next(call for call in calls if call.name == "addVisual")
    assert add.args["datasetId"] == "ds-risk-abc"


def test_build_dataset_calls_emit_executive_summary_first() -> None:
    calls = build_dataset_calls("exposure by country", _DATASET_ANSWER, trace_id="risk-abc")
    # cacheDataset, then the executive-summary narrative pinned to the top.
    assert calls[0].name == "cacheDataset"
    assert calls[1].name == "addVisual"
    assert calls[1].args == {
        "datasetId": "ds-risk-abc",
        "type": "riskNarrativeCard",
        "title": "Executive summary",
    }


def test_build_dataset_calls_without_table_keeps_narrative_card() -> None:
    calls = build_dataset_calls("Explain the demo", "No governed table is required.", trace_id="risk-xyz")
    names = [call.name for call in calls]
    assert names == ["cacheDataset", "addVisual"]
    cache = calls[0]
    assert cache.args["rows"] == []
    assert cache.args["answer"] == "No governed table is required."
    assert calls[1].args["type"] == "riskNarrativeCard"


def test_build_dataset_returns_none_without_rows() -> None:
    assert build_dataset("hello", "no table here") is None


def test_extract_markdown_table_parses_currency_and_european_numbers() -> None:
    text = """
| country | total_exposure_eur | loss_ratio |
| --- | ---: | ---: |
| Spain | €1,250,000 | 12.5 |
| France | 1.234,56 | 8,25 |
"""

    headers, rows = extract_markdown_table(text)

    assert headers == ["country", "total_exposure_eur", "loss_ratio"]
    assert rows == [
        {"country": "Spain", "total_exposure_eur": 1_250_000.0, "loss_ratio": 12.5},
        {"country": "France", "total_exposure_eur": 1234.56, "loss_ratio": 8.25},
    ]


def test_extract_bullet_metrics_uses_question_metric() -> None:
    headers, rows = extract_bullet_metrics("- Broker A: €10,000\n- Broker B: €7,500", "claims by broker")

    assert headers == ["label", "total_claim_amount_eur"]
    assert rows == [
        {"label": "Broker A", "total_claim_amount_eur": 10_000.0},
        {"label": "Broker B", "total_claim_amount_eur": 7_500.0},
    ]


def test_build_component_calls_adds_controlled_visualizations() -> None:
    answer = """
| broker | total_exposure_eur | total_claim_amount_eur |
| --- | ---: | ---: |
| Broker A | 1000 | 100 |
| Broker B | 2000 | 150 |
"""

    calls = build_component_calls("compare exposure and claims by broker", answer, "Risk Exposure Warehouse")
    names = [call.name for call in calls]

    assert names[:2] == ["plan_visualization", "riskNarrativeCard"]
    assert "insightTable" in names
    assert "kpiStrip" in names
    assert "metricComparisonChartCard" in names
    assert "policyBreachCard" in names
    assert "followUpQuestions" in names


def test_build_component_calls_without_rows_keeps_safe_narrative_only() -> None:
    calls = build_component_calls("Explain the demo", "No governed table is required for this explanation.")
    names = [call.name for call in calls]

    assert names == ["plan_visualization", "riskNarrativeCard", "followUpQuestions"]


def test_build_component_calls_limits_table_and_chart_rows() -> None:
    rows = "\n".join(f"| Broker {index} | {index * 1000} |" for index in range(1, 16))
    answer = f"""
| broker | total_exposure_eur |
| --- | ---: |
{rows}
"""

    calls = build_component_calls("Show exposure by broker", answer)
    table = next(call for call in calls if call.name == "insightTable")
    bar = next(call for call in calls if call.name == "barChartCard")
    donut = next(call for call in calls if call.name == "donutChartCard")

    assert len(table.args["rows"]) == 12
    assert len(bar.args["data"]) == 10
    assert len(donut.args["data"]) == 8


def test_build_component_calls_handles_numeric_first_column_without_charts() -> None:
    answer = """
| rank | total_exposure_eur |
| ---: | ---: |
| 1 | 1000 |
| 2 | 2000 |
"""

    calls = build_component_calls("Show ranked exposure", answer)
    names = [call.name for call in calls]

    assert "insightTable" in names
    assert "kpiStrip" not in names
    assert "barChartCard" not in names


def test_build_component_calls_adds_visual_provenance() -> None:
    answer = """
| broker | total_exposure_eur |
| --- | ---: |
| Broker A | 1000 |
| Broker B | 2000 |
"""

    calls = build_component_calls(
        "Show exposure by broker",
        answer,
        "Risk Warehouse",
        approval_request_id="abc123",
        trace_id="trace-1",
    )
    table = next(call for call in calls if call.name == "insightTable")
    policy = next(call for call in calls if call.name == "policyBreachCard")
    provenance = table.args["provenance"]

    assert policy.args["metricLabel"] == "Total Exposure Eur"
    assert policy.args["metricValue"] == 2000.0
    assert provenance["visualId"] == "insightTable-2"
    assert provenance["source"] == "Risk Warehouse"
    assert provenance["approvalRequestId"] == "abc123"
    assert provenance["traceId"] == "trace-1"
    assert provenance["rowCount"] == 2
    assert provenance["warnings"] == []


def test_build_component_calls_warns_when_no_structured_rows() -> None:
    calls = build_component_calls("Explain risk", "No table was returned.")
    narrative = next(call for call in calls if call.name == "riskNarrativeCard")

    assert narrative.args["provenance"]["rowCount"] == 0
    assert narrative.args["provenance"]["warnings"] == [
        {"code": "no_structured_rows", "message": "No structured rows were detected; narrative only."}
    ]
