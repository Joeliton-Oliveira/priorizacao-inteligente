import { NextResponse } from "next/server";

export function getPriorizacaoApiBase() {
  return process.env.PRIORIZACAO_API_URL ?? "http://backend:8000";
}

export function getJsonHeaders() {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
}

export function toDetail(errorBody: unknown, fallback: string) {
  if (!errorBody || typeof errorBody !== "object") return fallback;
  const detail = "detail" in errorBody ? (errorBody as { detail?: unknown }).detail : undefined;
  if (typeof detail === "string" && detail.trim()) return detail;
  return fallback;
}

export async function readUpstreamBody(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
  try {
    return await response.text();
  } catch {
    return null;
  }
}

export async function proxyToBackend(
  path: string,
  init?: RequestInit,
) {
  const response = await fetch(`${getPriorizacaoApiBase()}${path}`, {
    ...init,
    headers: {
      ...getJsonHeaders(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  const body = await readUpstreamBody(response);
  if (!response.ok) {
    return NextResponse.json(
      {
        detail: toDetail(body, `Falha ao consumir ${path}`),
        upstreamStatus: response.status,
      },
      { status: response.status },
    );
  }

  return NextResponse.json(body, { status: response.status });
}
