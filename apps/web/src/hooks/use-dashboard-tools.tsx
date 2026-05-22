"use client";

import { useEffect } from "react";
import { useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import {
  CacheDatasetParams,
  AddVisualParams,
  RemoveVisualParams,
  ChangeVisualTypeParams,
  ReorderVisualsParams,
  safeDatasetFromArgs,
  safeVisualSpecFromArgs,
} from "./dashboard-tools";
import { putDataset } from "@/components/generative-ui/dataset-store";
import {
  addVisual,
  removeVisual,
  changeVisualType,
  reorderVisuals,
  clearDashboard,
} from "@/components/generative-ui/dashboard-store";

function Chip({ text }: { text: string }) {
  return <div className="chat-visual-sent">{text}</div>;
}

function readString(args: unknown, key: string): string | undefined {
  const value = (args as Record<string, unknown> | null | undefined)?.[key];
  return typeof value === "string" ? value : undefined;
}

// The agent emits these as resolved tool calls (tool_call + ToolMessage), so
// CopilotKit RENDERS them — it does not execute a handler, and it does NOT parse
// the args against the schema. Each bridge therefore validates the raw args with
// its schema and only mutates the store on a full, valid parse; mid-stream or
// malformed payloads are skipped. Mutations replace/no-op by id, so repeated
// renders are idempotent.

function CacheDatasetBridge({ args }: { args: unknown }) {
  useEffect(() => {
    const dataset = safeDatasetFromArgs(args);
    if (dataset) putDataset(dataset);
  }, [args]);
  const rows = (args as { rows?: unknown })?.rows;
  return <Chip text={`Cached ${Array.isArray(rows) ? rows.length : 0} rows`} />;
}

function AddVisualBridge({ args }: { args: unknown }) {
  useEffect(() => {
    const spec = safeVisualSpecFromArgs(args);
    if (spec) addVisual(spec);
  }, [args]);
  return <Chip text={`Added ${readString(args, "type") ?? "visual"}`} />;
}

function RemoveVisualBridge({ args }: { args: unknown }) {
  useEffect(() => {
    const parsed = RemoveVisualParams.safeParse(args);
    if (parsed.success) removeVisual(parsed.data.id);
  }, [args]);
  return <Chip text="Removed visual" />;
}

function ChangeTypeBridge({ args }: { args: unknown }) {
  useEffect(() => {
    const parsed = ChangeVisualTypeParams.safeParse(args);
    if (parsed.success) changeVisualType(parsed.data.id, parsed.data.type);
  }, [args]);
  return <Chip text={`Changed to ${readString(args, "type") ?? "visual"}`} />;
}

function ReorderBridge({ args }: { args: unknown }) {
  useEffect(() => {
    const parsed = ReorderVisualsParams.safeParse(args);
    if (parsed.success && parsed.data.orderedIds.length) reorderVisuals(parsed.data.orderedIds);
  }, [args]);
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
    parameters: CacheDatasetParams,
    render: ({ parameters }) => <CacheDatasetBridge args={parameters} />,
  });
  useRenderTool({
    name: "addVisual",
    parameters: AddVisualParams,
    render: ({ parameters }) => <AddVisualBridge args={parameters} />,
  });
  useRenderTool({
    name: "removeVisual",
    parameters: RemoveVisualParams,
    render: ({ parameters }) => <RemoveVisualBridge args={parameters} />,
  });
  useRenderTool({
    name: "changeVisualType",
    parameters: ChangeVisualTypeParams,
    render: ({ parameters }) => <ChangeTypeBridge args={parameters} />,
  });
  useRenderTool({
    name: "reorderVisuals",
    parameters: ReorderVisualsParams,
    render: ({ parameters }) => <ReorderBridge args={parameters} />,
  });
  useRenderTool({
    name: "clearDashboard",
    parameters: z.object({}),
    render: () => <ClearBridge />,
  });
}
