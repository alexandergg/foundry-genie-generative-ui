# Deploying the full spectrum to Azure

How to take the three demos from localhost to Azure: one **Foundry Hosted Agent per band** plus one **App Service per band** (all webs share a single App Service plan). Everything below is scaffolded in the repo — this page is the order of operations.

Prerequisites: the cloud foundation from [azure-setup.md](azure-setup.md) (resource group, Foundry project + model deployment, ACR, Key Vault, monitoring) and `az login` with contributor rights.

## 1. Build and create the hosted agents

Every agent ships the same packaging as the deployed Genie agent: `hosted_main.py` (Invocations protocol), `Dockerfile`, and `agent.yaml`. Build an immutable image per band:

```bash
source .risk.env.local
./scripts/build-hosted-agent-image.sh apps/declarative/agent
./scripts/build-hosted-agent-image.sh apps/open-ended/agent
# Rebuild the Genie agent too if you want the spotlight/presentation tools in production:
./scripts/build-hosted-agent-image.sh apps/controlled/agent
```

Then create (or version) each hosted agent in the Foundry project, mirroring its `agent.yaml`, with the image reference each build prints. Hosted agents are a preview feature, so the SDK client needs `allow_preview=True`:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(endpoint="<project-endpoint>", credential=DefaultAzureCredential(), allow_preview=True)
client.agents.create_version(
    agent_name="risk-declarative-a2ui-hosted",
    definition={
        "kind": "hosted",
        "container_protocol_versions": [{"protocol": "invocations", "version": "1.0.0"}],
        "image": "<acr-login-server>/risk-declarative-a2ui-hosted:<tag>",
        "cpu": "0.5",
        "memory": "1Gi",
        "environment_variables": {
            "RISK_MODEL_ENDPOINT": "https://<resource>.services.ai.azure.com/openai/v1",
            "RISK_MODEL_DEPLOYMENT": "<deployment-name>",
        },
    },
)
```

- `RISK_MODEL_ENDPOINT` — the OpenAI-compatible endpoint of your Foundry resource. The `RISK_*` names exist because **`FOUNDRY_*` is a reserved prefix inside hosted-agent containers** (see `src/config.py` in each agent for the fallback order).
- `RISK_MODEL_DEPLOYMENT` — your model deployment name (a strong model is recommended for the open-ended band).

**RBAC — the part that bites:** every hosted agent gets its own **instance identity** (`client.agents.get(...).as_dict()["instance_identity"]["principal_id"]`) and that is the principal that calls the model — not the project identity. Grant each one `Cognitive Services OpenAI User` on the Foundry account:

```bash
az role assignment create --assignee-object-id <instance-principal-id> \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" --scope <foundry-account-resource-id>
```

Propagation takes a few minutes, and **sessions are isolated per calling identity** (`isolation_key_source: Entra`): a session container started before the grant keeps its stale 401 until it recycles, so test through the identity that will actually call (the web app), not just your own. Wait for the version to report `status: active`, then poll the invocations endpoint until the first session warms up (`session_not_ready` simply means the container is still starting — or crashed; check the agent's logs in the Foundry portal if it never readies).

The invocations endpoint per agent is deterministic: `https://<resource>.services.ai.azure.com/api/projects/<project>/agents/<agent-name>/endpoint/protocols/invocations?api-version=2025-11-15-preview`.

## 2. Provision the frontends

Edit `infra/main.demo.bicepparam` — enable the bands you want and paste the invocations endpoints:

```bicep
param deployControlledFrontend = true
param deployDeclarativeFrontend = true
param deployOpenEndedFrontend = true
param controlledFrontendAgentUrl = 'https://<controlled-invocations-endpoint>'
param declarativeFrontendAgentUrl = 'https://<declarative-invocations-endpoint>'
param openEndedFrontendAgentUrl = 'https://<open-ended-invocations-endpoint>'
```

```bash
source .risk.env.local
./scripts/deploy-infra.sh
```

