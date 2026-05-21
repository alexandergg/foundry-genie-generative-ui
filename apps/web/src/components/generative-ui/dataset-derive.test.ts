import { describe, expect, it } from "vitest";
import { buildVisualProps, isTimeLike } from "./dataset-derive";
import type { Dataset, VisualSpec } from "./dataset-types";
import type {
  BarChartCardProps,
  DonutChartCardProps,
  InsightTableProps,
  MetricComparisonChartCardProps,
} from "./types";

const dataset: Dataset = {
  id: "a",
  title: "Exposure",
  question: "exposure by country",
  createdAt: 0,
  columns: [
    { key: "country", label: "Country", role: "dimension" },
    { key: "exposure", label: "Exposure", role: "measure", format: "currency" },
  ],
  rows: [
    { country: "ES", exposure: 10 },
    { country: "ES", exposure: 5 },
    { country: "FR", exposure: 20 },
  ],
};

function spec(over: Partial<VisualSpec>): VisualSpec {
  return { id: "v", datasetId: "a", type: "barChartCard", dimension: "country", measure: "exposure", title: "T", order: 0, ...over };
}

describe("dataset-derive", () => {
  it("bar chart groups by dimension and sums measure", () => {
    const props = buildVisualProps(dataset, spec({ type: "barChartCard" })) as BarChartCardProps;
    expect(props).toMatchObject({ xKey: "country", yKey: "exposure", title: "T" });
    expect(props.data).toEqual([
      { country: "ES", exposure: 15 },
      { country: "FR", exposure: 20 },
    ]);
  });

  it("donut maps to labelKey/valueKey", () => {
    const props = buildVisualProps(dataset, spec({ type: "donutChartCard" })) as DonutChartCardProps;
    expect(props).toMatchObject({ labelKey: "country", valueKey: "exposure" });
    expect(props.data).toHaveLength(2);
  });

  it("insightTable projects columns and rows", () => {
    const props = buildVisualProps(dataset, spec({ type: "insightTable" })) as InsightTableProps;
    expect(props.columns).toEqual(["country", "exposure"]);
    expect(props.rows).toHaveLength(3);
  });

  it("metricComparison uses multiple measures", () => {
    const ds2: Dataset = {
      ...dataset,
      columns: [...dataset.columns, { key: "claims", label: "Claims", role: "measure" }],
      rows: [
        { country: "ES", exposure: 10, claims: 1 },
        { country: "FR", exposure: 20, claims: 2 },
      ],
    };
    const props = buildVisualProps(ds2, spec({ type: "metricComparisonChartCard", measure: ["exposure", "claims"] })) as MetricComparisonChartCardProps;
    expect(props.yKeys).toEqual(["exposure", "claims"]);
  });

  it("detects time-like dimensions", () => {
    expect(isTimeLike(["2025-Q1", "2025-Q2"])).toBe(true);
    expect(isTimeLike(["ES", "FR"])).toBe(false);
  });
});
