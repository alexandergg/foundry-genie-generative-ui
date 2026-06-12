"use client";

import { CopilotChat, useConfigureSuggestions } from "@copilotkit/react-core/v2";

// Spectrum nav targets: NEXT_PUBLIC_* values are inlined at build time, so set
// them when building for a deployed environment; localhost works out of the box.
const SPECTRUM_URLS = {
  controlled: process.env.NEXT_PUBLIC_SPECTRUM_URL_CONTROLLED ?? "http://localhost:3000",
  declarative: process.env.NEXT_PUBLIC_SPECTRUM_URL_DECLARATIVE ?? "http://localhost:3001",
  openEnded: process.env.NEXT_PUBLIC_SPECTRUM_URL_OPEN_ENDED ?? "http://localhost:3002",
};

const starterSuggestions = [
  { title: "Animated widget", message: "Build me an animated live-status widget for this energy risk portfolio — get creative" },
  { title: "Whiteboard diagram", message: "Draw the architecture of this demo (browser, CopilotKit runtime, AG-UI agent, Foundry model) on an Excalidraw whiteboard" },
];

function SparkMark() {
  return (
    <span className="spark-mark" aria-hidden="true">
      <i className="ray r1" />
      <i className="ray r2" />
      <i className="ray r3" />
      <i className="core" />
    </span>
  );
}

function SpectrumNav() {
  return (
    <nav className="spectrum-nav" aria-label="Generative UI spectrum demos">
      <a href={SPECTRUM_URLS.controlled}>
        <b>01</b> Controlled
      </a>
      <a href={SPECTRUM_URLS.declarative}>
        <b>02</b> Declarative
      </a>
      <a href={SPECTRUM_URLS.openEnded} aria-current="page" className="current">
        <b>03</b> Open-Ended
      </a>
    </nav>
  );
}

export default function HomePage() {
  useConfigureSuggestions({ suggestions: starterSuggestions, available: "before-first-message" }, []);

  return (
    <main className="shell">
      <header className="masthead reveal" style={{ animationDelay: "0s" }}>
        <div className="masthead-id">
          <SparkMark />
          <div>
            <p className="eyebrow">Generative UI spectrum · Band 03</p>
            <h1>
              The <em>unbounded</em> edge
            </h1>
          </div>
        </div>
        <SpectrumNav />
      </header>

      <div className="workspace">
        <aside className="rail">
          <section className="rail-card reveal" style={{ animationDelay: ".08s" }} aria-label="Open-ended mechanisms">
            <p className="rail-kicker">No components · no catalog</p>
            <div className="mech-card">
              <div className="mech-head">
                <span className="mech-glyph code-glyph" aria-hidden="true">
                  {"</>"}
                </span>
                <strong>Sandboxed UI</strong>
              </div>
              <p>
                The agent writes HTML/CSS/JS from scratch — streamed live into a sandboxed iframe via{" "}
                <code>generateSandboxedUi</code>.
              </p>
            </div>
            <div className="mech-card">
              <div className="mech-head">
                <span className="mech-glyph app-glyph" aria-hidden="true">
                  ▣
                </span>
                <strong>MCP Apps</strong>
              </div>
              <p>
                Full applications embedded in chat: the runtime discovers Excalidraw&apos;s tools from{" "}
                <code>mcp.excalidraw.com</code> and the agent drives the whiteboard.
              </p>
            </div>
          </section>

          <section className="rail-card caution reveal" style={{ animationDelay: ".16s" }} aria-label="Governance">
            <p className="rail-kicker">The fence is the sandbox</p>
            <p className="caution-note">
              No same-origin access, no cookies, no host DOM. Run the same prompt twice — the variation is the demo, and
              the reason governed analytics stays in band 01.
            </p>
          </section>

          <footer className="rail-pills reveal" style={{ animationDelay: ".24s" }} aria-label="Stack">
            <span>openGenerativeUI</span>
            <span>mcpApps</span>
            <span>sandboxed iframe</span>
          </footer>
        </aside>

        <section className="panel-frame reveal" style={{ animationDelay: ".12s" }}>
          <div className="chat-panel" aria-label="Open-ended generative UI copilot">
            <CopilotChat
              labels={{
                chatInputPlaceholder: "Describe any view of the energy risk portfolio…",
                chatDisclaimerText: " ",
              }}
            />
          </div>
        </section>
      </div>
    </main>
  );
}
