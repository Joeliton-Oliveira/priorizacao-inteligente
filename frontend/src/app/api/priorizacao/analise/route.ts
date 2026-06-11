import { NextResponse } from "next/server";
import { mockAnaliseFromForm } from "@/lib/priorizacao/mock-analise";
import type { ActivityFormData } from "@/lib/activity-form-draft";

const API_BASE =
  process.env.PRIORIZACAO_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";
const ALLOW_MOCK_FALLBACK =
  process.env.PRIORIZACAO_ANALISE_ALLOW_MOCK_FALLBACK?.trim().toLowerCase() ===
  "true";

function buildMockResponse(body: unknown) {
  const payload = body as Record<string, unknown>;
  const draft = payload.formDraft as ActivityFormData | undefined;

  if (draft?.description?.trim()) {
    return NextResponse.json(mockAnaliseFromForm(draft), {
      headers: { "X-Analise-Source": "mock" },
    });
  }

  if (!String(payload.texto_original ?? "").trim()) {
    return NextResponse.json(
      { detail: "Informe a descrição da demanda antes de analisar." },
      { status: 400 },
    );
  }

  const mockForm: ActivityFormData = {
    description: String(payload.texto_original ?? ""),
    demandType: "nao_sei",
    systemArea: String(payload.modulo_afetado ?? ""),
    businessImportance: String(payload.contexto_negocio ?? ""),
    expectedResult: String(payload.objetivo_desejado ?? ""),
    perceivedImpact: String(payload.impacto_percebido_usuario ?? ""),
    frequency: "",
    urgency: "",
    temporaryWorkaround: String(payload.ha_contorno ?? ""),
    systemOrProduct: String(payload.sistema_ou_produto ?? ""),
    projectId: "",
    requesterId: String(payload.perfil_solicitante ?? ""),
  };

  return NextResponse.json(mockAnaliseFromForm(mockForm), {
    headers: { "X-Analise-Source": "mock" },
  });
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Corpo JSON inválido." }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${API_BASE}/api/v1/requisitos/analise`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await upstream.json().catch(() => ({}));

    if (!upstream.ok) {
      return NextResponse.json(data, { status: upstream.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    if (ALLOW_MOCK_FALLBACK) {
      return buildMockResponse(body);
    }

    const message =
      error instanceof Error
        ? error.message
        : "Não foi possível conectar na API de análise.";

    return NextResponse.json(
      { detail: `${message} Ative PRIORIZACAO_ANALISE_ALLOW_MOCK_FALLBACK=true apenas se quiser usar o mock em desenvolvimento.` },
      { status: 502 },
    );
  }
}
