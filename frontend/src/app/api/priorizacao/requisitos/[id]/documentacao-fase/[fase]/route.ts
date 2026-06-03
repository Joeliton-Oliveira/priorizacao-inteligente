import { proxyToBackend } from "@/lib/priorizacao/server-api";

type RouteContext = {
  params: Promise<{ id: string; fase: string }>;
};

export async function PUT(request: Request, context: RouteContext) {
  try {
    const { id, fase } = await context.params;
    const body = await request.text();
    return proxyToBackend(`/api/v1/requisitos/${id}/documentacao-fase/${fase}`, {
      method: "PUT",
      body,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível guardar a fase documental.";
    return Response.json({ detail: message }, { status: 502 });
  }
}
