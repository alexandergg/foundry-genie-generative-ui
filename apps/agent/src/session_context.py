from __future__ import annotations

import re
from typing import Any

from src.visualization_mapper import ComponentCall, build_component_calls, extract_markdown_table

ContextSnapshot = dict[str, Any]

_CONTEXT_HINTS = {
    "same",
    "previous",
    "last",
    "those",
    "these",
    "result",
    "results",
    "table",
    "rows",
    "chart",
    "again",
    "sort",
    "rank",
    "top",
    "bottom",
    "highest",
    "lowest",
    "mayor",
    "menor",
    "mismos",
    "misma",
    "previo",
    "anterior",
    "tabla",
    "resultados",
    "orden",
    "ordena",
    "ranking",
    "gráfica",
    "grafica",
}

_DIMENSION_WORDS = {
    "country",
    "countries",
    "broker",
    "brokers",
    "broker_segment",
    "quarter",
    "risk",
    "risk_class",
    "product",
    "product_line",
    "claim",
    "claims",
    "overdue",
    "exposure",
    "país",
    "pais",
    "países",
    "paises",
    "trimestre",
    "riesgo",
    "siniestro",
    "siniestros",
    "vencido",
    "exposición",
    "exposicion",
}

_FRESH_QUERY_WORDS = {
    "query genie",
    "consult genie",
    "ask genie",
    "consulta genie",
    "consultar genie",
    "databricks",
    "warehouse",
    "fresh",
    "new query",
    "nueva consulta",
}


def build_context_snapshot(question: str, answer: str) -> ContextSnapshot | None:
    headers, rows = extract_markdown_table(answer)
    if not headers or not rows:
        return None
    return {
        "source": "foundry_genie",
        "question": question,
        "answer": answer[:4000],
        "headers": headers,
        "rows": rows[:50],
    }


def cached_context_answer(
    question: str,
    context: ContextSnapshot | None,
    warehouse_name: str | None = None,
) -> tuple[str, list[ComponentCall]] | None:
    if not context or not context.get("headers") or not context.get("rows"):
        return None

    lowered = question.lower()
    if any(word in lowered for word in _FRESH_QUERY_WORDS):
        return None

    headers = [str(header) for header in context["headers"]]
    rows = [dict(row) for row in context["rows"]]
    if not rows:
        return None

    header_terms = {term for header in headers for term in _header_terms(header)}
    has_context_hint = any(hint in lowered for hint in _CONTEXT_HINTS)
    mentioned_header = any(term and term in lowered for term in header_terms)
    mentioned_dimensions = {word for word in _DIMENSION_WORDS if word in lowered}
    missing_dimensions = [word for word in mentioned_dimensions if not _covered_by_headers(word, headers)]

    if missing_dimensions and not has_context_hint:
        return None
    if not has_context_hint and not mentioned_header:
        return None

    numeric_key = _metric_key_for_question(lowered, headers, rows)
    label_key = _label_key(headers, rows)
    selected_rows = rows[:]
    note = "I reused the previously approved Genie result in this session, so no new Databricks Genie query was needed."

    if numeric_key:
        reverse = not any(word in lowered for word in {"lowest", "bottom", "menor", "menores", "ascending", "ascendente"})
        selected_rows = sorted(selected_rows, key=lambda row: float(row.get(numeric_key) or 0), reverse=reverse)

    n = _requested_limit(lowered) or min(8, len(selected_rows))
    selected_rows = selected_rows[:n]

    aggregate_lines = []
    if any(word in lowered for word in {"total", "sum", "suma", "aggregate", "aggregated"}):
        for key in _numeric_keys(headers, rows)[:4]:
            aggregate_lines.append(f"- **{key}**: {_format_value(sum(float(row.get(key) or 0) for row in rows), key)}")

    table = _markdown_table(headers, selected_rows)
    title = _cached_title(question, numeric_key, label_key, n)
    aggregates = "\n" + "\n".join(aggregate_lines) + "\n" if aggregate_lines else ""
    answer = f"{note}\n\n**{title}**{aggregates}\n{table}"
    calls = build_component_calls(question, answer, warehouse_name)
    return answer, calls


def _header_terms(header: str) -> set[str]:
    lowered = header.lower()
    return {lowered, lowered.replace("_", " "), lowered.replace("_", "")}


def _covered_by_headers(word: str, headers: list[str]) -> bool:
    normalized_word = word.replace("país", "pais").replace("países", "paises")
    normalized_headers = " ".join(header.lower().replace("_", " ") for header in headers)
    aliases = {
        "countries": "country",
        "brokers": "broker",
        "claims": "claim",
        "país": "country",
        "pais": "country",
        "países": "country",
        "paises": "country",
        "trimestre": "quarter",
        "riesgo": "risk",
        "siniestro": "claim",
        "siniestros": "claim",
        "vencido": "overdue",
        "exposición": "exposure",
        "exposicion": "exposure",
    }
    target = aliases.get(normalized_word, normalized_word)
    return target in normalized_headers


def _numeric_keys(headers: list[str], rows: list[dict[str, Any]]) -> list[str]:
    return [header for header in headers if any(isinstance(row.get(header), (int, float)) for row in rows)]


def _metric_key_for_question(question: str, headers: list[str], rows: list[dict[str, Any]]) -> str | None:
    numeric = _numeric_keys(headers, rows)
    if not numeric:
        return None
    aliases = {
        "claim": ["claim", "siniestro"],
        "overdue": ["overdue", "vencido"],
        "exposure": ["exposure", "expos"],
        "policy": ["policy", "polic"],
        "count": ["count", "número", "numero"],
    }
    for key in numeric:
        key_lower = key.lower()
        if key_lower in question or key_lower.replace("_", " ") in question:
            return key
        for words in aliases.values():
            if any(word in question for word in words) and any(word in key_lower for word in words):
                return key
    return numeric[0]


def _label_key(headers: list[str], rows: list[dict[str, Any]]) -> str | None:
    return next((header for header in headers if any(not isinstance(row.get(header), (int, float)) for row in rows)), None)


def _requested_limit(question: str) -> int | None:
    match = re.search(r"(?:top|bottom|primeros|primeras|últimos|ultimos|lowest|highest)\s+(\d+)", question)
    if not match:
        match = re.search(r"\b(\d+)\b", question)
    if not match:
        return None
    return max(1, min(int(match.group(1)), 12))


def _cached_title(question: str, metric_key: str | None, label_key: str | None, n: int) -> str:
    if metric_key and label_key:
        direction = "lowest" if any(word in question.lower() for word in {"lowest", "bottom", "menor", "menores"}) else "highest"
        return f"Top {n} {label_key} rows by {direction} {metric_key}"
    return f"Cached Genie result ({n} rows)"


def _markdown_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    rendered_rows = [[_format_value(row.get(header), header) for header in headers] for row in rows]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rendered_rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _format_value(value: Any, key: str) -> str:
    if isinstance(value, float):
        if "eur" in key.lower() or "amount" in key.lower() or "balance" in key.lower() or "exposure" in key.lower():
            return f"€{value:,.0f}"
        if value.is_integer():
            return f"{value:,.0f}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
