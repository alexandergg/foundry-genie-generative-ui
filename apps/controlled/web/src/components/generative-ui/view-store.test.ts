import { beforeEach, describe, expect, it } from "vitest";
import { getViewSnapshot, resetViewStore, setPresentationMode, setSpotlight } from "./view-store";

describe("view-store mutations", () => {
  beforeEach(() => resetViewStore());

  it("starts with no spotlight and presentation mode off", () => {
    expect(getViewSnapshot()).toEqual({ spotlightVisualId: null, presentationMode: false });
  });

  it("setSpotlight stores and replaces the spotlighted id", () => {
    setSpotlight("v1");
    expect(getViewSnapshot().spotlightVisualId).toBe("v1");
    setSpotlight("v2");
    expect(getViewSnapshot().spotlightVisualId).toBe("v2");
  });

  it("setSpotlight(null) clears the spotlight", () => {
    setSpotlight("v1");
    setSpotlight(null);
    expect(getViewSnapshot().spotlightVisualId).toBeNull();
  });

  it("setPresentationMode toggles without touching the spotlight", () => {
    setSpotlight("v1");
    setPresentationMode(true);
    expect(getViewSnapshot()).toEqual({ spotlightVisualId: "v1", presentationMode: true });
    setPresentationMode(false);
    expect(getViewSnapshot().presentationMode).toBe(false);
  });
});
