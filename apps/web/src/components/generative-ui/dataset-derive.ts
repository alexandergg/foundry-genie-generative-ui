import type { Dataset, DatasetRow, VisualSpec } from "./dataset-types";
import type {
  BarChartCardProps,
  DonutChartCardProps,
  InsightTableProps,
  LineAreaChartCardProps,
  MetricComparisonChartCardProps,
  RiskNarrativeCardProps,
  VisualProvenance,
} from "./types";

export type DerivedProps =
  | BarChartCardProps
  | DonutChartCardProps
  | InsightTableProps
  | LineAreaChartCardProps
  | MetricComparisonChartCardProps
  | RiskNarrativeCardProps;

const TIME_RE = /(\d{4}[-/](q[1-4]|\d{1,2})|^q[1-4]\b|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i;

export function isTimeLike(values: Array<string | number | null>): boolean {
  const sample = values.slice(0, 6).map((v) => String(v ?? ""));
  return sample.length > 0 && sample.every((v) => TIME_RE.test(v));
}

function num(v: string | number | null | undefined): number {
  return typeof v === "number" ? v : Number(v) || 0;
}

function groupSum(rows: DatasetRow[], dimension: string, measure: string): DatasetRow[] {
  const acc = new Map<string, number>();
  for (const row of rows) {
    const key = String(row[dimension] ?? "");
    acc.set(key, (acc.get(key) ?? 0) + num(row[measure]));
  }
  return [...acc.entries()].map(([k, v]) => ({ [dimension]: k, [measure]: v }));
}

function asMeasures(measure: VisualSpec["measure"]): string[] {
  if (!measure) return [];
  return Array.isArray(measure) ? measure : [measure];
}

// One Genie result = one governance trail; each card stamps its own visualId.
function provenanceFor(dataset: Dataset, spec: VisualSpec): VisualProvenance | undefined {
  return dataset.provenance ? { ...dataset.provenance, visualId: spec.id } : undefined;
}

export function buildVisualProps(dataset: Dataset, spec: VisualSpec): DerivedProps {
  const dim = spec.dimension ?? dataset.columns.find((c) => c.role === "dimension")?.key ?? "";
  const measures = asMeasures(spec.measure);
  const primary = measures[0] ?? dataset.columns.find((c) => c.role === "measure")?.key ?? "";
  const fmt = dataset.columns.find((c) => c.key === primary)?.format ?? "number";
  const provenance = provenanceFor(dataset, spec);

  switch (spec.type) {
    case "barChartCard":
      return { title: spec.title, data: groupSum(dataset.rows, dim, primary), xKey: dim, yKey: primary, valueFormat: fmt, provenance };
    case "donutChartCard":
      return {
        title: spec.title,
        data: groupSum(dataset.rows, dim, primary).slice(0, 8),
        labelKey: dim,
        valueKey: primary,
        valueFormat: fmt,
        provenance,
      };
    case "lineAreaChartCard":
      return {
        title: spec.title,
        data: dataset.rows.slice(0, 12),
        xKey: dim,
        yKeys: (measures.length ? measures : [primary]).slice(0, 3),
        valueFormat: fmt,
        provenance,
      };
    case "metricComparisonChartCard":
      return {
        title: spec.title,
        data: dataset.rows.slice(0, 12),
        xKey: dim,
        yKeys: (measures.length >= 2 ? measures : dataset.columns.filter((c) => c.role === "measure").map((c) => c.key)).slice(0, 3),
        valueFormat: fmt,
        provenance,
      };
    case "insightTable":
      return { title: spec.title, columns: dataset.columns.map((c) => c.key), rows: dataset.rows.slice(0, 12), provenance };
    case "riskNarrativeCard":
      return {
        title: spec.title,
        answer: dataset.answer ?? "",
        assumptions: ["Data queried through the real Foundry/Genie agent"],
        provenance,
      };
  }
}
