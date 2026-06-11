import { proxyToBackend } from "@/lib/priorizacao/server-api";

export async function GET() {
  try {
    return proxyToBackend("/api/v1/fila", { method: "GET" });
  } catch (error) {
    return Response.json(
      {
        detail:
          error instanceof Error
            ? error.message
            : "Não foi possível carregar a fila operacional.",
      },
      { status: 500 },
    );
  }
}
