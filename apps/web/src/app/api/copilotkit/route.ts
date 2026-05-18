import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
import { NextRequest } from "next/server";

const raw = process.env.LANGGRAPH_DEPLOYMENT_URL;
const deploymentUrl = !raw ? "http://localhost:8123" : raw.startsWith("http") ? raw : `http://${raw}`;

const defaultAgent = new LangGraphHttpAgent({ url: deploymentUrl });

export const POST = async (req: NextRequest) => {
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
