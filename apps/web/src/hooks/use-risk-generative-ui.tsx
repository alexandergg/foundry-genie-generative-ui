"use client";

import { useComponent, useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { FollowUpQuestionsProps, McpApprovalCardProps } from "@/components/generative-ui/types";
import { FollowUpQuestions } from "@/components/generative-ui/follow-up-questions";
import { McpApprovalCard } from "@/components/generative-ui/mcp-approval-card";
import { ToolChip } from "@/components/generative-ui/tool-chip";
import { GENERATIVE_UI_COMPONENTS } from "@/components/generative-ui/registry";

export function useRiskGenerativeUI() {
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.mcpApprovalCard,
    description: "Human approval gate before querying governed Genie data.",
    parameters: McpApprovalCardProps,
    render: McpApprovalCard,
  });
  useComponent({
    name: GENERATIVE_UI_COMPONENTS.followUpQuestions,
    description: "Suggested follow-up questions for Risk Exposure drill-down analysis.",
    parameters: FollowUpQuestionsProps,
    render: FollowUpQuestions,
  });

  useDefaultRenderTool({
    render: ({ name, status }) => <ToolChip name={name} status={status} />,
  });
}
