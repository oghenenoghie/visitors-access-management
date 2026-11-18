import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_BASE = (process.env.ESTATE_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
const ACCESS_COOKIE = "estate_access";
const REFRESH_COOKIE = "estate_refresh";
const ACCESS_TTL = 15 * 60;
const REFRESH_TTL = 7 * 24 * 60 * 60;
type RouteContext = { params: Promise<{ path: string[] }> };

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict" as const,
    path: "/api/bff",
    maxAge,
  };
}
function setSession(response: NextResponse, access: string, refresh?: string) {
  response.cookies.set(ACCESS_COOKIE, access, cookieOptions(ACCESS_TTL));
  if (refresh) response.cookies.set(REFRESH_COOKIE, refresh, cookieOptions(REFRESH_TTL));
}
function clearSession(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", cookieOptions(0));
  response.cookies.set(REFRESH_COOKIE, "", cookieOptions(0));
}
function jsonError(message: string, status: number) {
  return NextResponse.json({ detail: message }, { status, headers: { "Cache-Control": "no-store" } });
}
async function refreshSession(refresh: string) {
  const response = await fetch(API_BASE + "/auth/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!response.ok) return null;
  return await response.json() as { access: string; refresh?: string };
}
async function upstream(path: string, method: string, body: string, access?: string) {
  const headers = new Headers({ Accept: "application/json" });
  if (body) headers.set("Content-Type", "application/json");
  if (access) headers.set("Authorization", "Bearer " + access);
  return fetch(API_BASE + "/" + path, {
    method,
    headers,
    body: body || undefined,
    cache: "no-store",
    redirect: "manual",
  });
}
async function relay(response: Response, cookiesToSet?: { access: string; refresh?: string }, clear = false) {
  const text = response.status === 204 ? null : await response.text();
  const headers = new Headers({ "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
  const contentType = response.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  const result = new NextResponse(text, { status: response.status, headers });
  if (cookiesToSet) setSession(result, cookiesToSet.access, cookiesToSet.refresh);
  if (clear) clearSession(result);
  return result;
}

async function handle(request: NextRequest, context: RouteContext) {
  const { path: segments } = await context.params;
  if (!segments?.length || segments.some(part => part === "." || part === "..")) return jsonError("Invalid API path.", 400);
  const path = segments.join("/");
  const method = request.method.toUpperCase();
  if (!["GET", "POST", "PUT", "PATCH", "DELETE"].includes(method)) return jsonError("Method not allowed.", 405);
  if (!["GET", "HEAD"].includes(method)) {
    const origin = request.headers.get("origin");
    if (!origin || origin !== request.nextUrl.origin) return jsonError("Cross-origin request rejected.", 403);
  }

  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  const isLogin = path === "auth/login";
  const isTwoFactor = path === "auth/2fa/setup" || path === "auth/2fa/confirm" || path === "auth/2fa/verify";
  const isLogout = path === "auth/logout";
  const body = method === "GET" ? "" : await request.text();

  if (isLogout) {
    if (access && refresh) {
      await upstream("auth/logout/", "POST", JSON.stringify({ refresh }), access).catch(() => null);
    }
    return relay(new Response(null, { status: 204 }), undefined, true);
  }

  let response = await upstream(path, method, body, isLogin || isTwoFactor ? undefined : access);
  let rotated: { access: string; refresh?: string } | undefined;

  if (response.status === 401 && !isLogin && !isTwoFactor && refresh) {
    const renewed = await refreshSession(refresh).catch(() => null);
    if (renewed?.access) {
      rotated = renewed;
      response = await upstream(path, method, body, renewed.access);
    } else {
      return relay(response, undefined, true);
    }
  }

  if (response.ok && (isLogin || path === "auth/2fa/confirm" || path === "auth/2fa/verify")) {
    const data = await response.json() as Record<string, unknown>;
    if (data.status === "authenticated" && typeof data.access === "string" && typeof data.refresh === "string") {
      const session = { access: data.access, refresh: data.refresh };
      delete data.access;
      delete data.refresh;
      const result = NextResponse.json(data, { status: response.status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
      setSession(result, session.access, session.refresh);
      return result;
    }
    return NextResponse.json(data, { status: response.status, headers: { "Cache-Control": "no-store" } });
  }

  return relay(response, rotated, response.status === 401);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
