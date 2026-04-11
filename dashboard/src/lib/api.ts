function resolveApiBaseUrl() {
  return "/api/backend";
}

export interface ApiError {
  detail?: string;
  message: string;
  status: number;
}

export function getApiBaseUrl() {
  return resolveApiBaseUrl();
}

export function getToken() {
  return null;
}

export function setToken(_: string) {
  return;
}

export async function clearToken() {
  await fetch(`${resolveApiBaseUrl()}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  requiresAuth = false,
): Promise<T> {
  const apiBaseUrl = resolveApiBaseUrl();

  const headers = new Headers(init.headers ?? {});
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  const isUrlEncoded =
    typeof URLSearchParams !== "undefined" && init.body instanceof URLSearchParams;

  if (!isFormData && !headers.has("Content-Type") && init.body) {
    headers.set(
      "Content-Type",
      isUrlEncoded ? "application/x-www-form-urlencoded;charset=UTF-8" : "application/json",
    );
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "string"
        ? payload
        : payload?.detail || payload?.message || "Error inesperado";
    throw {
      detail,
      message: detail,
      status: response.status,
    } satisfies ApiError;
  }

  return payload as T;
}
