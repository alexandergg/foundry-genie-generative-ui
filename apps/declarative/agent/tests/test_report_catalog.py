"""Contract tests for the fixed A2UI layouts over the custom catalog.

These invariants are what makes the declarative demo safe to run live: the
component tree is a valid A2UI v0.9 DAG over the app's catalog, inline chart /
table data is non-empty, and every data binding resolves against the surface
data model produced by `build_report_view`.
"""

from __future__ import annotations

import json
from typing import Any

from copilotkit import a2ui

from src.report_catalog import CATALOG_COMPONENTS, LAYOUTS, RISK_CATALOG_ID, build_report_operations
from src.sample_data import DEFAULT_QUARTER, LayoutId, build_report_view

Component = dict[str, Any]


def _component_index(components: list[Component]) -> dict[str, Component]:
    return {component["id"]: component for component in components}


def _child_ids(component: Component) -> list[str]:
    ids: list[str] = []
    child = component.get("child")
    if isinstance(child, str):
        ids.append(child)
    children = component.get("children")
    if isinstance(children, list):
        ids.extend(entry for entry in children if isinstance(entry, str))
    elif isinstance(children, dict) and isinstance(children.get("componentId"), str):
        ids.append(children["componentId"])
    return ids


def _resolve_absolute(data: dict[str, Any], path: str) -> Any:
    node: Any = data
    for part in (p for p in path.split("/") if p):
        assert isinstance(node, dict) and part in node, f"absolute path {path} does not resolve at {part}"
        node = node[part]
    return node


def _path_bindings(component: Component) -> list[str]:
    paths: list[str] = []
    for key, value in component.items():
        if key in {"child", "children", "id", "component"}:
            continue
        if isinstance(value, dict) and isinstance(value.get("path"), str):
            paths.append(value["path"])
    return paths


def _subtree_ids(index: dict[str, Component], root_id: str) -> set[str]:
    seen: set[str] = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(_child_ids(index[current]))
    return seen


def _components_for(layout_id: LayoutId) -> list[Component]:
    _, builder = LAYOUTS[layout_id]
    return builder(build_report_view(DEFAULT_QUARTER, layout_id))


def test_layouts_are_valid_dags_over_the_catalog() -> None:
    for layout_id, (surface_id, _) in LAYOUTS.items():
        components = _components_for(layout_id)
        ids = [component["id"] for component in components]
        assert len(ids) == len(set(ids)), f"{layout_id}: duplicate component ids"
        assert ids.count("root") == 1, f"{layout_id}: exactly one root required"

        index = _component_index(components)
        for component in components:
            assert component["component"] in CATALOG_COMPONENTS, f"{layout_id}: {component['component']} not in the catalog"
            for child_id in _child_ids(component):
                assert child_id != component["id"], f"{layout_id}: {component['id']} references itself"
                assert child_id in index, f"{layout_id}: missing child {child_id}"

        assert _subtree_ids(index, "root") == set(ids), f"{layout_id}: unreachable components"
        assert surface_id.startswith("risk-report-")


def test_inline_chart_and_table_data_is_baked_and_non_empty() -> None:
    executive = _component_index(_components_for("executive"))
    assert executive["bar-chart"]["data"], "executive bar chart needs inline data"
    assert all(set(point) >= {"label", "value"} for point in executive["bar-chart"]["data"])
    assert executive["detail-table"]["rows"], "executive table needs inline rows"
    assert {col["key"] for col in executive["detail-table"]["columns"]} == set(executive["detail-table"]["rows"][0])
    assert executive["kpi-metric-0"]["value"].startswith("€")

    brief = _component_index(_components_for("brief"))
    assert brief["pie-chart"]["data"], "brief pie chart needs inline data"


def test_every_data_binding_resolves_against_the_data_model() -> None:
    for layout_id in LAYOUTS:
        view = build_report_view(DEFAULT_QUARTER, layout_id)
        components = _components_for(layout_id)
        index = _component_index(components)
        template_member_ids: set[str] = set()
        for component in components:
            children = component.get("children")
            if isinstance(children, dict):
                items = _resolve_absolute(view.data_model, children["path"])
                assert isinstance(items, list) and items, f"{layout_id}: template path {children['path']} must be a non-empty list"
                for member_id in _subtree_ids(index, children["componentId"]):
                    template_member_ids.add(member_id)
                    for relative in _path_bindings(index[member_id]):
                        assert not relative.startswith("/"), f"{layout_id}: template binding {relative} must be relative"
                        assert relative in items[0], f"{layout_id}: template key {relative} missing from {children['path']} items"
        for component in components:
            if component["id"] in template_member_ids:
                continue
            for absolute in _path_bindings(component):
                assert absolute.startswith("/"), f"{layout_id}: non-template binding {absolute} must be absolute"
                assert isinstance(_resolve_absolute(view.data_model, absolute), str)


def test_build_report_operations_sequence_round_trips() -> None:
    layout_id: LayoutId = "executive"
    view = build_report_view(DEFAULT_QUARTER, layout_id)
    operations = build_report_operations(layout_id, view)

    assert [next(key for key in op if key != "version") for op in operations] == ["createSurface", "updateComponents", "updateDataModel"]
    assert operations[0]["createSurface"] == {"surfaceId": "risk-report-executive", "catalogId": RISK_CATALOG_ID}

    rendered = json.loads(a2ui.render(operations))
    assert rendered["a2ui_operations"] == operations
