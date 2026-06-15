import { DefaultAzureCredential } from "@azure/identity";

const DEFAULT_LOCAL_AGENT_URL = "http://localhost:8125";
const FOUNDRY_SCOPE = "https://ai.azure.com/.default";

export function normalizeAgentUrl(rawUrl: string | undefined, fallback: string = DEFAULT_LOCAL_AGENT_URL): string {
  if (!rawUrl) {
    return fallback;
  }

  return rawUrl.startsWith("http") ? rawUrl : `http://${rawUrl}`;
}

// Same contract as the controlled app: set AG_UI_AGENT_AUTH=azure-identity
// when AG_UI_AGENT_URL points at a Foundry Hosted Agent invocations endpoint.
export async function buildAgentHeaders(): Promise<Record<string, string>> {
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
