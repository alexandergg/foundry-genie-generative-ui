import { formatValue } from "./format";
import { ProvenanceFooter } from "./provenance-footer";
import type { KpiStripProps } from "./types";

export function KpiStrip({ items, provenance }: KpiStripProps) {
  return (
    <div className="viz-card">
      <div className="kpi-grid">
        {items.map((item, index) => (
          <div className={`kpi ${item.status ?? "stable"}`} key={`${item.label}-${index}`}>
            <div className="kpi-label">{item.label}</div>
            <div className="kpi-value">{formatValue(item.value, item.format)}</div>
            {item.delta ? <div className="kpi-delta">{item.delta}</div> : null}
          </div>
        ))}
      </div>
      <ProvenanceFooter provenance={provenance} />
    </div>
  );
}
