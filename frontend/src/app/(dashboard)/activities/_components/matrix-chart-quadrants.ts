export type MatrixQuadrantSlot = "topLeft" | "topRight" | "bottomLeft" | "bottomRight";

export type MatrixQuadrantVisual = {
  label: string;
  textClass: string;
  borderClass: string;
  bgClass: string;
};

export type MatrixQuadrantConfig = Record<MatrixQuadrantSlot, MatrixQuadrantVisual>;

export const BUG_MATRIX_QUADRANTS: MatrixQuadrantConfig = {
  topLeft: {
    label: "Alta severidade / Baixa criticidade",
    textClass: "text-amber-300/90",
    borderClass: "border-amber-500/35",
    bgClass: "bg-amber-500/8",
  },
  topRight: {
    label: "Alta severidade / Alta criticidade",
    textClass: "text-red-300/90",
    borderClass: "border-red-500/35",
    bgClass: "bg-red-500/8",
  },
  bottomLeft: {
    label: "Baixa severidade / Baixa criticidade",
    textClass: "text-sky-300/80",
    borderClass: "border-sky-500/30",
    bgClass: "bg-sky-500/8",
  },
  bottomRight: {
    label: "Baixa severidade / Alta criticidade",
    textClass: "text-orange-300/90",
    borderClass: "border-orange-500/35",
    bgClass: "bg-orange-500/8",
  },
};

export const INCREMENT_MATRIX_QUADRANTS: MatrixQuadrantConfig = {
  topLeft: {
    label: "Ganhos rápidos",
    textClass: "text-blue-300/90",
    borderClass: "border-blue-500/35",
    bgClass: "bg-blue-500/8",
  },
  topRight: {
    label: "Grandes projetos",
    textClass: "text-violet-300/90",
    borderClass: "border-violet-500/35",
    bgClass: "bg-violet-500/8",
  },
  bottomLeft: {
    label: "Melhorias simples",
    textClass: "text-emerald-300/80",
    borderClass: "border-emerald-500/30",
    bgClass: "bg-emerald-500/8",
  },
  bottomRight: {
    label: "Baixo retorno",
    textClass: "text-slate-400/90",
    borderClass: "border-slate-500/30",
    bgClass: "bg-slate-500/8",
  },
};
