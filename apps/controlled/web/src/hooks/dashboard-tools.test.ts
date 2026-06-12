import { describe, expect, it } from "vitest";
import { safeDatasetFromArgs, safeVisualSpecFromArgs, visualIdFor } from "./dashboard-tools";

const validDataset = {
  id: "ds-1",
  title: "Exposure by country",
  question: "exposure by country",
  columns: [{ key: "country", label: "Country", role: "dimension" }],
  rows: [{ country: "ES", exposure: 100 }],
};

describe("safeDatasetFromArgs", () => {
  it("accepts a complete payload and stamps createdAt", () => {
    const ds = safeDatasetFromArgs(validDataset);
    expect(ds).toMatchObject({ id: "ds-1", title: "Exposure by country" });
    expect(ds?.createdAt).toEqual(expect.any(Number));
  });

  it("defaults provenance.warnings to [] when omitted — the guarantee ProvenanceFooter relies on", () => {
    const ds = safeDatasetFromArgs({
      ...validDataset,
      provenance: { source: "Warehouse", generatedAt: "2026-05-22T00:00:00Z", rowCount: 1 },
    });
    expect(ds?.provenance?.warnings).toEqual([]);
  });

  it("rejects a partial provenance object (mid-stream) instead of storing it", () => {
    expect(safeDatasetFromArgs({ ...validDataset, provenance: { source: "Warehouse" } })).toBeNull();
  });

  it("rejects payloads missing required fields or with the wrong type", () => {
    expect(safeDatasetFromArgs({ title: "t", question: "q", columns: [], rows: [] })).toBeNull();
    expect(safeDatasetFromArgs({ ...validDataset, rows: "nope" })).toBeNull();
    expect(safeDatasetFromArgs(undefined)).toBeNull();
  });

  it("accepts a dataset with no provenance (footer simply renders nothing)", () => {
    expect(safeDatasetFromArgs(validDataset)?.provenance).toBeUndefined();
  });
});

describe("safeVisualSpecFromArgs", () => {
  it("maps a valid spec to a deterministic id and a numeric order", () => {
    const spec = safeVisualSpecFromArgs({
      datasetId: "ds-1",
      type: "barChartCard",
      title: "Bar",
      dimension: "country",
      measure: "exposure",
    });
    expect(spec?.id).toBe("vis-ds-1-barChartCard-country-exposure");
    expect(spec?.order).toEqual(expect.any(Number));
  });

  it("yields a stable id and order across calls (idempotent replace)", () => {
    const a = safeVisualSpecFromArgs({ datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T" });
    const b = safeVisualSpecFromArgs({ datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T2" });
    expect(a?.id).toBe(b?.id);
    expect(a?.order).toBe(b?.order);
  });

  it("joins array measures into the id", () => {
    const spec = safeVisualSpecFromArgs({
      datasetId: "a",
      type: "metricComparisonChartCard",
      dimension: "c",
      measure: ["x", "y"],
      title: "T",
    });
    expect(spec?.id).toContain("x_y");
  });

  it("rejects an unknown visual type", () => {
    expect(safeVisualSpecFromArgs({ datasetId: "ds-1", type: "pieChart", title: "x" })).toBeNull();
  });

  it("rejects a spec missing its title", () => {
    expect(safeVisualSpecFromArgs({ datasetId: "ds-1", type: "barChartCard" })).toBeNull();
  });
});

describe("visualIdFor", () => {
  it("is deterministic for the same args regardless of title", () => {
    const args = { datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T" } as const;
    expect(visualIdFor(args)).toBe(visualIdFor({ ...args, title: "different" }));
  });
});
