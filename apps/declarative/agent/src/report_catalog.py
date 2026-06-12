"""Pre-authored A2UI layouts over the app's custom component catalog.

The frontend registers a custom catalog (`copilotkit://risk-catalog` — Metric,
BarChart, PieChart, DashboardCard, DataTable, Badge…) and these builders
compose the FIXED schemas against it: the structure is authored ahead of time,
and per render only the data changes. Chart/metric/table data is baked inline
at build time (those props take literal arrays per the catalog contract),
while titles and the ranked list stay path-bound to the surface data model —
the two data-delivery styles A2UI supports.

Conventions enforced by tests:
- exactly one component has id "root";
- ids are unique and every component is reachable from "root";
- only catalog components are used;
- components inside a repeating List template use RELATIVE data paths
  ("name"), everything else uses absolute paths ("/report/title").
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from copilotkit import a2ui

from .sample_data import LayoutId, ReportView

RENDER_TOOL_NAME = "renderRiskReport"

RISK_CATALOG_ID = "copilotkit://risk-catalog"

SURFACE_EXECUTIVE = "risk-report-executive"
SURFACE_BRIEF = "risk-report-brief"

# Custom catalog component names this demo is allowed to use (must stay in
# sync with apps/declarative-web/src/catalog/definitions.ts; tests assert the
# layouts never leave it).
CATALOG_COMPONENTS: frozenset[str] = frozenset(
    {
        "Title",
        "Text",
        "Divider",
        "Card",
        "List",
        "Row",
        "Column",
        "DashboardCard",
        "Metric",
        "PieChart",
        "BarChart",
        "Badge",
        "DataTable",
        "Button",
    }
)

Component = dict[str, Any]


def _kpi_cards(view: ReportView) -> list[Component]:
    components: list[Component] = []
    for index, kpi in enumerate(view.kpis):
        components.append({"id": f"kpi-card-{index}", "component": "Card", "child": f"kpi-metric-{index}"})
        components.append(
            {
                "id": f"kpi-metric-{index}",
                "component": "Metric",
                "label": kpi["label"],
                "value": kpi["value"],
                "trend": kpi["trend"],
                "trendValue": kpi["trendValue"],
            }
        )
    return components


def executive_components(view: ReportView) -> list[Component]:
    return [
        {
            "id": "root",
            "component": "Column",
            "gap": 14,
            "children": ["title", "subtitle", "kpi-row", "chart-card", "top-card", "table-card", "footnote"],
        },
        {"id": "title", "component": "Text", "variant": "h2", "text": {"path": "/report/title"}},
        {"id": "subtitle", "component": "Text", "variant": "caption", "text": {"path": "/report/subtitle"}},
        {"id": "kpi-row", "component": "Row", "gap": 12, "children": [f"kpi-card-{index}" for index in range(len(view.kpis))]},
        *_kpi_cards(view),
        {
            "id": "chart-card",
            "component": "DashboardCard",
            "title": "Exposure by country",
            "subtitle": f"M EUR · {view.quarter}",
            "child": "bar-chart",
        },
        {"id": "bar-chart", "component": "BarChart", "data": view.bar_data, "color": "#5b46ff"},
        {"id": "top-card", "component": "DashboardCard", "title": "Top exposures", "child": "top-list"},
        # The ranked list stays PATH-BOUND: a List template repeated over the
        # surface data model — the fixed-schema data-streaming teaching point.
        {"id": "top-list", "component": "List", "gap": 6, "children": {"componentId": "top-row", "path": "/report/topExposures"}},
        {"id": "top-row", "component": "Row", "justify": "spaceBetween", "children": ["top-name", "top-amount"]},
        {"id": "top-name", "component": "Text", "variant": "body", "text": {"path": "name"}},
        {"id": "top-amount", "component": "Text", "variant": "h3", "text": {"path": "amount"}},
        {"id": "table-card", "component": "DashboardCard", "title": "Country detail", "child": "detail-table"},
        {"id": "detail-table", "component": "DataTable", "columns": view.table_columns, "rows": view.table_rows},
        {"id": "footnote", "component": "Text", "variant": "caption", "text": {"path": "/report/footnote"}},
    ]


def brief_components(view: ReportView) -> list[Component]:
    return [
        {"id": "root", "component": "Column", "gap": 12, "children": ["title", "kpi-row", "pie-card", "top-card", "footnote"]},
        {"id": "title", "component": "Text", "variant": "h3", "text": {"path": "/report/title"}},
        {"id": "kpi-row", "component": "Row", "gap": 12, "children": [f"kpi-metric-{index}" for index in range(len(view.kpis))]},
        *[
            {
                "id": f"kpi-metric-{index}",
                "component": "Metric",
                "label": kpi["label"],
                "value": kpi["value"],
                "trend": kpi["trend"],
                "trendValue": kpi["trendValue"],
            }
            for index, kpi in enumerate(view.kpis)
        ],
        {"id": "pie-card", "component": "DashboardCard", "title": "Exposure share by country", "child": "pie-chart"},
        {"id": "pie-chart", "component": "PieChart", "data": view.pie_data},
        {"id": "top-card", "component": "DashboardCard", "title": "Top exposures", "child": "top-list"},
        {"id": "top-list", "component": "List", "gap": 6, "children": {"componentId": "top-row", "path": "/report/topExposures"}},
        {"id": "top-row", "component": "Row", "justify": "spaceBetween", "children": ["top-name", "top-amount"]},
        {"id": "top-name", "component": "Text", "variant": "body", "text": {"path": "name"}},
        {"id": "top-amount", "component": "Text", "variant": "h3", "text": {"path": "amount"}},
        {"id": "footnote", "component": "Text", "variant": "caption", "text": {"path": "/report/footnote"}},
    ]


LAYOUTS: dict[LayoutId, tuple[str, Callable[[ReportView], list[Component]]]] = {
    "executive": (SURFACE_EXECUTIVE, executive_components),
    "brief": (SURFACE_BRIEF, brief_components),
}


def build_report_operations(layout_id: LayoutId, view: ReportView) -> list[dict[str, Any]]:
    """Assemble the A2UI operation sequence for a pre-authored layout + view."""
    surface_id, builder = LAYOUTS[layout_id]
    return [
        a2ui.create_surface(surface_id, catalog_id=RISK_CATALOG_ID),
        a2ui.update_components(surface_id, builder(view)),
        a2ui.update_data_model(surface_id, view.data_model),
    ]
