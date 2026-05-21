import type { Dataset, DerivableVisualType, VisualSpec } from "@/components/generative-ui/dataset-types";

export type DashboardToolDeps = {
  putDataset: (ds: Dataset) => void;
  addVisual: (spec: VisualSpec) => void;
  removeVisual: (id: string) => void;
  changeVisualType: (id: string, type: DerivableVisualType) => void;
  reorderVisuals: (orderedIds: string[]) => void;
  clearDashboard: () => void;
};

export type CacheDatasetArgs = Omit<Dataset, "createdAt" | "traceId"> & { traceId?: string };
export type AddVisualArgs = Omit<VisualSpec, "id" | "order">;

let visualSeq = 0;

export function makeDashboardToolHandlers(deps: DashboardToolDeps) {
  return {
    cacheDataset: async (args: CacheDatasetArgs) => {
      deps.putDataset({ ...args, createdAt: Date.now() });
      return `Cached dataset ${args.id} (${args.rows.length} rows).`;
    },
    addVisual: async (args: AddVisualArgs) => {
      visualSeq += 1;
      const id = `vis-${args.datasetId}-${args.type}-${args.dimension ?? "x"}-${visualSeq}`;
      const spec: VisualSpec = { id, order: visualSeq, ...args };
      deps.addVisual(spec);
      return `Added ${args.type} "${args.title}".`;
    },
    removeVisual: async ({ id }: { id: string }) => {
      deps.removeVisual(id);
      return `Removed ${id}.`;
    },
    changeVisualType: async ({ id, type }: { id: string; type: DerivableVisualType }) => {
      deps.changeVisualType(id, type);
      return `Changed ${id} to ${type}.`;
    },
    reorderVisuals: async ({ orderedIds }: { orderedIds: string[] }) => {
      deps.reorderVisuals(orderedIds);
      return "Reordered.";
    },
    clearDashboard: async () => {
      deps.clearDashboard();
      return "Cleared dashboard.";
    },
  };
}
