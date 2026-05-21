"use client";

import { useSyncExternalStore } from "react";
import { useAgentContext } from "@copilotkit/react-core/v2";
import { getDashboardSnapshot, subscribeDashboard } from "@/components/generative-ui/dashboard-store";
import { listSummaries, subscribeDatasets, getDatasetsSnapshot } from "@/components/generative-ui/dataset-store";
import type { VisualSpec } from "@/components/generative-ui/dataset-types";

const KIND: Record<VisualSpec["type"], string> = {
  barChartCard: "bar chart",
  lineAreaChartCard: "line/area trend chart",
  donutChartCard: "donut chart",
  metricComparisonChartCard: "grouped bar comparison chart",
  insightTable: "table",
  riskNarrativeCard: "executive summary narrative",
};

export function useDashboardReadable() {
  const dashboard = useSyncExternalStore(subscribeDashboard, getDashboardSnapshot, getDashboardSnapshot);
  useSyncExternalStore(subscribeDatasets, getDatasetsSnapshot, getDatasetsSnapshot);

  useAgentContext({
    description:
      "Current dashboard context. `datasets` lists cached query results the agent can derive new visuals from WITHOUT re-querying Genie (use these column keys for dimension/measure). `visuals` lists what is on screen now (use ids for remove/changeType). Derive from a cached dataset whenever the requested data is already present.",
    value: {
      datasets: listSummaries(),
      visuals: dashboard.visuals.map((v) => ({
        id: v.id,
        kind: KIND[v.type],
        type: v.type,
        title: v.title,
        datasetId: v.datasetId,
        dimension: v.dimension ?? null,
        measure: v.measure ?? null,
      })),
    },
  });
}
