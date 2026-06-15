export type ViewState = {
  spotlightVisualId: string | null;
  presentationMode: boolean;
};

let state: ViewState = { spotlightVisualId: null, presentationMode: false };
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export function subscribeView(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getViewSnapshot(): ViewState {
  return state;
}

export function setSpotlight(id: string | null) {
  state = { ...state, spotlightVisualId: id };
  emit();
}

export function setPresentationMode(enabled: boolean) {
  state = { ...state, presentationMode: enabled };
  emit();
}

export function resetViewStore() {
  state = { spotlightVisualId: null, presentationMode: false };
  emit();
}
