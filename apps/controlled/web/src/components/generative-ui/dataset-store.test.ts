import { beforeEach, describe, expect, it } from "vitest";
import { putDataset, getDataset, listSummaries, resetDatasetStore, MAX_DATASETS } from "./dataset-store";
import type { Dataset } from "./dataset-types";

function ds(id: string): Dataset {
  return {
    id,
    title: `T-${id}`,
    question: "q",
    createdAt: Date.now(),
    columns: [
      { key: "country", label: "Country", role: "dimension" },
      { key: "exposure", label: "Exposure", role: "measure", format: "currency" },
    ],
    rows: [
      { country: "ES", exposure: 10 },
      { country: "FR", exposure: 20 },
    ],
  };
}

describe("dataset-store", () => {
  beforeEach(() => resetDatasetStore());

  it("puts and gets a dataset", () => {
    putDataset(ds("a"));
    expect(getDataset("a")?.rows).toHaveLength(2);
  });

  it("listSummaries omits rows and reports rowCount", () => {
    putDataset(ds("a"));
    const [s] = listSummaries();
    expect(s).toEqual({ id: "a", title: "T-a", rowCount: 2, columns: ds("a").columns });
    expect((s as unknown as { rows?: unknown }).rows).toBeUndefined();
  });

  it("evicts the oldest beyond MAX_DATASETS", () => {
    for (let i = 0; i < MAX_DATASETS + 2; i++) putDataset(ds(String(i)));
    expect(getDataset("0")).toBeUndefined();
    expect(listSummaries()).toHaveLength(MAX_DATASETS);
  });
});
