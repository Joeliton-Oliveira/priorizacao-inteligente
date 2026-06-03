/** Mapa id → posição na fila operacional (vazão + intercalação da config). */
export function buildFilaRankMap(fila: { id: number }[]): Map<number, number> {
  const map = new Map<number, number>();
  fila.forEach((item, index) => {
    map.set(item.id, index);
  });
  return map;
}

export function compareByFilaRank<T extends { id: number }>(
  a: T,
  b: T,
  rank: Map<number, number>,
): number {
  const rankA = rank.get(a.id) ?? Number.MAX_SAFE_INTEGER;
  const rankB = rank.get(b.id) ?? Number.MAX_SAFE_INTEGER;
  if (rankA !== rankB) return rankA - rankB;
  return a.id - b.id;
}
