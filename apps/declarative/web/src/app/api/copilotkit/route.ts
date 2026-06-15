import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { buildAgentHeaders, normalizeAgentUrl } from "@/lib/agent-url";

// Declarative band, both schemas (course L4):
// - FIXED: the agent's ToolNode returns pre-authored `a2ui_operations`; the
//   middleware detects them by content and renders the surface.
// - DYNAMIC: `injectA2UITool: true` injects a `render_a2ui` tool the agent can
//   bind, composing layouts from the client-registered catalog (its component
//   schemas travel as context from CopilotKitProvider).
export const POST = async (req: NextRequest) => {
  const agentUrl = normalizeAgentUrl(process.env.AG_UI_AGENT_URL);

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    endpoint: "/api/copilotkit",
    serviceAdapter: new ExperimentalEmptyAdapter(),
    runtime: new CopilotRuntime({
      agents: { default: new HttpAgent({ url: agentUrl, headers: await buildAgentHeaders() }) },
      a2ui: { injectA2UITool: true },
    }),
  });

  return handleRequest(req);
};
