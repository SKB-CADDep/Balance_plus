import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "./api";

describe("resolveApiBaseUrl", () => {
    it("uses same-origin requests when no API URL is configured", () => {
        expect(resolveApiBaseUrl()).toBe("");
        expect(resolveApiBaseUrl("   ")).toBe("");
    });

    it("normalizes an explicitly configured API URL", () => {
        expect(resolveApiBaseUrl("http://backend.example:8010///")).toBe(
            "http://backend.example:8010",
        );
    });
});
