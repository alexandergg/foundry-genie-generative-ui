# Band 03 · Open-Ended — sandboxed generated UI + MCP Apps

The far end of the spectrum (course L5): **no registered components, no catalog**. Two mechanisms, both enabled in the runtime route:

- **`openGenerativeUI`** — the client registers a `generateSandboxedUi` tool; the agent writes HTML/CSS/JS from scratch, rendered **live while streaming** inside a sandboxed iframe (no same-origin access; CDN libraries allowed).
- **`mcpApps`** — the runtime discovers UI tools from MCP servers (Excalidraw here), executes the agent's call against the server, and embeds the **full application** in chat.

Run the same prompt twice: the variation is the demo — and the governance caveat that keeps governed analytics in band 01.

| | |
| --- | --- |
| Web | `web/` — runtime wiring for both mechanisms (<http://localhost:3002>) |
| Agent | `agent/` — one-node graph binding every injected tool (<http://localhost:8125>) |
| Needs | A Foundry model endpoint (`RISK_MODEL_ENDPOINT`, strong model recommended) + internet to `mcp.excalidraw.com` for the whiteboard beat |

## Run

```bash
cp agent/.env.example agent/.env   # set RISK_MODEL_ENDPOINT (+ deployment)
npm run install:open-ended-agent   # once
npm run dev:open-ended-agent       # :8125
npm run dev:open-ended-web         # :3002
```

## Key files

- `web/src/app/api/copilotkit/route.ts` — the whole band is two runtime options
- `agent/src/graph.py` — binds all injected tools, streams, repairs orphan tool calls
- `agent/src/sample_data.py` — the dataset that grounds every generated view
- `agent/hosted_main.py` + `agent/Dockerfile` + `agent/agent.yaml` — Foundry Hosted Agent packaging

Try: `Build me an animated live-status widget for this energy risk portfolio — get creative` → `Draw the architecture of this demo on an Excalidraw whiteboard` → repeat the first prompt and compare.

More: [docs/generative-ui-spectrum.md](../../docs/generative-ui-spectrum.md) · session prompts in [docs/session-guide.es.md](../../docs/session-guide.es.md)
