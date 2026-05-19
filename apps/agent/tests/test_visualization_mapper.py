from __future__ import annotations

from src.visualization_mapper import build_component_calls, extract_bullet_metrics, extract_markdown_table


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
    assert "followUpQuestions" in names
