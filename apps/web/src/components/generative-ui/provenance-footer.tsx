import type { VisualProvenance } from "./types";

export function ProvenanceFooter({ provenance }: { provenance?: VisualProvenance }) {
  if (!provenance) return null;

  const generatedAt = new Date(provenance.generatedAt).toLocaleString();

  return (
    <footer className="provenance-footer" aria-label="Visualization provenance">
      <span>{provenance.source}</span>
      <span>{generatedAt}</span>
      <span>{provenance.rowCount} rows</span>
      {provenance.approvalRequestId ? <span>Approval {provenance.approvalRequestId}</span> : null}
      {provenance.traceId ? <span>Trace {provenance.traceId}</span> : null}
      {provenance.warnings.map((warning) => (
        <span className="provenance-warning" key={`${warning.code}-${warning.message}`}>{warning.message}</span>
      ))}
    </footer>
  );
}
