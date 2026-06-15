// The component catalog RENDERERS — platform-specific implementations (React)
// for the definitions in definitions.ts, styled with this demo's palette.
// Ported from the course's L4 demonstration catalog and type-checked against
// the Zod definitions. `createCatalog` assembles definitions + renderers under
// the catalog id the agent references in `createSurface`.

import React from "react";
import {
  PieChart as RechartsPie,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart as RechartsBar,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { createCatalog, type CatalogRenderers } from "@copilotkit/a2ui-renderer";
import { riskCatalogDefinitions, type RiskCatalogDefinitions } from "./definitions";

export const RISK_CATALOG_ID = "copilotkit://risk-catalog";

const INK = "#1f1e1a";
const MUTED = "#57534b";
const BORDER = "rgba(31, 30, 26, 0.10)";
const CHART_COLORS = ["#5b46ff", "#19a974", "#ff3621", "#b87521", "#2b8fd6", "#8a72ff"];

function resolveText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object" && "path" in value) return String((value as { path: string }).path);
  return String(value ?? "");
}

type ChildItem = string | { id: string; basePath?: string };

function renderChildItems(
  items: unknown,
  children: (id: string, basePath?: string) => React.ReactNode,
  wrap?: (node: React.ReactNode, key: string) => React.ReactNode,
): React.ReactNode[] {
  if (!Array.isArray(items)) return [];
  return (items as ChildItem[]).flatMap((item, i) => {
    if (typeof item === "string") {
      const node = children(item);
      return [wrap ? wrap(node, `${item}-${i}`) : <React.Fragment key={`${item}-${i}`}>{node}</React.Fragment>];
    }
    if (item && typeof item === "object" && "id" in item) {
      const node = children(item.id, item.basePath);
      return [wrap ? wrap(node, `${item.id}-${i}`) : <React.Fragment key={`${item.id}-${i}`}>{node}</React.Fragment>];
    }
    return [];
  });
}

