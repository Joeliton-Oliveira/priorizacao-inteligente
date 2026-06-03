import { NextResponse } from "next/server";

const API_BASE =
  process.env.PRIORIZACAO_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ detail: "Corpo JSON inválido." }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${API_BASE}/api/v1/requisitos/salvar-avaliacao`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await upstream.json().catch(() => ({}));

    if (!upstream.ok) {
      return NextResponse.json(data, { status: upstream.status });
    }

    const cadastro =
      body.cadastro && typeof body.cadastro === "object"
        ? (body.cadastro as Record<string, unknown>)
        : null;
    const rawProjectId = cadastro?.id_projeto;
    const projectId =
      typeof rawProjectId === "number"
        ? rawProjectId
        : Number.parseInt(String(rawProjectId ?? ""), 10);

    if (!Number.isInteger(projectId)) {
      return NextResponse.json(data);
    }

    const usuarioAvaliador =
      typeof body.usuario_avaliador === "string"
        ? body.usuario_avaliador.trim() || undefined
        : undefined;

    const evolutionResponse = await fetch(
      `${API_BASE}/api/v1/projetos/${projectId}/evoluir-versao`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nivel: "patch",
          motivo: "Demanda priorizada registrada no fluxo Next.js",
          usuario_responsavel: usuarioAvaliador,
        }),
      },
    );

    const evolutionData = await evolutionResponse.json().catch(() => ({}));

    if (!evolutionResponse.ok) {
      return NextResponse.json({
        ...data,
        warning:
          typeof evolutionData.detail === "string"
            ? `Avaliação salva no banco, mas a versão do projeto não foi atualizada automaticamente: ${evolutionData.detail}`
            : "Avaliação salva no banco, mas a versão do projeto não foi atualizada automaticamente.",
      });
    }

    return NextResponse.json({
      ...data,
      versao_projeto_atualizada:
        typeof evolutionData.versao_atual === "string"
          ? evolutionData.versao_atual
          : undefined,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível salvar na API.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
