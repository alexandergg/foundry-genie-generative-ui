"use client";

import { useEffect } from "react";
import { useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { datasetFromArgs, visualSpecFromArgs, type AddVisualArgs, type CacheDatasetArgs } from "./dashboard-tools";
import { putDataset } from "@/components/generative-ui/dataset-store";
import {
  addVisual,
  removeVisual,
  changeVisualType,
  reorderVisuals,
  clearDashboard,
} from "@/components/generative-ui/dashboard-store";
import { Column, VISUAL_TYPES, ALL_VISUAL_TYPES, DatasetRow, DatasetProvenance, type DerivableVisualType } from "@/components/generative-ui/dataset-types";

// addVisual may add the executive summary; changeVisualType only retargets derivable charts.
const addVisualType = z.enum(ALL_VISUAL_TYPES);
const derivableVisualType = z.enum(VISUAL_TYPES);

function Chip({ text }: { text: string }) {
  return <div className="chat-visual-sent">{text}</div>;
}

// The agent emits these as resolved tool calls (tool_call + ToolMessage), so
// CopilotKit RENDERS them — it does not execute a handler. Each bridge applies
// its store side-effect on render. Mutations replace/no-op by id, so repeated
// renders are idempotent.

function CacheDatasetBridge({ args }: { args: CacheDatasetArgs }) {
  useEffect(() => {
    if (args?.id && Array.isArray(args.rows)) putDataset(datasetFromArgs(args));
  }, [args]);
  return <Chip text={`Cached ${args?.rows?.length ?? 0} rows`} />;
}

function AddVisualBridge({ args }: { args: AddVisualArgs }) {
  useEffect(() => {
    if (args?.datasetId && args?.type) addVisual(visualSpecFromArgs(args));
  }, [args]);
  return <Chip text={`Added ${args?.type ?? "visual"}`} />;
}

function RemoveVisualBridge({ id }: { id: string }) {
  useEffect(() => {
    if (id) removeVisual(id);
  }, [id]);
  return <Chip text="Removed visual" />;
}

function ChangeTypeBridge({ id, type }: { id: string; type: DerivableVisualType }) {
  useEffect(() => {
    if (id && type) changeVisualType(id, type);
  }, [id, type]);
  return <Chip text={`Changed to ${type}`} />;
}

function ReorderBridge({ orderedIds }: { orderedIds: string[] }) {
  const key = orderedIds?.join(",");
  useEffect(() => {
    if (orderedIds?.length) reorderVisuals(orderedIds);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return <Chip text="Reordered" />;
}

function ClearBridge() {
  useEffect(() => {
    clearDashboard();
  }, []);
  return <Chip text="Cleared dashboard" />;
}

export function useDashboardTools() {
  useRenderTool({
    name: "cacheDataset",
    parameters: z.object({ id: z.string(), title: z.string(), question: z.string(), columns: z.array(Column), rows: z.array(DatasetRow), answer: z.string().optional(), traceId: z.string().optional(), provenance: DatasetProvenance.optional() }),
    render: ({ parameters }) => <CacheDatasetBridge args={parameters as CacheDatasetArgs} />,
  });
  useRenderTool({
    name: "addVisual",
    parameters: z.object({
      datasetId: z.string(),
      type: addVisualType,
      dimension: z.string().optional(),
      measure: z.union([z.string(), z.array(z.string())]).optional(),
      title: z.string(),
    }),
    render: ({ parameters }) => <AddVisualBridge args={parameters as AddVisualArgs} />,
  });
  useRenderTool({
    name: "removeVisual",
    parameters: z.object({ id: z.string() }),
    render: ({ parameters }) => <RemoveVisualBridge id={parameters?.id ?? ""} />,
  });
  useRenderTool({
    name: "changeVisualType",
    parameters: z.object({ id: z.string(), type: derivableVisualType }),
    render: ({ parameters }) => <ChangeTypeBridge id={parameters?.id ?? ""} type={parameters?.type as DerivableVisualType} />,
  });
  useRenderTool({
    name: "reorderVisuals",
    parameters: z.object({ orderedIds: z.array(z.string()) }),
    render: ({ parameters }) => <ReorderBridge orderedIds={parameters?.orderedIds ?? []} />,
  });
  useRenderTool({
    name: "clearDashboard",
    parameters: z.object({}),
    render: () => <ClearBridge />,
  });
}
