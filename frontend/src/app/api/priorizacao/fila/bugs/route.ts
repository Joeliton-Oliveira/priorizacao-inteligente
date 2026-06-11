import { proxyToBackend } from "@/lib/priorizacao/server-api";

export async function GET() {
  try {
    return proxyToBackend("/api/v1/fila/bugs", { method: "GET" });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível carregar a fila de bugs.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
