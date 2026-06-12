import { describe, expect, it } from "vitest";
import { normalizeAgentUrl } from "./agent-url";

describe("normalizeAgentUrl", () => {
  it("falls back to the local declarative agent when unset", () => {
    expect(normalizeAgentUrl(undefined)).toBe("http://localhost:8124");
  });

  it("keeps absolute http(s) urls untouched", () => {
    expect(normalizeAgentUrl("https://agent.example.com")).toBe("https://agent.example.com");
    expect(normalizeAgentUrl("http://localhost:9000")).toBe("http://localhost:9000");
  });

  it("prefixes bare hosts with http://", () => {
    expect(normalizeAgentUrl("localhost:8124")).toBe("http://localhost:8124");
  });

  it("honours a custom fallback", () => {
    expect(normalizeAgentUrl(undefined, "http://localhost:8125")).toBe("http://localhost:8125");
  });
});
