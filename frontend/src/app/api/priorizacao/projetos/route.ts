import { proxyToBackend } from "@/lib/priorizacao/server-api";

function getPathWithQuery(requestUrl: string) {
  const url = new URL(requestUrl);
  const query = url.searchParams.toString();
  return `/api/v1/projetos${query ? `?${query}` : ""}`;
}

export async function GET(request: Request) {
  try {
    return proxyToBackend(getPathWithQuery(request.url), { method: "GET" });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Não foi possível conectar na API de projetos.";
    return Response.json({ detail: message }, { status: 502 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.text();
    return proxyToBackend("/api/v1/projetos", {
      method: "POST",
      body,
    });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Não foi possível conectar na API de projetos.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
