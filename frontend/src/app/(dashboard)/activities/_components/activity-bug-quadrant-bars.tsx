"use client";

import type { MatrixPoint } from "./mock-matrix-data";
import { BUG_QUADRANT_EXPLANATION, countBugQuadrants } from "./matrix-quadrants";
import { ActivityQuadrantBars } from "./activity-quadrant-bars";

const BAR_COLORS: Record<string, string> = {
  "crítica-alta": "#b91c1c",
  "alta-média": "#dc2626",
  média: "#f87171",
  baixa: "#94a3b8",
};

type ActivityBugQuadrantBarsProps = {
  data: MatrixPoint[];
};

export function ActivityBugQuadrantBars({ data }: ActivityBugQuadrantBarsProps) {
  return (
    <ActivityQuadrantBars
      title="Bugs por quadrante"
      data={data}
      chartData={countBugQuadrants(data)}
      barColors={BAR_COLORS}
      itemLabel={{ one: "bug", many: "bugs" }}
      explanation={BUG_QUADRANT_EXPLANATION}
    />
  );
}
