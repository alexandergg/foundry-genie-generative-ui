"use client";

import { useComponent, useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { FollowUpQuestionsProps } from "@/components/generative-ui/types";
import { FollowUpQuestions } from "@/components/generative-ui/follow-up-questions";
import { ToolChip } from "@/components/generative-ui/tool-chip";
import { GENERATIVE_UI_COMPONENTS } from "@/components/generative-ui/registry";

export function useRiskGenerativeUI() {
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
