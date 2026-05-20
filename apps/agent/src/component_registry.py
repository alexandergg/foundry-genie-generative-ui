from __future__ import annotations

CONTROLLED_COMPONENT_NAMES: tuple[str, ...] = (
    "plan_visualization",
    "riskNarrativeCard",
    "warehouseStatusCard",
    "insightTable",
    "kpiStrip",
    "metricComparisonChartCard",
    "lineAreaChartCard",
    "donutChartCard",
    "barChartCard",
    "policyBreachCard",
    "mcpApprovalCard",
    "followUpQuestions",
)

_CONTROLLED_COMPONENT_NAME_SET = frozenset(CONTROLLED_COMPONENT_NAMES)


def is_controlled_component_name(name: str) -> bool:
    return name in _CONTROLLED_COMPONENT_NAME_SET


def validate_component_name(name: str) -> str:
    if not is_controlled_component_name(name):
        raise ValueError(f"Unsupported controlled UI component: {name}")
    return name
