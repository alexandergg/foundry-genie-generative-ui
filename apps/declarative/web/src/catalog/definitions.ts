// The component catalog DEFINITIONS — the platform-agnostic contract between
// the agent and this app (course L4 pattern). Each entry declares a name, a
// description the agent reads, and a Zod schema for the props. The renderers
// in renderers.tsx implement them; `createCatalog` assembles both and the
// CopilotKitProvider ships these schemas to the agent as context.

import { z } from "zod";

export const riskCatalogDefinitions = {
  Title: {
    description: "A heading. Use for section titles and page headers.",
    props: z.object({
      text: z.string(),
      level: z.string().optional(),
    }),
  },

  Text: {
    description: "A text element. Use for labels, values, captions. `text` accepts a literal or a { path } data binding.",
    props: z.object({
      text: z.union([z.string(), z.object({ path: z.string() })]),
      variant: z.enum(["h1", "h2", "h3", "body", "caption"]).optional(),
    }),
  },

  Divider: {
    description: "A horizontal divider line.",
    props: z.object({}),
  },

  Card: {
    description: "A generic card container with a child slot.",
    props: z.object({
      child: z.string().optional(),
    }),
  },

  List: {
    description:
      "A list of children. Use an array of component ids, or a template object { componentId, path } to repeat a component per item of a data-model array.",
    props: z.object({
      children: z.union([
        z.array(z.string()),
        z.object({ componentId: z.string(), path: z.string() }),
      ]),
      direction: z.enum(["horizontal", "vertical"]).optional(),
      gap: z.number().optional(),
    }),
  },

  Row: {
    description: "Horizontal layout container.",
    props: z.object({
      gap: z.number().optional(),
      align: z.string().optional(),
      justify: z.string().optional(),
      children: z.union([
        z.array(z.string()),
        z.object({ componentId: z.string(), path: z.string() }),
      ]),
    }),
  },

  Column: {
    description: "Vertical layout container.",
    props: z.object({
      gap: z.number().optional(),
      align: z.string().optional(),
      children: z.union([
        z.array(z.string()),
        z.object({ componentId: z.string(), path: z.string() }),
      ]),
    }),
  },

  DashboardCard: {
    description:
      "A card container with title and optional subtitle. Has a 'child' slot for content (chart, metrics, table). Use 'child' with a single component ID.",
    props: z.object({
      title: z.string(),
      subtitle: z.string().optional(),
      child: z.string().optional(),
    }),
  },

  Metric: {
    description: "A key metric display with label, value, and optional trend indicator. Great for KPIs and stats.",
    props: z.object({
      label: z.string(),
      value: z.string(),
      trend: z.enum(["up", "down", "neutral"]).optional(),
      trendValue: z.string().optional(),
    }),
  },

  PieChart: {
    description: "A pie/donut chart. Provide data as an inline array of {label, value, color?} objects.",
    props: z.object({
      data: z.array(
        z.object({
          label: z.string(),
          value: z.number(),
          color: z.string().optional(),
        }),
      ),
      innerRadius: z.number().optional(),
    }),
  },

  BarChart: {
    description: "A bar chart. Provide data as an inline array of {label, value} objects.",
    props: z.object({
      data: z.array(z.object({ label: z.string(), value: z.number() })),
      color: z.string().optional(),
    }),
  },

  Badge: {
    description: "A small status badge/tag. Use for labels, statuses, categories.",
    props: z.object({
      text: z.string(),
      variant: z.enum(["success", "warning", "error", "info", "neutral"]).optional(),
    }),
  },

  DataTable: {
    description: "A data table with columns and rows.",
    props: z.object({
      columns: z.array(z.object({ key: z.string(), label: z.string() })),
      rows: z.array(z.record(z.string(), z.any())),
    }),
  },

  Button: {
    description:
      "An interactive button. Use 'label' for simple text. 'action' uses the nested event format { event: { name, context? } } and is dispatched on click.",
    props: z.object({
      label: z.string().optional(),
      child: z.string().optional(),
      variant: z.enum(["primary", "secondary", "ghost"]).optional(),
      action: z
        .union([
          z.object({
            event: z.object({
              name: z.string(),
              context: z.record(z.string(), z.any()).optional(),
            }),
          }),
          z.null(),
        ])
        .optional(),
    }),
  },
};

export type RiskCatalogDefinitions = typeof riskCatalogDefinitions;
