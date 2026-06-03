"use client";

import type { MatrixPoint } from "./mock-matrix-data";
import {
  BUG_QUADRANT_BAR_COLORS,
  BUG_QUADRANT_EXPLANATION,
  countBugQuadrants,
} from "./matrix-quadrants";
import { ActivityQuadrantBars } from "./activity-quadrant-bars";

type ActivityBugQuadrantBarsProps = {
  data: MatrixPoint[];
};

export function ActivityBugQuadrantBars({ data }: ActivityBugQuadrantBarsProps) {
  return (
    <ActivityQuadrantBars
      title="Bugs por quadrante"
      data={data}
      chartData={countBugQuadrants(data)}
      barColors={BUG_QUADRANT_BAR_COLORS}
      itemLabel={{ one: "bug", many: "bugs" }}
      explanation={BUG_QUADRANT_EXPLANATION}
    />
  );
}
