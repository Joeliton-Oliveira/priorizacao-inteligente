import { proxyToBackend } from "@/lib/priorizacao/server-api";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(_request: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    return proxyToBackend(`/api/v1/demandas/${id}/visao-360`, { method: "GET" });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível carregar a visão 360.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