All deployed webs share one App Service plan (`B1` by default — three apps, one plan's cost). Each web app gets a system-assigned identity with `Cognitive Services User` on the Foundry account, and app settings `AG_UI_AGENT_URL` / `AG_UI_AGENT_AUTH=azure-identity` wired to its agent. Note the three URL outputs: `controlledFrontendUrl`, `declarativeFrontendUrl`, `openEndedFrontendUrl`.

## 3. Build the webs with the spectrum URLs and deploy

The spectrum nav (the `01 Controlled · 02 Declarative · 03 Open-Ended` buttons) reads `NEXT_PUBLIC_SPECTRUM_URL_*` at **build time** — that is why the infra comes first. Build each web with the three deployed URLs exported, then ship the standalone bundle:

```bash
export NEXT_PUBLIC_SPECTRUM_URL_CONTROLLED="https://<controlledFrontendUrl-host>"
export NEXT_PUBLIC_SPECTRUM_URL_DECLARATIVE="https://<declarativeFrontendUrl-host>"
export NEXT_PUBLIC_SPECTRUM_URL_OPEN_ENDED="https://<openEndedFrontendUrl-host>"

deploy_web () { # usage: deploy_web <band> <webAppName>
  local band="$1" app_name="$2" stage="/tmp/risk-frontend-$1"
  npm run "build:${band}-web"
  rm -rf "$stage" "/tmp/risk-frontend-$band.zip"
  mkdir -p "$stage/apps/$band/web/.next"
  cp -R "apps/$band/web/.next/standalone/." "$stage/"
  cp -R "apps/$band/web/.next/static" "$stage/apps/$band/web/.next/static"
  if [ -d "apps/$band/web/public" ]; then cp -R "apps/$band/web/public" "$stage/apps/$band/web/public"; fi
  (cd "$stage" && zip -qr "/tmp/risk-frontend-$band.zip" .)
  az webapp deploy --resource-group "$RESOURCE_GROUP" --name "$app_name" --src-path "/tmp/risk-frontend-$band.zip" --type zip
}

deploy_web controlled  "<controlledFrontendWebAppName>"
deploy_web declarative "<declarativeFrontendWebAppName>"
deploy_web open-ended  "<openEndedFrontendWebAppName>"
```

Each App Service's startup command (`node apps/<band>/web/server.js`) is set by Bicep to match the standalone layout.

**Zip-deploy gotchas on B1 (field-tested):**

- `az webapp deploy` exit codes are unreliable — it can print `ERROR ... 503/502` (or exit 0 on a failed deployment). The source of truth is Kudu: poll `https://<app>.scm.azurewebsites.net/api/deployments/latest` until `status: 4` (success) — `3` is failed, `1` is still extracting. A dropped client connection mid-deploy does NOT cancel the server-side extraction.
- An app whose startup command points at content that is not deployed yet crash-loops and can drag Kudu down (503 on the deploy itself). For a first deploy, `az webapp stop` the site, push the zip, **wait for `status: 4`**, then `az webapp start`. Do not start the site while the zip is still extracting — that kills the deployment.

## 4. Verify

- Open each frontend URL; the spectrum nav should jump between the three deployed apps.
- Controlled: run a governed question end to end (warehouse running), then `Spotlight the bar chart` — this confirms the rebuilt Genie hosted image.
- Declarative: the fixed beats work even if the model RBAC is still propagating (deterministic fallback); the `freeform` beat confirms model access from the hosted container.
- Open-ended: the sandboxed widget confirms model access; the Excalidraw beat additionally needs outbound internet from the App Service running the **web** (the MCP middleware executes inside the Next.js API route).

## Notes

- **Cost**: one B1 plan + three small web apps + hosted agent containers. Stop what you do not need between sessions (`scripts/stop-compute.sh` covers Databricks; hosted agents bill while deployed).
- **Local stays untouched**: with no `NEXT_PUBLIC_SPECTRUM_URL_*` set, the nav falls back to `localhost:3000/3001/3002`, and the agents keep reading `FOUNDRY_MODEL_*`/`RISK_MODEL_*` from their `.env` files.
- **One domain instead of three**: possible later with Front Door path routing + Next `basePath`, but three URLs keep the per-band apps standalone and are the recommended demo topology.
