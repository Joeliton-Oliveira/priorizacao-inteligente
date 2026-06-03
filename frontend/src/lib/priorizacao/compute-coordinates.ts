import type { PerguntaAvaliacao } from "./types";

export function computeCoordinatesFromAnswers(
  perguntas: PerguntaAvaliacao[],
  answers: Record<number, number>,
): { coordenada_x: number; coordenada_y: number; score: number } {
  const byDim: Record<string, number[]> = {};

  for (const pergunta of perguntas) {
    const valor = answers[pergunta.id_pergunta];
    if (valor === undefined) continue;
    const dim = pergunta.dimensao.toUpperCase().trim();
    if (!byDim[dim]) byDim[dim] = [];
    byDim[dim].push(valor);
  }

  const media = (dim: string) => {
    const vals = byDim[dim];
    if (!vals?.length) return 0;
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  };

  const tipo =
    perguntas.some((p) => p.dimensao.toUpperCase() === "CRITICIDADE") ||
    perguntas.some((p) => p.dimensao.toUpperCase() === "SEVERIDADE")
      ? "BUG"
      : "INCREMENTO";

  let coordenada_x: number;
  let coordenada_y: number;

  if (tipo === "BUG") {
    coordenada_x = media("CRITICIDADE");
    coordenada_y = media("SEVERIDADE");
  } else {
    coordenada_x = media("ESFORCO");
    coordenada_y = media("VALOR");
  }

  coordenada_x = Math.round(coordenada_x * 100) / 100;
  coordenada_y = Math.round(coordenada_y * 100) / 100;
  const score = Math.round(coordenada_x * coordenada_y * 100) / 100;

  return { coordenada_x, coordenada_y, score };
}