const riskCatalogRenderers: CatalogRenderers<RiskCatalogDefinitions> = {
  Title: ({ props }) => {
    const Tag = (props.level === "h1" ? "h1" : props.level === "h3" ? "h3" : "h2") as "h1" | "h2" | "h3";
    const sizes: Record<string, string> = { h1: "1.6rem", h2: "1.2rem", h3: "1rem" };
    return (
      <Tag style={{ margin: 0, fontWeight: 690, fontSize: sizes[props.level ?? "h2"], color: INK, letterSpacing: "-0.03em" }}>
        {resolveText(props.text)}
      </Tag>
    );
  },

  Text: ({ props }) => {
    const styles: Record<string, React.CSSProperties> = {
      h1: { fontSize: "1.5rem", fontWeight: 700, color: INK, letterSpacing: "-0.02em" },
      h2: { fontSize: "1.25rem", fontWeight: 700, color: INK, letterSpacing: "-0.02em" },
      h3: { fontSize: "1rem", fontWeight: 650, color: "#37352f" },
      body: { fontSize: "0.875rem", color: "#37352f" },
      caption: { fontSize: "0.75rem", color: MUTED },
    };
    return <span style={styles[props.variant ?? "body"]}>{resolveText(props.text)}</span>;
  },

  Divider: () => <hr style={{ border: "none", borderTop: `1px solid ${BORDER}`, margin: "4px 0", width: "100%" }} />,

  Card: ({ props, children }) => (
    <div
      style={{
        background: "#fff",
        borderRadius: 16,
        border: `1px solid ${BORDER}`,
        padding: 16,
        boxShadow: "0 8px 22px rgba(31, 30, 26, 0.05)",
      }}
    >
      {typeof props.child === "string" && children(props.child)}
    </div>
  ),

  List: ({ props, children }) => {
    const isHorizontal = props.direction === "horizontal";
    return (
      <div
        style={{
          display: "flex",
          flexDirection: isHorizontal ? "row" : "column",
          gap: props.gap ?? 8,
          overflowX: isHorizontal ? "auto" : undefined,
          width: "100%",
        }}
      >
        {renderChildItems(props.children, children as (id: string, basePath?: string) => React.ReactNode, (node, key) =>
          isHorizontal ? (
            <div key={key} style={{ flex: "0 0 auto", minWidth: 240 }}>
              {node}
            </div>
          ) : (
            <React.Fragment key={key}>{node}</React.Fragment>
          ),
        )}
      </div>
    );
  },

  Row: ({ props, children }) => {
    const justifyMap: Record<string, string> = {
      start: "flex-start",
      center: "center",
      end: "flex-end",
      spaceBetween: "space-between",
    };
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          gap: `${props.gap ?? 14}px`,
          alignItems: props.align ?? "stretch",
          justifyContent: justifyMap[props.justify ?? "start"] ?? "flex-start",
          flexWrap: "wrap",
          width: "100%",
        }}
      >
        {renderChildItems(props.children, children as (id: string, basePath?: string) => React.ReactNode, (node, key) => (
          <div key={key} style={{ flex: "1 1 0", minWidth: 0 }}>
            {node}
          </div>
        ))}
      </div>
    );
  },

  Column: ({ props, children }) => (
    <div style={{ display: "flex", flexDirection: "column", gap: `${props.gap ?? 12}px`, width: "100%" }}>
      {renderChildItems(props.children, children as (id: string, basePath?: string) => React.ReactNode)}
    </div>
  ),

  DashboardCard: ({ props, children }) => (
    <div
      style={{
        background: "#fff",
        borderRadius: 16,
        border: `1px solid ${BORDER}`,
        padding: 18,
        boxShadow: "0 8px 22px rgba(31, 30, 26, 0.05)",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        height: "100%",
      }}
    >
      <div>
        <div style={{ fontWeight: 650, fontSize: "0.9rem", color: INK, letterSpacing: "-0.015em" }}>{resolveText(props.title)}</div>
        {props.subtitle && <div style={{ fontSize: "0.72rem", color: MUTED, marginTop: 2 }}>{resolveText(props.subtitle)}</div>}
      </div>
      {typeof props.child === "string" && children(props.child)}
    </div>
  ),

  Metric: ({ props }) => {
    const trendColors: Record<string, string> = { up: "#16895f", down: "#c84646", neutral: MUTED };
    const trendIcons: Record<string, string> = { up: "↑", down: "↓", neutral: "→" };
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontSize: "0.72rem", color: MUTED, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {resolveText(props.label)}
        </span>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{ fontSize: "1.45rem", fontWeight: 700, color: INK, letterSpacing: "-0.02em" }}>{resolveText(props.value)}</span>
          {props.trend && props.trendValue && (
            <span style={{ fontSize: "0.78rem", fontWeight: 600, color: trendColors[props.trend] ?? MUTED }}>
              {trendIcons[props.trend]} {resolveText(props.trendValue)}
            </span>
          )}
        </div>
      </div>
    );
  },

  PieChart: ({ props }) => {
    const data = props.data ?? [];
    return (
      <div style={{ width: "100%", height: 200 }}>
        <ResponsiveContainer>
          <RechartsPie>
            <Pie data={data} dataKey="value" nameKey="label" cx="50%" cy="50%" innerRadius={props.innerRadius ?? 42} outerRadius={80} paddingAngle={2}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color ?? CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </RechartsPie>
        </ResponsiveContainer>
      </div>
    );
  },

  BarChart: ({ props }) => (
    <div style={{ width: "100%", height: 200 }}>
      <ResponsiveContainer>
        <RechartsBar data={props.data ?? []}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(31,30,26,.08)" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: MUTED }} />
          <YAxis tick={{ fontSize: 11, fill: MUTED }} />
          <Tooltip />
          <Bar dataKey="value" fill={props.color ?? "#5b46ff"} radius={[4, 4, 0, 0]} />
        </RechartsBar>
      </ResponsiveContainer>
    </div>
  ),

  Badge: ({ props }) => {
    const variants: Record<string, { bg: string; color: string }> = {
      success: { bg: "rgba(25,169,116,.12)", color: "#16895f" },
      warning: { bg: "rgba(184,117,33,.12)", color: "#b87521" },
      error: { bg: "rgba(200,70,70,.12)", color: "#c84646" },
      info: { bg: "rgba(91,70,255,.10)", color: "#5b46ff" },
      neutral: { bg: "#f2efe8", color: "#4b4842" },
    };
    const v = variants[props.variant ?? "neutral"] ?? variants.neutral;
    return (
      <span
        style={{
          display: "inline-block",
          padding: "2px 9px",
          borderRadius: 999,
          fontSize: "0.7rem",
          fontWeight: 600,
          background: v.bg,
          color: v.color,
        }}
      >
        {resolveText(props.text)}
      </span>
    );
  },

  DataTable: ({ props }) => {
    const cols = props.columns ?? [];
    const rows = props.rows ?? [];
    return (
      <div style={{ overflowX: "auto", width: "100%", border: `1px solid ${BORDER}`, borderRadius: 13 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", background: "#fff" }}>
          <thead>
            <tr>
              {cols.map((col) => (
                <th
                  key={col.key}
                  style={{
                    textAlign: "left",
                    padding: "9px 12px",
                    borderBottom: `1px solid ${BORDER}`,
                    background: "#fbfaf7",
                    color: MUTED,
                    fontWeight: 650,
                    fontSize: "0.68rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} style={{ borderBottom: i === rows.length - 1 ? "none" : `1px solid ${BORDER}` }}>
                {cols.map((col) => (
                  <td key={col.key} style={{ padding: "9px 12px", color: "#37352f" }}>
                    {String((row as Record<string, unknown>)[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  },

  Button: ({ props, children, dispatch }) => {
    const variants: Record<string, React.CSSProperties> = {
      primary: { background: "#191817", color: "#fff", border: "none" },
      secondary: { background: "#fbfaf7", color: "#37352f", border: `1px solid ${BORDER}` },
      ghost: { background: "transparent", color: "#5b46ff", border: "none" },
    };
    const style = variants[props.variant ?? "primary"] ?? variants.primary;
    return (
      <button
        style={{ ...style, padding: "9px 14px", borderRadius: 999, fontSize: "0.8rem", fontWeight: 650, cursor: "pointer" }}
        onClick={() => dispatch?.(props.action ?? null)}
      >
        {typeof props.child === "string" ? children(props.child) : (props.label ?? null)}
      </button>
    );
  },
};

export const riskCatalog = createCatalog(riskCatalogDefinitions, riskCatalogRenderers, {
  catalogId: RISK_CATALOG_ID,
  includeBasicCatalog: false,
});
