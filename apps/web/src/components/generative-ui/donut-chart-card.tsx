"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { formatValue } from "./format";
import type { DonutChartCardProps } from "./types";

const colors = ["#2563eb", "#ff3621", "#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#64748b"];

export function DonutChartCard({ title, data, labelKey, valueKey, valueFormat = "number" }: DonutChartCardProps) {
  return (
    <div className="viz-card">
      <h3 className="viz-title">{title}</h3>
      <p className="viz-muted">Share of the selected metric across the returned segments.</p>
      <div className="donut-layout">
        <div style={{ height: 250, minWidth: 230 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey={valueKey} nameKey={labelKey} innerRadius={66} outerRadius={100} paddingAngle={2} stroke="rgba(255,255,255,.9)">
                {data.map((_, index) => <Cell key={`slice-${index}`} fill={colors[index % colors.length]} />)}
              </Pie>
              <Tooltip formatter={(value) => formatValue(Number(value), valueFormat)} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="donut-legend">
          {data.slice(0, 7).map((row, index) => (
            <div key={`${row[labelKey]}-${index}`} className="donut-legend-row">
              <span style={{ background: colors[index % colors.length] }} />
              <p>{String(row[labelKey])}</p>
              <strong>{formatValue(Number(row[valueKey] ?? 0), valueFormat)}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
