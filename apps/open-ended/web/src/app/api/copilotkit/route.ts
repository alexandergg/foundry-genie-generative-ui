import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { buildAgentHeaders, normalizeAgentUrl } from "@/lib/agent-url";

// Open-ended band (course L5):
// - `openGenerativeUI: true` lets the client register a `generateSandboxedUi`
//   frontend tool — the agent generates arbitrary HTML/CSS/JS rendered in a
//   sandboxed iframe, streamed progressively.
// - `mcpApps` connects MCP App servers (Excalidraw): their UI tools are
//   appended to the agent's tool list, and the middleware executes the call
//   against the MCP server and embeds the app in chat.
export const POST = async (req: NextRequest) => {
  const agentUrl = normalizeAgentUrl(process.env.AG_UI_AGENT_URL);

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    endpoint: "/api/copilotkit",
    serviceAdapter: new ExperimentalEmptyAdapter(),
    runtime: new CopilotRuntime({
      agents: { default: new HttpAgent({ url: agentUrl, headers: await buildAgentHeaders() }) },
      openGenerativeUI: true,
      mcpApps: {
        servers: [
          {
            type: "http",
            url: "https://mcp.excalidraw.com",
            serverId: "excalidraw",
          },
        ],
      },
    }),
  });

  return handleRequest(req);
};
