import { proxyToBackend } from "@/lib/priorizacao/server-api";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function PATCH(request: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const body = await request.text();
    return proxyToBackend(`/api/v1/projetos/${id}/status`, {
      method: "PATCH",
      body,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível atualizar o status do projeto.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
