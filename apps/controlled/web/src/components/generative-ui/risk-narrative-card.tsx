import { MarkdownContent } from "./markdown-content";
import { ProvenanceFooter } from "./provenance-footer";
import type { RiskNarrativeCardProps } from "./types";

export function RiskNarrativeCard({ title, answer, assumptions = [], provenance }: RiskNarrativeCardProps) {
  return (
    <div className="viz-card narrative-card">
      <h3 className="viz-title">{title}</h3>
      <MarkdownContent content={answer} />
      {assumptions.length > 0 && (
        <ul className="plan-list">
          {assumptions.map((item) => <li key={item}>{item}</li>)}
        </ul>
      )}
      <ProvenanceFooter provenance={provenance} />
    </div>
  );
}
