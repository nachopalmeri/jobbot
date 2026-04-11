import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest, clearToken, getApiBaseUrl, getToken, setToken } from "./api";

describe("api helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("always resolves the dashboard proxy base url", () => {
    expect(getApiBaseUrl()).toBe("/api/backend");
  });

  it("does not expose auth tokens in browser helpers", async () => {
    setToken("abc123");
    expect(getToken()).toBeNull();

    await clearToken();
    expect(fetch).toHaveBeenCalledWith(
      "/api/backend/auth/logout",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
  });

  it("sends requests through the dashboard proxy with cookies included", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ ok: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/users/dashboard", { method: "GET" }, true);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend/users/dashboard",
      expect.objectContaining({
        headers: expect.any(Headers),
        credentials: "include",
      }),
    );
  });

  it("surfaces backend detail when request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ detail: "Credenciales invalidas" }),
      }),
    );

    await expect(apiRequest("/auth/token", { method: "POST" })).rejects.toMatchObject({
      status: 401,
      message: "Credenciales invalidas",
    });
  });
});
