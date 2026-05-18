"use client";

import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatValue } from "./format";
import type { LineAreaChartCardProps } from "./types";

const colors = ["#2563eb", "#ff3621", "#06b6d4"];

export function LineAreaChartCard({ title, data, xKey, yKeys, valueFormat = "number" }: LineAreaChartCardProps) {
  const [primaryKey, ...secondaryKeys] = yKeys;

  return (
    <div className="viz-card">
      <h3 className="viz-title">{title}</h3>
      <p className="viz-muted">Trend view from real Genie data, rendered as controlled AG-UI.</p>
      <div style={{ height: 300, marginTop: 14 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 18, left: 8, bottom: 28 }}>
            <defs>
              <linearGradient id="uc3AreaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity={0.28} />
                <stop offset="100%" stopColor="#2563eb" stopOpacity={0.03} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={(value) => formatValue(Number(value), valueFormat)} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => formatValue(Number(value), valueFormat)} />
            {primaryKey ? <Area type="monotone" dataKey={primaryKey} stroke={colors[0]} fill="url(#uc3AreaGradient)" strokeWidth={2.5} /> : null}
            {secondaryKeys.slice(0, 2).map((key, index) => (
              <Line key={key} type="monotone" dataKey={key} stroke={colors[index + 1]} strokeWidth={2.2} dot={{ r: 3 }} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
