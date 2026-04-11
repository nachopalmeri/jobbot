import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const SESSION_COOKIE = "jobbot_session";
const SESSION_TTL_SECONDS = 60 * 60 * 24;
const SESSION_PATHS = new Set([
  "POST:/auth/register",
  "POST:/auth/token",
  "POST:/auth/telegram",
  "POST:/auth/telegram/code",
]);
const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "cookie",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "set-cookie",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function resolveApiOrigin() {
  return (
    process.env.JOBBOT_API_ORIGIN?.trim() ||
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
}

function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  };
}

function isSessionResponse(pathname: string, method: string) {
  return SESSION_PATHS.has(`${method.toUpperCase()}:${pathname}`);
}

function forwardHeaders(request: NextRequest, token: string | undefined) {
  const headers = new Headers();

  request.headers.forEach((value, key) => {
    if (HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      return;
    }
    headers.set(key, value);
  });

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  } else {
    headers.delete("Authorization");
  }

  return headers;
}

function sanitizeSessionPayload(payload: unknown) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return payload;
  }

  const sanitized = { ...(payload as Record<string, unknown>) };
  delete sanitized.access_token;
  delete sanitized.token_type;
  sanitized.authenticated = true;
  return sanitized;
}

function copyResponseHeaders(source: Headers, target: Headers) {
  source.forEach((value, key) => {
    if (HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      return;
    }
    target.set(key, value);
  });
}

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const pathname = `/${path.join("/")}`;
  const method = request.method.toUpperCase();

  if (pathname === "/auth/logout" && method === "POST") {
    const response = NextResponse.json({ message: "Sesion cerrada" });
    response.cookies.set(SESSION_COOKIE, "", {
      ...sessionCookieOptions(),
      maxAge: 0,
    });
    return response;
  }

  const targetUrl = new URL(`${resolveApiOrigin()}${pathname}`);
  request.nextUrl.searchParams.forEach((value, key) => {
    targetUrl.searchParams.set(key, value);
  });

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const body =
    method === "GET" || method === "HEAD" ? undefined : await request.text();

  let upstream: Response;
  try {
    upstream = await fetch(targetUrl, {
      method,
      headers: forwardHeaders(request, token),
      body,
      redirect: "manual",
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "No se pudo conectar con la API de JobBot." },
      { status: 502 },
    );
  }

  const contentType = upstream.headers.get("content-type") ?? "";
  const responseHeaders = new Headers();
  copyResponseHeaders(upstream.headers, responseHeaders);

  if (contentType.includes("application/json")) {
    const payload = await upstream.json();
    const response = NextResponse.json(
      isSessionResponse(pathname, method) ? sanitizeSessionPayload(payload) : payload,
      {
        status: upstream.status,
        headers: responseHeaders,
      },
    );

    if (isSessionResponse(pathname, method) && upstream.ok) {
      const nextToken =
        payload && typeof payload === "object" && "access_token" in payload
          ? String((payload as Record<string, unknown>).access_token || "")
          : "";
      if (nextToken) {
        response.cookies.set(SESSION_COOKIE, nextToken, sessionCookieOptions());
      }
    }

    if (upstream.status === 401) {
      response.cookies.set(SESSION_COOKIE, "", {
        ...sessionCookieOptions(),
        maxAge: 0,
      });
    }

    return response;
  }

  const response = new NextResponse(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: responseHeaders,
  });

  if (upstream.status === 401) {
    response.cookies.set(SESSION_COOKIE, "", {
      ...sessionCookieOptions(),
      maxAge: 0,
    });
  }

  return response;
}

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

export async function OPTIONS(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}
