import { proxyToBackend } from "@/lib/priorizacao/server-api";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(request: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const url = new URL(request.url);
    const query = url.searchParams.toString();
    return proxyToBackend(
      `/api/v1/projetos/${id}/historico-versao${query ? `?${query}` : ""}`,
      { method: "GET" },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível carregar o histórico do projeto.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
