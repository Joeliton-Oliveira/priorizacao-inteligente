import { proxyToBackend } from "@/lib/priorizacao/server-api";

export async function GET() {
  try {
    return proxyToBackend("/api/v1/fila/incrementos", { method: "GET" });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Não foi possível carregar a fila de incrementos.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
