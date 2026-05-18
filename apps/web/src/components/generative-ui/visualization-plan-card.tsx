import type { VisualizationPlanProps } from "./types";

export function VisualizationPlanCard({ approach, technology, key_elements }: VisualizationPlanProps) {
  return (
    <div className="viz-card">
      <h3 className="viz-title">Visualization plan</h3>
      <p><strong>Approach:</strong> {approach}</p>
      <p><strong>Technology:</strong> {technology}</p>
      <ul className="plan-list">
        {key_elements.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}
