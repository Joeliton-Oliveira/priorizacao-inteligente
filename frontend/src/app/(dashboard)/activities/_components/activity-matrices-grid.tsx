"use client";

import { useEffect, useState } from "react";
import { ActivityBugQuadrantBars } from "./activity-bug-quadrant-bars";
import { ActivityIncrementQuadrantBars } from "./activity-increment-quadrant-bars";
import { ActivityMatrixScatter } from "./activity-matrix-scatter";
import {
  MOCK_BUGS_MATRIX,
  MOCK_INCREMENTS_MATRIX,
  type MatrixPoint,
} from "./mock-matrix-data";
import { splitUserMatrixPoints } from "@/lib/priorizacao/matrix-points-storage";

export function ActivityMatricesGrid() {
  const [bugs, setBugs] = useState<MatrixPoint[]>(MOCK_BUGS_MATRIX);
  const [incrementos, setIncrementos] = useState<MatrixPoint[]>(
    MOCK_INCREMENTS_MATRIX,
  );

  useEffect(() => {
    const user = splitUserMatrixPoints();
    setBugs([...MOCK_BUGS_MATRIX, ...user.bugs]);
    setIncrementos([...MOCK_INCREMENTS_MATRIX, ...user.incrementos]);
  }, []);

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div className="flex flex-col gap-4">
        <ActivityMatrixScatter
          title="Matriz de BUGs"
          xLabel="Criticidade"
          yLabel="Severidade"
          color="#dc2626"
          data={bugs}
          emptyMessage="Nenhum bug na seleção atual (ajuste os filtros)."
        />
        <ActivityBugQuadrantBars data={bugs} />
      </div>
      <div className="flex flex-col gap-4">
        <ActivityMatrixScatter
          title="Matriz de INCREMENTOs"
          xLabel="Esforco"
          yLabel="Valor"
          color="#2563eb"
          data={incrementos}
          emptyMessage="Nenhum incremento na seleção atual (ajuste os filtros)."
        />
        <ActivityIncrementQuadrantBars data={incrementos} />
      </div>
    </div>
  );
}
