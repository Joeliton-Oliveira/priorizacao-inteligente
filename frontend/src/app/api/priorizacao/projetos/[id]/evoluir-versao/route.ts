import { proxyToBackend } from "@/lib/priorizacao/server-api";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const body = await request.text();
    return proxyToBackend(`/api/v1/projetos/${id}/evoluir-versao`, {
      method: "POST",
      body,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível evoluir a versão do projeto.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
