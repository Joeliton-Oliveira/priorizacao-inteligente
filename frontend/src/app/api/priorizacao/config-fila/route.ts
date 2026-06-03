import { proxyToBackend } from "@/lib/priorizacao/server-api";

export async function GET() {
  try {
    return proxyToBackend("/api/v1/config-fila", { method: "GET" });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Não foi possível carregar a calibragem.";
    return Response.json({ detail: message }, { status: 502 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.text();
    return proxyToBackend("/api/v1/config-fila", {
      method: "POST",
      body,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível salvar a calibragem.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
