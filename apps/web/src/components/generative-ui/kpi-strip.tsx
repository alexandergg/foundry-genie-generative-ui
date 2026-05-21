import { formatValue } from "./format";
import { ProvenanceFooter } from "./provenance-footer";
import type { KpiStripProps } from "./types";

export function KpiStrip({ items, provenance }: KpiStripProps) {
  return (
    <div className="kpi-strip">
      <div className="kpi-grid">
        {items.map((item, index) => (
          <div className={`kpi ${item.status ?? "stable"}`} key={`${item.label}-${index}`}>
            <div className="kpi-top">
              <span className="kpi-icon" aria-hidden="true" />
              {item.delta ? <span className="kpi-delta">{item.delta}</span> : null}
            </div>
            <div className="kpi-value">{formatValue(item.value, item.format)}</div>
            <div className="kpi-label">{item.label}</div>
          </div>
        ))}
      </div>
      <ProvenanceFooter provenance={provenance} />
    </div>
  );
}
