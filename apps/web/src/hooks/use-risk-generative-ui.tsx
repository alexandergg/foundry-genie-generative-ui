"use client";

import { useComponent, useDefaultRenderTool, useRenderTool } from "@copilotkit/react-core/v2";
import {
  BarChartCardProps,
  DonutChartCardProps,
  FollowUpQuestionsProps,
  InsightTableProps,
  KpiStripProps,
  LineAreaChartCardProps,
  McpApprovalCardProps,
  MetricComparisonChartCardProps,
  RiskNarrativeCardProps,
  VisualizationPlanProps,
  WarehouseStatusCardProps,
} from "@/components/generative-ui/types";
import { FollowUpQuestions } from "@/components/generative-ui/follow-up-questions";
import { McpApprovalCard } from "@/components/generative-ui/mcp-approval-card";
import { DashboardPlanBridge, DashboardToolStatusBridge, DashboardVisualBridge } from "@/components/generative-ui/dashboard-stage";

export function useRiskGenerativeUI() {
  useComponent({
    name: "kpiStrip",
    description: "Executive KPI strip for Risk Exposure metrics.",
    parameters: KpiStripProps,
    render: (props) => <DashboardVisualBridge visual={{ id: "kpi-strip", type: "kpiStrip", props }} />,
  });
  useComponent({
    name: "barChartCard",
    description: "Bar chart for ranked Risk Exposure analytics results.",
    parameters: BarChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `bar-${props.title}`, type: "barChartCard", props }} />,
  });
  useComponent({
    name: "lineAreaChartCard",
    description: "Line and area trend chart for temporal Risk Exposure analytics.",
    parameters: LineAreaChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `line-area-${props.title}`, type: "lineAreaChartCard", props }} />,
  });
  useComponent({
    name: "donutChartCard",
    description: "Donut chart for metric share across Risk Exposure segments.",
    parameters: DonutChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `donut-${props.title}`, type: "donutChartCard", props }} />,
  });
  useComponent({
    name: "metricComparisonChartCard",
    description: "Grouped bar chart comparing multiple Risk Exposure metrics.",
    parameters: MetricComparisonChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `metric-comparison-${props.title}`, type: "metricComparisonChartCard", props }} />,
  });
  useComponent({
    name: "insightTable",
    description: "Table with real Databricks Genie results.",
    parameters: InsightTableProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `table-${props.title}`, type: "insightTable", props }} />,
  });
  useComponent({
    name: "riskNarrativeCard",
    description: "Executive narrative for the risk insight.",
    parameters: RiskNarrativeCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `narrative-${props.title}`, type: "riskNarrativeCard", props }} />,
  });
  useComponent({
    name: "warehouseStatusCard",
    description: "Warehouse availability warning.",
    parameters: WarehouseStatusCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: "warehouse-status", type: "warehouseStatusCard", props }} />,
  });
  useComponent({ name: "mcpApprovalCard", description: "Human approval gate before querying governed Genie data.", parameters: McpApprovalCardProps, render: McpApprovalCard });
  useComponent({ name: "followUpQuestions", description: "Suggested follow-up questions for Risk Exposure drill-down analysis.", parameters: FollowUpQuestionsProps, render: FollowUpQuestions });

  useRenderTool({
    name: "plan_visualization",
    parameters: VisualizationPlanProps,
    render: ({ parameters }) => (
      <DashboardPlanBridge
        plan={{
          approach: parameters.approach ?? "Analyze the question and query Genie.",
          technology: parameters.technology ?? "Azure AI Foundry + Databricks Genie + AG-UI",
          key_elements: parameters.key_elements ?? [],
        }}
      />
    ),
  });

  useDefaultRenderTool({
    render: ({ name, status }) => <DashboardToolStatusBridge name={name} status={status} />,
  });
}
