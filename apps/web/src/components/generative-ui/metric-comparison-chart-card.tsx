"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatValue } from "./format";
import { ProvenanceFooter } from "./provenance-footer";
import type { MetricComparisonChartCardProps } from "./types";

const colors = ["#2563eb", "#ff3621", "#06b6d4"];

export function MetricComparisonChartCard({ title, data, xKey, yKeys, valueFormat = "number", provenance }: MetricComparisonChartCardProps) {
  return (
    <div className="viz-card">
      <h3 className="viz-title">{title}</h3>
      <p className="viz-muted">Side-by-side comparison of multiple metrics returned by Genie.</p>
      <div style={{ height: 320, marginTop: 14 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 18, left: 8, bottom: 42 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey={xKey} angle={-25} textAnchor="end" interval={0} height={70} tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={(value) => formatValue(Number(value), valueFormat)} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => formatValue(Number(value), valueFormat)} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {yKeys.slice(0, 3).map((key, index) => (
              <Bar key={key} dataKey={key} fill={colors[index % colors.length]} radius={[7, 7, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ProvenanceFooter provenance={provenance} />
    </div>
  );
}
