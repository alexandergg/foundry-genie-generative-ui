import { describe, expect, it } from "vitest";
import { datasetFromArgs, visualSpecFromArgs, visualIdFor } from "./dashboard-tools";

describe("dashboard-tools builders", () => {
  it("datasetFromArgs adds createdAt", () => {
    const ds = datasetFromArgs({
      id: "a",
      title: "T",
      question: "q",
      columns: [{ key: "c", label: "C", role: "dimension" }],
      rows: [{ c: "x" }],
    });
    expect(ds).toMatchObject({ id: "a", title: "T" });
    expect(ds.createdAt).toEqual(expect.any(Number));
  });

  it("visualIdFor is deterministic for the same args", () => {
    const args = { datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T" } as const;
    expect(visualIdFor(args)).toBe(visualIdFor({ ...args, title: "different" }));
  });

  it("visualSpecFromArgs yields a stable id and order across calls (idempotent replace)", () => {
    const a = visualSpecFromArgs({ datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T" });
    const b = visualSpecFromArgs({ datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T2" });
    expect(a.id).toBe(b.id);
    expect(a.order).toBe(b.order);
  });

  it("visualSpecFromArgs joins array measures into the id", () => {
    const spec = visualSpecFromArgs({ datasetId: "a", type: "metricComparisonChartCard", dimension: "c", measure: ["x", "y"], title: "T" });
    expect(spec.id).toContain("x_y");
  });
});
