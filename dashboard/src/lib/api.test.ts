import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest, clearToken, getApiBaseUrl, getToken, setToken } from "./api";

const localStorageMock = {
  store: {} as Record<string, string>,
  getItem(key: string) {
    return this.store[key] ?? null;
  },
  setItem(key: string, value: string) {
    this.store[key] = value;
  },
  removeItem(key: string) {
    delete this.store[key];
  },
  clear() {
    this.store = {};
  },
};

describe("api helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("window", { localStorage: localStorageMock });
    vi.stubGlobal("localStorage", localStorageMock);
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("always resolves the dashboard proxy base url", () => {
    expect(getApiBaseUrl()).toBe("/api/backend");
  });

  it("stores and clears auth token in localStorage", () => {
    setToken("abc123");
    expect(getToken()).toBe("abc123");

    clearToken();
    expect(getToken()).toBeNull();
  });

  it("adds authorization header for authenticated requests", async () => {
    setToken("secure-token");
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
      }),
    );
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer secure-token");
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
