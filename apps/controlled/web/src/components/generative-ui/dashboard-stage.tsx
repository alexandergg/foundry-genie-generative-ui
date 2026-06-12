"use client";

import { useSyncExternalStore } from "react";
import { DatabricksGenieMark } from "../databricks-genie-mark";
import { BarChartCard } from "./bar-chart-card";
import { DonutChartCard } from "./donut-chart-card";
import { InsightTable } from "./insight-table";
import { LineAreaChartCard } from "./line-area-chart-card";
import { MetricComparisonChartCard } from "./metric-comparison-chart-card";
import { RiskNarrativeCard } from "./risk-narrative-card";
import { getDashboardSnapshot, subscribeDashboard } from "./dashboard-store";
import { getProcessSnapshot, subscribeProcess } from "./process-store";
import { getDataset, getDatasetsSnapshot, subscribeDatasets } from "./dataset-store";
import { getViewSnapshot, subscribeView } from "./view-store";
import { buildVisualProps, type DerivedProps } from "./dataset-derive";
import type { VisualSpec } from "./dataset-types";
import { StatusTimeline, formatDashboardPhase } from "./status-timeline";
import type {
  BarChartCardProps,
  DonutChartCardProps,
  InsightTableProps,
  LineAreaChartCardProps,
  MetricComparisonChartCardProps,
  RiskNarrativeCardProps,
} from "./types";

// Executive summary and tables read better across the full grid width; charts pair up 2-up.
const FULL_WIDTH: ReadonlySet<VisualSpec["type"]> = new Set(["insightTable", "riskNarrativeCard"]);

function spanClass(type: VisualSpec["type"]): string {
  return FULL_WIDTH.has(type) ? "dashboard-visual span-full" : "dashboard-visual";
}

function renderSpec(spec: VisualSpec) {
  const dataset = getDataset(spec.datasetId);
  if (!dataset) return null;
  const props: DerivedProps = buildVisualProps(dataset, spec);
  switch (spec.type) {
    case "barChartCard":
      return <BarChartCard {...(props as BarChartCardProps)} />;
    case "lineAreaChartCard":
      return <LineAreaChartCard {...(props as LineAreaChartCardProps)} />;
    case "donutChartCard":
      return <DonutChartCard {...(props as DonutChartCardProps)} />;
    case "metricComparisonChartCard":
      return <MetricComparisonChartCard {...(props as MetricComparisonChartCardProps)} />;
    case "insightTable":
      return <InsightTable {...(props as InsightTableProps)} />;
    case "riskNarrativeCard":
      return <RiskNarrativeCard {...(props as RiskNarrativeCardProps)} />;
  }
}

function SkeletonVisuals() {
  return (
    <div className="dashboard-skeletons" aria-label="Generating visualizations">
      <div className="skeleton-card skeleton-chart data-orchestration">
        <div className="query-beam" />
        <div className="skeleton-line short" />
        <div className="skeleton-bars">
          <span style={{ height: "36%" }} />
          <span style={{ height: "58%" }} />
          <span style={{ height: "82%" }} />
          <span style={{ height: "52%" }} />
          <span style={{ height: "70%" }} />
        </div>
      </div>
      <div className="skeleton-card skeleton-table">
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
      </div>
    </div>
  );
}

export function DashboardStage() {
  const state = useSyncExternalStore(subscribeDashboard, getDashboardSnapshot, getDashboardSnapshot);
  useSyncExternalStore(subscribeDatasets, getDatasetsSnapshot, getDatasetsSnapshot);
  const process = useSyncExternalStore(subscribeProcess, getProcessSnapshot, getProcessSnapshot);
  const view = useSyncExternalStore(subscribeView, getViewSnapshot, getViewSnapshot);
  const hasVisuals = state.visuals.length > 0;
  // A stale spotlight id (visual removed since) means no spotlight at all.
  const spotlightId = state.visuals.some((v) => v.id === view.spotlightVisualId) ? view.spotlightVisualId : null;

  return (
    <section className="dashboard-card" aria-label="Generative visualization panel">
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">Generative canvas</p>
          <h2>Visual insights</h2>
        </div>
        <span className={`dashboard-state ${state.phase}`}>{formatDashboardPhase(state.phase)}</span>
      </div>

      {!hasVisuals && state.phase === "idle" && (
        <div className="dashboard-placeholder">
          <div className="genie-orchestrator" aria-hidden="true">
            <span className="orbit orbit-one" />
            <span className="orbit orbit-two" />
            <span className="orbit-dot dot-one" />
            <span className="orbit-dot dot-two" />
            <DatabricksGenieMark animated />
          </div>
          <h3>Ask a question to create the dashboard</h3>
          <p>Genie will turn governed warehouse results into live KPIs, charts and executive tables.</p>
          <div className="startup-steps" aria-hidden="true">
            <span>Governed query</span>
            <span>Genie reasoning</span>
            <span>Visual canvas</span>
          </div>
        </div>
      )}

      {!hasVisuals && state.phase !== "idle" && (
        <div className="dashboard-loading">
          <StatusTimeline process={process} />
          <SkeletonVisuals />
        </div>
      )}

      {hasVisuals && (
        <div className="dashboard-grid">
          <div className="dashboard-visual span-full">
            <StatusTimeline process={process} />
          </div>
          {state.visuals.map((spec) => (
            <div
              className={`${spanClass(spec.type)}${spotlightId ? (spec.id === spotlightId ? " spotlighted" : " dimmed") : ""}`}
              key={spec.id}
            >
              {renderSpec(spec)}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
