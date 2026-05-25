"use client";

import type { MatrixPoint } from "./mock-matrix-data";
import {
  INCREMENT_QUADRANT_EXPLANATION,
  countIncrementQuadrants,
} from "./matrix-quadrants";
import { ActivityQuadrantBars } from "./activity-quadrant-bars";

const BAR_COLORS: Record<string, string> = {
  "quick wins": "#1d4ed8",
  "grandes projetos": "#2563eb",
  preenchimento: "#60a5fa",
  desperdício: "#94a3b8",
};

type ActivityIncrementQuadrantBarsProps = {
  data: MatrixPoint[];
};

export function ActivityIncrementQuadrantBars({
  data,
}: ActivityIncrementQuadrantBarsProps) {
  return (
    <ActivityQuadrantBars
      title="Incrementos por quadrante"
      data={data}
      chartData={countIncrementQuadrants(data)}
      barColors={BAR_COLORS}
      itemLabel={{ one: "incremento", many: "incrementos" }}
      explanation={INCREMENT_QUADRANT_EXPLANATION}
    />
  );
}
