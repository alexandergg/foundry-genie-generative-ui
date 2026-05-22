import { z } from "zod";

export const UI_EVENT_SCHEMA_VERSION = "risk-ui/v1";

export const UiEventKind = z.enum([
  "reasoning.started",
  "reasoning.completed",
  "plan.created",
  "query.started",
  "query.completed",
  "normalization.started",
  "normalization.completed",
  "visualization.proposed",
  "visualization.rendered",
  "provenance.attached",
  "followups.suggested",
  "error.safe",
]);
export type UiEventKind = z.infer<typeof UiEventKind>;

export const UiEventPhase = z.enum(["supervise", "query", "normalize", "visualize", "complete", "error"]);
export type UiEventPhase = z.infer<typeof UiEventPhase>;

export const UiEventEnvelopeV1 = z.object({
  schemaVersion: z.literal(UI_EVENT_SCHEMA_VERSION),
  eventId: z.string().min(1),
  runId: z.string().min(1).optional(),
  threadId: z.string().min(1).optional(),
  kind: UiEventKind,
  phase: UiEventPhase,
  timestamp: z.string().datetime(),
  payload: z.unknown(),
});
export type UiEventEnvelopeV1 = z.infer<typeof UiEventEnvelopeV1>;
