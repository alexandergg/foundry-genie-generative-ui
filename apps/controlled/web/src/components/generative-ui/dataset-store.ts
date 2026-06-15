import type { Dataset, DatasetSummary } from "./dataset-types";

export const MAX_DATASETS = 8;

let datasets: Dataset[] = [];
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export function subscribeDatasets(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function putDataset(ds: Dataset) {
  datasets = [...datasets.filter((d) => d.id !== ds.id), ds];
  if (datasets.length > MAX_DATASETS) {
    datasets = datasets.slice(datasets.length - MAX_DATASETS);
  }
  emit();
}

export function getDataset(id: string): Dataset | undefined {
  return datasets.find((d) => d.id === id);
}

export function listSummaries(): DatasetSummary[] {
  return datasets.map((d) => ({
    id: d.id,
    title: d.title,
    rowCount: d.rows.length,
    columns: d.columns,
  }));
}

export function getDatasetsSnapshot(): Dataset[] {
  return datasets;
}

export function resetDatasetStore() {
  datasets = [];
  emit();
}
