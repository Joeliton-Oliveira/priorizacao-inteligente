import { NextResponse } from "next/server";

const API_BASE =
  process.env.PRIORIZACAO_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const body = await request.json();

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

    return NextResponse.json(data);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Não foi possível salvar na API.";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
