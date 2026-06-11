"use client";

import type { MatrixPoint } from "@/lib/priorizacao/types";
import {
  INCREMENT_QUADRANT_BAR_COLORS,
  INCREMENT_QUADRANT_EXPLANATION,
  countIncrementQuadrants,
} from "./matrix-quadrants";
import { ActivityQuadrantBars } from "./activity-quadrant-bars";

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
      barColors={INCREMENT_QUADRANT_BAR_COLORS}
      itemLabel={{ one: "incremento", many: "incrementos" }}
      explanation={INCREMENT_QUADRANT_EXPLANATION}
    />
  );
}
