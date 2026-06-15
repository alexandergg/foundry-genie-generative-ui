import { describe, expect, it } from "vitest";
import { normalizeAgentUrl } from "./agent-url";

describe("normalizeAgentUrl", () => {
  it("falls back to the local open-ended agent when unset", () => {
    expect(normalizeAgentUrl(undefined)).toBe("http://localhost:8125");
  });

  it("keeps absolute http(s) urls untouched", () => {
    expect(normalizeAgentUrl("https://agent.example.com")).toBe("https://agent.example.com");
  });

  it("prefixes bare hosts with http://", () => {
    expect(normalizeAgentUrl("localhost:8125")).toBe("http://localhost:8125");
  });
});
