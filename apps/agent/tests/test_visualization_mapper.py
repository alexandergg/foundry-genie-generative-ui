from __future__ import annotations

from src.visualization_mapper import (
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


def test_build_dataset_calls_emit_table_for_numeric_only_dimension() -> None:
    # All columns numeric (ranked result) → no categorical dimension, so _pick_keys
    # returns no label_key. The rows must still be shown as a table; charts are skipped.
    answer = """
| rank | total_exposure_eur |
| ---: | ---: |
| 1 | 1000 |
| 2 | 2000 |
"""
    calls = build_dataset_calls("Show ranked exposure", answer)
    types = [call.args.get("type") for call in calls if call.name == "addVisual"]
    assert "insightTable" in types
    assert "barChartCard" not in types
    assert "donutChartCard" not in types
    assert "lineAreaChartCard" not in types


def test_build_dataset_calls_without_table_keeps_narrative_card() -> None:
    calls = build_dataset_calls("Explain the demo", "No governed table is required.", trace_id="risk-xyz")
    names = [call.name for call in calls]
    assert names == ["cacheDataset", "addVisual", "followUpQuestions"]
    cache = calls[0]
    assert cache.args["rows"] == []
    assert cache.args["answer"] == "No governed table is required."
    assert calls[1].args["type"] == "riskNarrativeCard"


def test_build_dataset_calls_emit_follow_up_questions() -> None:
    # The followups.suggested status event is only honest if a followUpQuestions
    # component is actually emitted; cover both the table and narrative-only paths.
    for question, answer in [
        ("compare exposure and claims by broker", _DATASET_ANSWER),
        ("Explain the demo", "No governed table is required."),
    ]:
        follow = next(call for call in build_dataset_calls(question, answer) if call.name == "followUpQuestions")
        assert follow.args["title"] == "Continue the analysis"
        assert 1 <= len(follow.args["questions"]) <= 4
        assert all(isinstance(q, str) and q for q in follow.args["questions"])


def test_build_dataset_returns_none_without_rows() -> None:
    assert build_dataset("hello", "no table here") is None


def test_build_dataset_attaches_governed_provenance() -> None:
    dataset = build_dataset(
        "exposure by country",
        _DATASET_ANSWER,
        trace_id="risk-abc",
        source="Risk Exposure Warehouse",
    )
    assert dataset is not None
    provenance = dataset["provenance"]
    assert provenance["source"] == "Risk Exposure Warehouse"
    assert provenance["rowCount"] == 2
    assert provenance["traceId"] == "risk-abc"
    assert provenance["generatedAt"].endswith("Z")
    assert provenance["warnings"] == []


def test_build_dataset_defaults_provenance_source() -> None:
    dataset = build_dataset("exposure by country", _DATASET_ANSWER)
    assert dataset is not None
    assert dataset["provenance"]["source"] == "Azure AI Foundry + Databricks Genie"


def test_build_dataset_calls_narrative_only_warns_no_rows() -> None:
    calls = build_dataset_calls("Explain the demo", "No governed table is required.", trace_id="risk-xyz")
    provenance = calls[0].args["provenance"]
    assert provenance["rowCount"] == 0
    assert provenance["warnings"][0]["code"] == "no_structured_rows"


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
