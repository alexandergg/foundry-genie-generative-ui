"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatValue } from "./format";
import type { BarChartCardProps } from "./types";

export function BarChartCard({ title, data, xKey, yKey, valueFormat = "number" }: BarChartCardProps) {
  return (
    <div className="viz-card">
      <h3 className="viz-title">{title}</h3>
      <p className="viz-muted">Real data returned by Databricks Genie through Azure AI Foundry.</p>
      <div style={{ height: 320, marginTop: 14 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 42 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey={xKey} angle={-25} textAnchor="end" interval={0} height={70} tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={(value) => formatValue(Number(value), valueFormat)} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => formatValue(Number(value), valueFormat)} />
            <Bar dataKey={yKey} fill="url(#uc3Gradient)" radius={[8, 8, 0, 0]} />
            <defs>
              <linearGradient id="uc3Gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
