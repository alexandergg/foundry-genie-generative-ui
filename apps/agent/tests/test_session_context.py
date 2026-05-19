from __future__ import annotations

from src.session_context import build_context_snapshot, cached_context_answer


def test_build_context_snapshot_returns_limited_table_context() -> None:
    answer = """
| country | total_exposure_eur |
| --- | ---: |
| Spain | 1000 |
| France | 2000 |
"""

    context = build_context_snapshot("show exposure by country", answer)

    assert context is not None
    assert context["source"] == "foundry_genie"
    assert context["headers"] == ["country", "total_exposure_eur"]
    assert context["rows"][0] == {"country": "Spain", "total_exposure_eur": 1000.0}


def test_cached_context_answer_reuses_previous_result_for_ranked_follow_up() -> None:
    context = {
        "source": "foundry_genie",
        "question": "show exposure by country",
        "answer": "previous answer",
        "headers": ["country", "total_exposure_eur"],
        "rows": [
            {"country": "Spain", "total_exposure_eur": 1000.0},
            {"country": "France", "total_exposure_eur": 3000.0},
            {"country": "Germany", "total_exposure_eur": 2000.0},
        ],
    }

    cached = cached_context_answer("sort the same table by highest exposure top 2", context, "Risk Exposure Warehouse")

    assert cached is not None
    answer, calls = cached
    assert "previously approved Genie result" in answer
    assert "France" in answer
    assert "Germany" in answer
    assert "Spain" not in answer
    assert any(call.name == "insightTable" for call in calls)


def test_cached_context_answer_ignores_fresh_query_requests() -> None:
    context = {"headers": ["country"], "rows": [{"country": "Spain"}]}

    assert cached_context_answer("new query in Databricks for claims", context) is None
