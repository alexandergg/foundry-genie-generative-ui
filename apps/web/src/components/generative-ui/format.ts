import type { Format } from "./types";

export function formatValue(value: string | number | null | undefined, format: Format = "number") {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (format === "currency") {
    return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", notation: "compact", maximumFractionDigits: 1 }).format(value);
  }
  if (format === "percent") {
    return new Intl.NumberFormat("es-ES", { style: "percent", maximumFractionDigits: 1 }).format(value);
  }
  return new Intl.NumberFormat("es-ES", { notation: Math.abs(value) >= 1000000 ? "compact" : "standard", maximumFractionDigits: 1 }).format(value);
}
