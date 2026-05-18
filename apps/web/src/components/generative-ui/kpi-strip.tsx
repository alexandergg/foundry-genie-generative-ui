import { formatValue } from "./format";
import type { KpiStripProps } from "./types";

export function KpiStrip({ items }: KpiStripProps) {
  return (
    <div className="viz-card">
      <div className="kpi-grid">
        {items.map((item, index) => (
          <div className="kpi" key={`${item.label}-${index}`}>
            <div className="kpi-label">{item.label}</div>
            <div className="kpi-value">{formatValue(item.value, item.format)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
