import type { MatrixPoint } from "./mock-matrix-data";
import type { QuadrantExplanationRow } from "./quadrant-explanation-table";

/** Mesmo corte da fila (`fila_priorizacao.py`). */
export const QUADRANT_CUTOFF = 2.5;

export const BUG_QUADRANT_EXPLANATION: {
  axisHint: string;
  rows: QuadrantExplanationRow[];
} = {
  axisHint: "Condição (x = criticidade, y = severidade) — corte em 2,5:",
  rows: [
    { ordem: 1, condicao: "x > 2,5 e y > 2,5", nome: "Crítica-alta" },
    { ordem: 2, condicao: "x > 2,5 e y ≤ 2,5", nome: "Alta-média" },
    { ordem: 3, condicao: "x ≤ 2,5 e y > 2,5", nome: "Média" },
    { ordem: 4, condicao: "demais casos", nome: "Baixa" },
  ],
};

export const INCREMENT_QUADRANT_EXPLANATION: {
  axisHint: string;
  rows: QuadrantExplanationRow[];
} = {
  axisHint: "Condição (x = esforço, y = valor) — corte em 2,5:",
  rows: [
    { ordem: 1, condicao: "x ≤ 2,5 e y > 2,5", nome: "Quick wins" },
    { ordem: 2, condicao: "x > 2,5 e y > 2,5", nome: "Grandes projetos" },
    { ordem: 3, condicao: "x ≤ 2,5 e y ≤ 2,5", nome: "Preenchimento" },
    { ordem: 4, condicao: "demais casos", nome: "Desperdício" },
  ],
};

export type BugQuadrantLabel = "crítica-alta" | "alta-média" | "média" | "baixa";

const BUG_QUADRANT_ORDER: BugQuadrantLabel[] = [
  "crítica-alta",
  "alta-média",
  "média",
  "baixa",
];

export function classifyBugQuadrant(x: number, y: number): BugQuadrantLabel {
  const t = QUADRANT_CUTOFF;
  if (x > t && y > t) return "crítica-alta";
  if (x > t && y <= t) return "alta-média";
  if (x <= t && y > t) return "média";
  return "baixa";
}

export type QuadrantBarDatum = {
  quadrante: string;
  quantidade: number;
};

export function countBugQuadrants(points: MatrixPoint[]): QuadrantBarDatum[] {
  const totals: Record<BugQuadrantLabel, number> = {
    "crítica-alta": 0,
    "alta-média": 0,
    média: 0,
    baixa: 0,
  };

  for (const point of points) {
    totals[classifyBugQuadrant(point.x, point.y)] += 1;
  }

  return BUG_QUADRANT_ORDER.map((quadrante) => ({
    quadrante,
    quantidade: totals[quadrante],
  }));
}

export type IncrementQuadrantLabel =
  | "quick wins"
  | "grandes projetos"
  | "preenchimento"
  | "desperdício";

const INCREMENT_QUADRANT_ORDER: IncrementQuadrantLabel[] = [
  "quick wins",
  "grandes projetos",
  "preenchimento",
  "desperdício",
];

export function classifyIncrementQuadrant(
  x: number,
  y: number,
): IncrementQuadrantLabel {
  const t = QUADRANT_CUTOFF;
  if (x <= t && y > t) return "quick wins";
  if (x > t && y > t) return "grandes projetos";
  if (x <= t && y <= t) return "preenchimento";
  return "desperdício";
}

export function countIncrementQuadrants(points: MatrixPoint[]): QuadrantBarDatum[] {
  const totals: Record<IncrementQuadrantLabel, number> = {
    "quick wins": 0,
    "grandes projetos": 0,
    preenchimento: 0,
    desperdício: 0,
  };

  for (const point of points) {
    totals[classifyIncrementQuadrant(point.x, point.y)] += 1;
  }

  return INCREMENT_QUADRANT_ORDER.map((quadrante) => ({
    quadrante,
    quantidade: totals[quadrante],
  }));
}
