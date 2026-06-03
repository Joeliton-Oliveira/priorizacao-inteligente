import type { MatrixPoint } from "@/app/(dashboard)/activities/_components/mock-matrix-data";

const STORAGE_KEY = "intelli-reqs:user-matrix-points";

type StoredPoint = MatrixPoint & { tipo: "BUG" | "INCREMENTO" };

export function loadUserMatrixPoints(): StoredPoint[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as StoredPoint[];
  } catch {
    return [];
  }
}

export function appendUserMatrixPoint(
  point: MatrixPoint,
  tipo: "BUG" | "INCREMENTO",
): void {
  if (typeof window === "undefined") return;
  const current = loadUserMatrixPoints();
  current.push({ ...point, tipo });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
}

export function splitUserMatrixPoints(): {
  bugs: MatrixPoint[];
  incrementos: MatrixPoint[];
} {
  const all = loadUserMatrixPoints();
  return {
    bugs: all.filter((p) => p.tipo === "BUG").map(({ x, y, titulo }) => ({ x, y, titulo })),
    incrementos: all
      .filter((p) => p.tipo === "INCREMENTO")
      .map(({ x, y, titulo }) => ({ x, y, titulo })),
  };
}
