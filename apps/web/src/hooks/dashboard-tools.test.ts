import { describe, expect, it, vi } from "vitest";
import { makeDashboardToolHandlers } from "./dashboard-tools";

function deps() {
  return {
    putDataset: vi.fn(),
    addVisual: vi.fn(),
    removeVisual: vi.fn(),
    changeVisualType: vi.fn(),
    reorderVisuals: vi.fn(),
    clearDashboard: vi.fn(),
  };
}

describe("dashboard-tools handlers", () => {
  it("cacheDataset stores a normalized dataset", async () => {
    const d = deps();
    const h = makeDashboardToolHandlers(d);
    await h.cacheDataset({ id: "a", title: "T", question: "q", columns: [{ key: "c", label: "C", role: "dimension" }], rows: [{ c: "x" }] });
    expect(d.putDataset).toHaveBeenCalledTimes(1);
    expect(d.putDataset.mock.calls[0][0]).toMatchObject({ id: "a", createdAt: expect.any(Number) });
  });

  it("addVisual forwards a spec with id and order", async () => {
    const d = deps();
    await makeDashboardToolHandlers(d).addVisual({ datasetId: "a", type: "donutChartCard", dimension: "c", measure: "m", title: "T" });
    expect(d.addVisual).toHaveBeenCalledTimes(1);
    expect(d.addVisual.mock.calls[0][0]).toMatchObject({ datasetId: "a", type: "donutChartCard", id: expect.any(String), order: expect.any(Number) });
  });

  it("removeVisual / changeVisualType / reorder / clear delegate", async () => {
    const d = deps();
    const h = makeDashboardToolHandlers(d);
    await h.removeVisual({ id: "v1" });
    expect(d.removeVisual).toHaveBeenCalledWith("v1");
    await h.changeVisualType({ id: "v1", type: "barChartCard" });
    expect(d.changeVisualType).toHaveBeenCalledWith("v1", "barChartCard");
    await h.reorderVisuals({ orderedIds: ["b", "a"] });
    expect(d.reorderVisuals).toHaveBeenCalledWith(["b", "a"]);
    await h.clearDashboard();
    expect(d.clearDashboard).toHaveBeenCalledTimes(1);
  });
});
