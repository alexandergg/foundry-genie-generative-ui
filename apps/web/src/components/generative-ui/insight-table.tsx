import { formatValue } from "./format";
import { ProvenanceFooter } from "./provenance-footer";
import type { InsightTableProps } from "./types";

export function InsightTable({ title, columns, rows, provenance }: InsightTableProps) {
  return (
    <div className="viz-card">
      <h3 className="viz-title">{title}</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => {
                  const value = row[column];
                  const format = column.toLowerCase().includes("eur") ? "currency" : "number";
                  return <td key={column}>{typeof value === "number" ? formatValue(value, format) : value ?? "—"}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ProvenanceFooter provenance={provenance} />
    </div>
  );
}
