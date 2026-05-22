from __future__ import annotations

CONTROLLED_COMPONENT_NAMES: tuple[str, ...] = (
    "riskNarrativeCard",
    "insightTable",
    "metricComparisonChartCard",
    "lineAreaChartCard",
    "donutChartCard",
    "barChartCard",
    "followUpQuestions",
    # Dashboard frontend tools (agent-invoked, handled client-side)
    "cacheDataset",
    "addVisual",
    "removeVisual",
    "changeVisualType",
    "reorderVisuals",
    "clearDashboard",
)

_CONTROLLED_COMPONENT_NAME_SET = frozenset(CONTROLLED_COMPONENT_NAMES)


def is_controlled_component_name(name: str) -> bool:
    return name in _CONTROLLED_COMPONENT_NAME_SET


def validate_component_name(name: str) -> str:
    if not is_controlled_component_name(name):
        raise ValueError(f"Unsupported controlled UI component: {name}")
    return name
