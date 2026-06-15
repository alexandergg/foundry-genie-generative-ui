import { HttpAgent } from "@ag-ui/client";
import { DefaultAzureCredential } from "@azure/identity";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

const DEFAULT_LOCAL_AGENT_URL = "http://localhost:8123";
const FOUNDRY_SCOPE = "https://ai.azure.com/.default";

function normalizeAgentUrl(rawUrl: string | undefined): string {
  if (!rawUrl) {
    return DEFAULT_LOCAL_AGENT_URL;
  }

  return rawUrl.startsWith("http") ? rawUrl : `http://${rawUrl}`;
}

async function buildAgentHeaders(): Promise<Record<string, string>> {
  if (process.env.AG_UI_AGENT_AUTH !== "azure-identity") {
    return {};
  }

  const credential = new DefaultAzureCredential();
  const token = await credential.getToken(process.env.AG_UI_AGENT_SCOPE ?? FOUNDRY_SCOPE);
  if (!token?.token) {
    throw new Error("Unable to acquire an Azure identity token for the AG-UI agent endpoint.");
  }

  return { authorization: `Bearer ${token.token}` };
}

export const POST = async (req: NextRequest) => {
  const agentUrl = normalizeAgentUrl(process.env.AG_UI_AGENT_URL ?? process.env.LANGGRAPH_DEPLOYMENT_URL);
  const defaultAgent = new HttpAgent({ url: agentUrl, headers: await buildAgentHeaders() });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    endpoint: "/api/copilotkit",
    serviceAdapter: new ExperimentalEmptyAdapter(),
    runtime: new CopilotRuntime({
      agents: { default: defaultAgent },
      a2ui: { injectA2UITool: true },
    }),
  });

  return handleRequest(req);
};
