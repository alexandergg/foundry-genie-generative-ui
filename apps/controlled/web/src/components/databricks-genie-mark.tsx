type DatabricksGenieMarkProps = {
  compact?: boolean;
  showLabel?: boolean;
  animated?: boolean;
};

export function DatabricksGenieMark({ compact = false, showLabel = false, animated = false }: DatabricksGenieMarkProps) {
  const className = ["genie-mark", compact ? "compact" : "", animated ? "animated" : ""].filter(Boolean).join(" ");

  return (
    <div className={className} aria-label="Databricks Genie">
      <svg viewBox="0 0 64 64" role="img" aria-hidden="true">
        <path className="genie-stack top" d="M32 7 57 20 32 33 7 20 32 7Z" />
        <path className="genie-stack mid" d="M15 27 32 36 49 27 57 31 32 44 7 31 15 27Z" />
        <path className="genie-stack bottom" d="M15 39 32 48 49 39 57 43 32 56 7 43 15 39Z" />
        <circle className="genie-spark one" cx="46" cy="13" r="2.6" />
        <circle className="genie-spark two" cx="20" cy="11" r="1.7" />
      </svg>
      {showLabel && (
        <span className="genie-wordmark">
          <strong>Databricks</strong>
          <em>Genie</em>
        </span>
      )}
    </div>
  );
}
