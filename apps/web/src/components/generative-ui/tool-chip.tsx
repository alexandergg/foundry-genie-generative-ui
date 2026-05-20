const PRETTY_NAME: Record<string, string> = {
  ask_genie: "Databricks Genie",
  query_genie: "Databricks Genie",
};

function prettify(name: string) {
  return PRETTY_NAME[name] ?? name.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ToolChip({ name, status }: { name: string; status: string }) {
  const done = status.toLowerCase() === "complete";
  return (
    <span className={`tool-chip ${done ? "done" : "running"}`}>
      <span className="tool-chip-icon" aria-hidden="true" />
      <span className="tool-chip-name">{prettify(name)}</span>
      <span className="tool-chip-status">{done ? "done" : "running"}</span>
    </span>
  );
}
