import { ProvenanceFooter } from "./provenance-footer";
import type { PolicyBreachCardProps } from "./types";

export function PolicyBreachCard({ title, severity, summary, metricLabel, metricValue, recommendation, provenance }: PolicyBreachCardProps) {
  return (
    <div className={`viz-card policy-breach-card ${severity}`}>
      <p className="eyebrow">Executive risk signal</p>
      <h3 className="viz-title">{title}</h3>
      <p className="viz-muted">{summary}</p>
      <div className="policy-breach-metric">
        <span>{metricLabel}</span>
        <strong>{metricValue}</strong>
      </div>
      <p className="policy-recommendation">{recommendation}</p>
      <ProvenanceFooter provenance={provenance} />
    </div>
  );
}
