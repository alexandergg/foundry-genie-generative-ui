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
  PolicyBreachCardProps,
  RiskNarrativeCardProps,
  VisualizationPlanProps,
  WarehouseStatusCardProps,
} from "@/components/generative-ui/types";
import { FollowUpQuestions } from "@/components/generative-ui/follow-up-questions";
import { McpApprovalCard } from "@/components/generative-ui/mcp-approval-card";
import { DashboardPlanBridge, DashboardVisualBridge } from "@/components/generative-ui/dashboard-stage";
import { ToolChip } from "@/components/generative-ui/tool-chip";
import { GENERATIVE_UI_COMPONENTS } from "@/components/generative-ui/registry";

export function useRiskGenerativeUI() {
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.kpiStrip,
    description: "Executive KPI strip for Risk Exposure metrics.",
    parameters: KpiStripProps,
    render: (props) => <DashboardVisualBridge visual={{ id: "kpi-strip", type: "kpiStrip", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.barChartCard,
    description: "Bar chart for ranked Risk Exposure analytics results.",
    parameters: BarChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `bar-${props.title}`, type: "barChartCard", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.lineAreaChartCard,
    description: "Line and area trend chart for temporal Risk Exposure analytics.",
    parameters: LineAreaChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `line-area-${props.title}`, type: "lineAreaChartCard", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.donutChartCard,
    description: "Donut chart for metric share across Risk Exposure segments.",
    parameters: DonutChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `donut-${props.title}`, type: "donutChartCard", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.metricComparisonChartCard,
    description: "Grouped bar chart comparing multiple Risk Exposure metrics.",
    parameters: MetricComparisonChartCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `metric-comparison-${props.title}`, type: "metricComparisonChartCard", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.insightTable,
    description: "Table with real Databricks Genie results.",
    parameters: InsightTableProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `table-${props.title}`, type: "insightTable", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.riskNarrativeCard,
    description: "Executive narrative for the risk insight.",
    parameters: RiskNarrativeCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `narrative-${props.title}`, type: "riskNarrativeCard", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.warehouseStatusCard,
    description: "Warehouse availability warning.",
    parameters: WarehouseStatusCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: "warehouse-status", type: "warehouseStatusCard", props }} />,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.policyBreachCard,
    description: "Executive alert card for notable Risk Exposure signals.",
    parameters: PolicyBreachCardProps,
    render: (props) => <DashboardVisualBridge visual={{ id: `policy-${props.title}`, type: "policyBreachCard", props }} />,
  });
  useComponent({ name: GENERATIVE_UI_COMPONENTS.mcpApprovalCard, description: "Human approval gate before querying governed Genie data.", parameters: McpApprovalCardProps, render: McpApprovalCard });
  useComponent({ name: GENERATIVE_UI_COMPONENTS.followUpQuestions, description: "Suggested follow-up questions for Risk Exposure drill-down analysis.", parameters: FollowUpQuestionsProps, render: FollowUpQuestions });

  useRenderTool({
    name: GENERATIVE_UI_COMPONENTS.planVisualization,
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
    render: ({ name, status }) => <ToolChip name={name} status={status} />,
  });
}
