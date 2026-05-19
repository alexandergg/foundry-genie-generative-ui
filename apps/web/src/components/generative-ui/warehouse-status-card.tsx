import type { WarehouseStatusCardProps } from "./types";

export function WarehouseStatusCard({ warehouseName, status }: WarehouseStatusCardProps) {
  const pending = status === "query-pending";

  return (
    <div className="viz-card warning">
      <h3 className="viz-title">SQL Warehouse</h3>
      <p>The warehouse <strong>{warehouseName}</strong> needs attention: <strong>{status}</strong>.</p>
      <p className="viz-muted">
        {pending
          ? "Genie indicates that the query is still running. Retry in a few seconds if the warehouse is already active."
          : "Start it from Databricks or with the Risk Exposure scripts before running the query again."}
      </p>
    </div>
  );
}
