import type { MatrixPoint } from "./mock-matrix-data";
import type { QuadrantExplanationRow } from "./quadrant-explanation-table";

/** Mesmo corte da fila (`fila_priorizacao.py`). */
export const QUADRANT_CUTOFF = 2.5;

export const BUG_QUADRANT_EXPLANATION: {
  axisHint: string;
  rows: QuadrantExplanationRow[];
} = {
  axisHint: "",
  rows: [
    { ordem: 1, condicao: "x > 2,5 e y > 2,5", nome: "Crítica-alta" },
    { ordem: 2, condicao: "x > 2,5 e y ≤ 2,5", nome: "Alta-média" },
    { ordem: 3, condicao: "x ≤ 2,5 e y > 2,5", nome: "Média" },
    { ordem: 4, condicao: "x ≤ 2,5 e y ≤ 2,5", nome: "Baixa" },
  ],
};

export const INCREMENT_QUADRANT_EXPLANATION: {
  axisHint: string;
  rows: QuadrantExplanationRow[];
} = {
  axisHint: "",
  rows: [
    { ordem: 1, condicao: "x ≤ 2,5 e y > 2,5", nome: "Ganhos rápidos" },
    { ordem: 2, condicao: "x > 2,5 e y > 2,5", nome: "Grandes projetos" },
    { ordem: 3, condicao: "x ≤ 2,5 e y ≤ 2,5", nome: "Melhorias simples" },
    { ordem: 4, condicao: "x > 2,5 e y ≤ 2,5", nome: "Baixo retorno" },
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
  | "ganhos rápidos"
  | "grandes projetos"
  | "melhorias simples"
  | "baixo retorno";

const INCREMENT_QUADRANT_ORDER: IncrementQuadrantLabel[] = [
  "ganhos rápidos",
  "grandes projetos",
  "melhorias simples",
  "baixo retorno",
];

export function classifyIncrementQuadrant(
  x: number,
  y: number,
): IncrementQuadrantLabel {
  const t = QUADRANT_CUTOFF;
  if (x <= t && y > t) return "ganhos rápidos";
  if (x > t && y > t) return "grandes projetos";
  if (x <= t && y <= t) return "melhorias simples";
  return "baixo retorno";
}

export function countIncrementQuadrants(points: MatrixPoint[]): QuadrantBarDatum[] {
  const totals: Record<IncrementQuadrantLabel, number> = {
    "ganhos rápidos": 0,
    "grandes projetos": 0,
    "melhorias simples": 0,
    "baixo retorno": 0,
  };

  for (const point of points) {
    totals[classifyIncrementQuadrant(point.x, point.y)] += 1;
  }

  return INCREMENT_QUADRANT_ORDER.map((quadrante) => ({
    quadrante,
    quantidade: totals[quadrante],
  }));
}

/** Cores dos gráficos de barras — fonte única para badges na fila. */
export const BUG_QUADRANT_BAR_COLORS: Record<BugQuadrantLabel, string> = {
  "crítica-alta": "#f87171",
  "alta-média": "#fdba74",
  média: "#fcd34d",
  baixa: "#38bdf8",
};

export const INCREMENT_QUADRANT_BAR_COLORS: Record<IncrementQuadrantLabel, string> = {
  "ganhos rápidos": "#2563eb",
  "grandes projetos": "#7c3aed",
  "melhorias simples": "#38bdf8",
  "baixo retorno": "#94a3b8",
};

const BADGE_BASE = "border font-semibold capitalize";

const BUG_QUADRANT_BADGE_CLASSES: Record<BugQuadrantLabel, string> = {
  "crítica-alta": `${BADGE_BASE} border-[#f87171]/45 bg-[#f87171]/22 text-[#fecaca]`,
  "alta-média": `${BADGE_BASE} border-[#fdba74]/45 bg-[#fdba74]/22 text-[#ffedd5]`,
  média: `${BADGE_BASE} border-[#fcd34d]/45 bg-[#fcd34d]/22 text-[#fef9c3]`,
  baixa: `${BADGE_BASE} border-[#38bdf8]/45 bg-[#38bdf8]/22 text-[#e0f2fe]`,
};

const INCREMENT_QUADRANT_BADGE_CLASSES: Record<IncrementQuadrantLabel, string> = {
  "ganhos rápidos": `${BADGE_BASE} border-[#2563eb]/45 bg-[#2563eb]/22 text-[#bfdbfe]`,
  "grandes projetos": `${BADGE_BASE} border-[#7c3aed]/45 bg-[#7c3aed]/22 text-[#ddd6fe]`,
  "melhorias simples": `${BADGE_BASE} border-[#38bdf8]/45 bg-[#38bdf8]/22 text-[#e0f2fe]`,
  "baixo retorno": `${BADGE_BASE} border-[#94a3b8]/45 bg-[#94a3b8]/22 text-[#e2e8f0]`,
};

const BUG_BADGE_BY_ORDER = [
  BUG_QUADRANT_BADGE_CLASSES["crítica-alta"],
  BUG_QUADRANT_BADGE_CLASSES["alta-média"],
  BUG_QUADRANT_BADGE_CLASSES.média,
  BUG_QUADRANT_BADGE_CLASSES.baixa,
];

const INCREMENT_BADGE_BY_ORDER = [
  INCREMENT_QUADRANT_BADGE_CLASSES["ganhos rápidos"],
  INCREMENT_QUADRANT_BADGE_CLASSES["grandes projetos"],
  INCREMENT_QUADRANT_BADGE_CLASSES["melhorias simples"],
  INCREMENT_QUADRANT_BADGE_CLASSES["baixo retorno"],
];

function normalizeQuadrantKey(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

const BUG_BADGE_BY_NORMALIZED: Record<string, BugQuadrantLabel> = {
  "critica-alta": "crítica-alta",
  "alta-media": "alta-média",
  media: "média",
  baixa: "baixa",
};

const INCREMENT_BADGE_BY_NORMALIZED: Record<string, IncrementQuadrantLabel> = {
  "ganhos rapidos": "ganhos rápidos",
  "grandes projetos": "grandes projetos",
  "melhorias simples": "melhorias simples",
  "baixo retorno": "baixo retorno",
  "quick wins": "ganhos rápidos",
  preenchimento: "melhorias simples",
  desperdicio: "baixo retorno",
};

/** Classes do badge de quadrante na fila (mesmas cores dos gráficos por quadrante). */
export function getQuadrantBadgeClassName(
  tipo: "bug" | "increment",
  label: string,
  ordemQuadrante?: number,
): string {
  if (tipo === "bug") {
    const key = BUG_BADGE_BY_NORMALIZED[normalizeQuadrantKey(label)];
    if (key) return BUG_QUADRANT_BADGE_CLASSES[key];
    if (ordemQuadrante != null && ordemQuadrante >= 1 && ordemQuadrante <= 4) {
      return BUG_BADGE_BY_ORDER[ordemQuadrante - 1];
    }
    return `${BADGE_BASE} border-rose-500/35 bg-rose-500/15 text-rose-300`;
  }

  const key = INCREMENT_BADGE_BY_NORMALIZED[normalizeQuadrantKey(label)];
  if (key) return INCREMENT_QUADRANT_BADGE_CLASSES[key];
  if (ordemQuadrante != null && ordemQuadrante >= 1 && ordemQuadrante <= 4) {
    return INCREMENT_BADGE_BY_ORDER[ordemQuadrante - 1];
  }
  return `${BADGE_BASE} border-blue-500/35 bg-blue-500/15 text-blue-300`;
}
