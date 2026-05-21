"use client";

import { useFrontendTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { makeDashboardToolHandlers } from "./dashboard-tools";
import { putDataset } from "@/components/generative-ui/dataset-store";
import { addVisual, removeVisual, changeVisualType, reorderVisuals, clearDashboard } from "@/components/generative-ui/dashboard-store";
import { Column, VISUAL_TYPES, DatasetRow } from "@/components/generative-ui/dataset-types";

const h = makeDashboardToolHandlers({ putDataset, addVisual, removeVisual, changeVisualType, reorderVisuals, clearDashboard });
const visualType = z.enum(VISUAL_TYPES);

export function useDashboardTools() {
  useFrontendTool({
    name: "cacheDataset",
    description: "Store a structured query result so visuals can be derived from it without re-querying. Called by the system after a governed query.",
    parameters: z.object({ id: z.string(), title: z.string(), question: z.string(), columns: z.array(Column), rows: z.array(DatasetRow) }),
    handler: h.cacheDataset,
  });
  useFrontendTool({
    name: "addVisual",
    description: "Add a chart or table derived from a cached dataset. Use dataset column keys for dimension (label/axis) and measure (value).",
    parameters: z.object({
      datasetId: z.string(),
      type: visualType,
      dimension: z.string().optional(),
      measure: z.union([z.string(), z.array(z.string())]).optional(),
      title: z.string(),
    }),
    handler: h.addVisual,
  });
  useFrontendTool({
    name: "removeVisual",
    description: "Remove a visual from the dashboard by its id.",
    parameters: z.object({ id: z.string() }),
    handler: h.removeVisual,
  });
  useFrontendTool({
    name: "changeVisualType",
    description: "Change an existing visual's chart type (same dataset, dimension and measure).",
    parameters: z.object({ id: z.string(), type: visualType }),
    handler: h.changeVisualType,
  });
  useFrontendTool({
    name: "reorderVisuals",
    description: "Reorder visuals top-to-bottom by id.",
    parameters: z.object({ orderedIds: z.array(z.string()) }),
    handler: h.reorderVisuals,
  });
  useFrontendTool({
    name: "clearDashboard",
    description: "Remove all visuals from the dashboard.",
    parameters: z.object({}),
    handler: h.clearDashboard,
  });
}
