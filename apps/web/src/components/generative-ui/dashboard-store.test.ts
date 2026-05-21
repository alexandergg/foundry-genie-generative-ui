import { beforeEach, describe, expect, it } from "vitest";
import {
  resetDashboardStore,
  getDashboardSnapshot,
  addVisual,
  removeVisual,
  changeVisualType,
  reorderVisuals,
  clearDashboard,
  removeVisualsForDataset,
} from "./dashboard-store";
import type { VisualSpec } from "./dataset-types";

function v(over: Partial<VisualSpec>): VisualSpec {
  return { id: "v1", datasetId: "a", type: "barChartCard", dimension: "country", measure: "exposure", title: "T", order: 0, ...over };
}

describe("dashboard-store mutations", () => {
  beforeEach(() => resetDashboardStore());

  it("addVisual appends and sets phase ready", () => {
    addVisual(v({ id: "v1" }));
    const s = getDashboardSnapshot();
    expect(s.phase).toBe("ready");
    expect(s.visuals.map((x) => x.id)).toEqual(["v1"]);
  });

  it("addVisual replaces by id", () => {
    addVisual(v({ id: "v1", title: "A" }));
    addVisual(v({ id: "v1", title: "B" }));
    expect(getDashboardSnapshot().visuals).toHaveLength(1);
    expect(getDashboardSnapshot().visuals[0].title).toBe("B");
  });

  it("removeVisual drops by id", () => {
    addVisual(v({ id: "v1", order: 0 }));
    addVisual(v({ id: "v2", order: 1 }));
    removeVisual("v1");
    expect(getDashboardSnapshot().visuals.map((x) => x.id)).toEqual(["v2"]);
  });

  it("changeVisualType retypes in place", () => {
    addVisual(v({ id: "v1", type: "barChartCard" }));
    changeVisualType("v1", "donutChartCard");
    expect(getDashboardSnapshot().visuals[0].type).toBe("donutChartCard");
  });

  it("reorderVisuals applies given order", () => {
    addVisual(v({ id: "v1", order: 0 }));
    addVisual(v({ id: "v2", order: 1 }));
    reorderVisuals(["v2", "v1"]);
    expect(getDashboardSnapshot().visuals.map((x) => x.id)).toEqual(["v2", "v1"]);
  });

  it("removeVisualsForDataset prunes dependents", () => {
    addVisual(v({ id: "v1", datasetId: "a", order: 0 }));
    addVisual(v({ id: "v2", datasetId: "b", order: 1 }));
    removeVisualsForDataset("a");
    expect(getDashboardSnapshot().visuals.map((x) => x.id)).toEqual(["v2"]);
  });

  it("clearDashboard empties and idles", () => {
    addVisual(v({ id: "v1" }));
    clearDashboard();
    expect(getDashboardSnapshot()).toMatchObject({ phase: "idle", visuals: [] });
  });
});
