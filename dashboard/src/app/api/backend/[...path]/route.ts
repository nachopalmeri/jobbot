import type { NextRequest } from "next/server";

const DEFAULT_REMOTE_API_ORIGIN = "http://128.203.100.186:8000";

function getBackendOrigin() {
  const configured =
    process.env.JOBBOT_API_ORIGIN ||
    process.env.JOBBOT_API_URL ||
    process.env.NEXT_PUBLIC_API_URL;

  if (configured) {
    return configured.replace(/\/$/, "");
  }

  return process.env.VERCEL ? DEFAULT_REMOTE_API_ORIGIN : "http://localhost:8000";
}

function buildTargetUrl(request: NextRequest, path: string[]) {
  const target = new URL(`${getBackendOrigin()}/${path.join("/")}`);
  target.search = request.nextUrl.search;
  return target;
}

function forwardHeaders(request: NextRequest) {
  const headers = new Headers(request.headers);

  headers.delete("host");
  headers.delete("content-length");
  headers.delete("x-forwarded-host");
  headers.delete("x-forwarded-port");
  headers.delete("x-forwarded-proto");

  return headers;
}

async function proxyRequest(request: NextRequest, path: string[]) {
  const target = buildTargetUrl(request, path);
  const method = request.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);

  const upstream = await fetch(target, {
    method,
    headers: forwardHeaders(request),
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store",
  });

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-length");
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");

  return new Response(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function OPTIONS(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}
