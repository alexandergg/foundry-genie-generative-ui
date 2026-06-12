"use client";

import { CopilotChat, useConfigureSuggestions } from "@copilotkit/react-core/v2";
import { riskCatalogDefinitions } from "@/catalog/definitions";

// Spectrum nav targets: NEXT_PUBLIC_* values are inlined at build time, so set
// them when building for a deployed environment; localhost works out of the box.
const SPECTRUM_URLS = {
  controlled: process.env.NEXT_PUBLIC_SPECTRUM_URL_CONTROLLED ?? "http://localhost:3000",
  declarative: process.env.NEXT_PUBLIC_SPECTRUM_URL_DECLARATIVE ?? "http://localhost:3001",
  openEnded: process.env.NEXT_PUBLIC_SPECTRUM_URL_OPEN_ENDED ?? "http://localhost:3002",
};

const starterSuggestions = [
  { title: "Executive report (fixed)", message: "Give me the executive risk report for 2026-Q2" },
  { title: "Compact brief (fixed)", message: "Show the compact risk brief for 2026-Q1 instead" },
  { title: "Your layout (dynamic)", message: "Compose a risk dashboard your way — pick the catalog components you think fit best" },
];

const catalogPieces = Object.keys(riskCatalogDefinitions);

function AssemblyMark() {
  return (
    <span className="assembly-mark" aria-hidden="true">
      <i />
      <i />
      <i />
      <i />
    </span>
  );
}

function SpectrumNav() {
  return (
    <nav className="spectrum-nav" aria-label="Generative UI spectrum demos">
      <a href={SPECTRUM_URLS.controlled}>
        <b>01</b> Controlled
      </a>
      <a href={SPECTRUM_URLS.declarative} aria-current="page" className="current">
        <b>02</b> Declarative
      </a>
      <a href={SPECTRUM_URLS.openEnded}>
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
          <AssemblyMark />
          <div>
            <p className="eyebrow">Generative UI spectrum · Band 02</p>
            <h1>
              The <em>composition</em> workshop
            </h1>
          </div>
        </div>
        <SpectrumNav />
      </header>

      <div className="workspace">
        <aside className="rail">
          <section className="rail-card reveal" style={{ animationDelay: ".08s" }} aria-label="Component catalog">
            <p className="rail-kicker">The catalog · the only vocabulary</p>
            <div className="piece-wall">
              {catalogPieces.map((piece, index) => (
                <span className="piece" key={piece} style={{ animationDelay: `${0.15 + index * 0.04}s` }}>
                  {piece}
                </span>
              ))}
            </div>
            <p className="rail-note">
              Defined once in <code>definitions.ts</code>, shipped to the agent as its contract.
            </p>
          </section>

          <section className="rail-card reveal" style={{ animationDelay: ".16s" }} aria-label="Schema modes">
            <p className="rail-kicker">One catalog · two schemas</p>
            <div className="mode-card">
              <div className="mode-head">
                <span className="mode-dot fixed" />
                <strong>Fixed</strong>
                <span className="mode-tag">deterministic</span>
              </div>
              <p>Pre-authored layouts, reviewed in PR. Only the data changes — works with no model at all.</p>
            </div>
            <div className="mode-card">
              <div className="mode-head">
                <span className="mode-dot dynamic" />
                <strong>Dynamic</strong>
                <span className="mode-tag">LLM-composed</span>
              </div>
              <p>The agent assembles the layout itself, streamed piece by piece — same vocabulary, new composition.</p>
            </div>
          </section>

          <footer className="rail-pills reveal" style={{ animationDelay: ".24s" }} aria-label="Stack">
            <span>AG-UI</span>
            <span>A2UI v0.9</span>
            <span>risk-catalog</span>
          </footer>
        </aside>

        <section className="chat-panel reveal" style={{ animationDelay: ".12s" }} aria-label="Declarative report copilot">
          <CopilotChat
            labels={{
              chatInputPlaceholder: "Ask for the executive report, the brief, or a freeform composition…",
              chatDisclaimerText: " ",
            }}
          />
        </section>
      </div>
    </main>
  );
}
