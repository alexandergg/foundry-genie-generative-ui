from __future__ import annotations

from main import route_supervisor_decision
from src.foundry_agent_client import FoundryAgentClient


def test_route_dashboard_op() -> None:
    assert route_supervisor_decision({"route": "dashboard_op"}) == "dashboard_op"


def test_route_risk_data() -> None:
    assert route_supervisor_decision({"route": "risk_data"}) == "run_risk"


def test_route_default_direct() -> None:
    assert route_supervisor_decision({"route": "direct"}) == "direct_response"
    assert route_supervisor_decision({}) == "direct_response"


def test_parse_dashboard_op_decision_addvisual() -> None:
    client = FoundryAgentClient.__new__(FoundryAgentClient)
    text = '{"tool": "addVisual", "args": {"datasetId": "ds-1", "type": "donutChartCard", "dimension": "Country", "measure": "Exposure", "title": "Donut"}, "message": "Added a donut."}'
    decision = client._parse_dashboard_op_decision(text)
    assert decision.tool == "addVisual"
    assert decision.args["type"] == "donutChartCard"
    assert decision.message == "Added a donut."


def test_parse_dashboard_op_decision_unknown_tool_falls_back_to_none() -> None:
    client = FoundryAgentClient.__new__(FoundryAgentClient)
    decision = client._parse_dashboard_op_decision('{"tool": "explode", "args": {}, "message": "nope"}')
    assert decision.tool == "none"
    assert decision.message == "nope"


def test_parse_dashboard_op_decision_view_tools() -> None:
    client = FoundryAgentClient.__new__(FoundryAgentClient)
    spotlight = client._parse_dashboard_op_decision(
        '{"tool": "spotlightVisual", "args": {"id": "vis-ds-1-barChartCard-Country-Exposure"}, "message": "Spotlighted."}'
    )
    assert spotlight.tool == "spotlightVisual"
    assert spotlight.args == {"id": "vis-ds-1-barChartCard-Country-Exposure"}

    presentation = client._parse_dashboard_op_decision('{"tool": "setPresentationMode", "args": {"enabled": true}, "message": "On."}')
    assert presentation.tool == "setPresentationMode"
    assert presentation.args == {"enabled": True}
