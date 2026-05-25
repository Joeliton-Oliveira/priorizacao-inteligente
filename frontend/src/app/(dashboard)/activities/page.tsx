"use client";

import { ActivityMatricesGrid } from "./_components/activity-matrices-grid";
import {
  ActivitySummaryCards,
  type ActivitySummaryStats,
} from "./_components/activity-summary-cards";
import {
  MOCK_BUGS_MATRIX,
  MOCK_INCREMENTS_MATRIX,
} from "./_components/mock-matrix-data";

/** Valores de exemplo até integração com a API de atividades. */
const MOCK_SUMMARY: ActivitySummaryStats = {
  bugs: MOCK_BUGS_MATRIX.length,
  incrementos: MOCK_INCREMENTS_MATRIX.length,
  concluidas: 0,
  pendentesVisao: MOCK_BUGS_MATRIX.length + MOCK_INCREMENTS_MATRIX.length,
};

export default function ActivitiesPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Matrizes de Atividades</h1>

      <ActivitySummaryCards stats={MOCK_SUMMARY} />

      <ActivityMatricesGrid />
    </div>
  );
}
