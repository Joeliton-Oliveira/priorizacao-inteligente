export type MatrixPoint = {
  x: number;
  y: number;
  titulo: string;
};

function fromPairs(pairs: [number, number][], prefix: string): MatrixPoint[] {
  return pairs.map(([x, y], index) => ({
    x,
    y,
    titulo: `${prefix} ${index + 1}`,
  }));
}

/** Dados de exemplo — espelham clusters típicos da matriz (API futura). */
export const MOCK_BUGS_MATRIX: MatrixPoint[] = fromPairs(
  [
    [1.5, 1.0],
    [1.5, 2.5],
    [1.5, 4.0],
    [1.5, 5.0],
    [1.5, 3.2],
    [1.5, 1.8],
    [3.5, 1.5],
    [3.5, 3.0],
    [3.5, 4.5],
    [3.5, 2.2],
    [3.5, 5.0],
    [3.5, 0.8],
    [4.5, 2.0],
    [4.5, 3.5],
    [4.5, 5.0],
    [4.5, 1.2],
    [4.5, 4.2],
    [4.5, 2.8],
    [2.5, 2.0],
    [2.5, 4.0],
    [5.0, 3.0],
  ],
  "Bug",
);

export const MOCK_INCREMENTS_MATRIX: MatrixPoint[] = fromPairs(
  [
    [1.4, 1.5],
    [1.5, 2.5],
    [1.5, 4.5],
    [1.5, 3.2],
    [2.5, 1.8],
    [2.6, 4.2],
    [2.5, 3.0],
    [2.4, 4.8],
    [3.6, 2.0],
    [3.6, 4.0],
    [3.5, 3.5],
    [4.5, 1.6],
    [4.6, 4.3],
    [4.5, 2.8],
    [4.4, 4.0],
    [1.5, 1.8],
    [2.6, 2.2],
    [3.6, 4.5],
    [4.5, 3.8],
    [2.5, 4.5],
  ],
  "Incremento",
);
