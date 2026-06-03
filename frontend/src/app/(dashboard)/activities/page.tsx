"use client";

import { useEffect, useMemo, useState } from "react";
import { ActivitiesPageHeader } from "./_components/activities-page-header";
import { ActivitySummaryCards } from "./_components/activity-summary-cards";
import { ActivityMatrixScatter } from "./_components/activity-matrix-scatter";
import { ActivityBugQuadrantBars } from "./_components/activity-bug-quadrant-bars";
import { ActivityIncrementQuadrantBars } from "./_components/activity-increment-quadrant-bars";
import {
  BUG_MATRIX_QUADRANTS,
  INCREMENT_MATRIX_QUADRANTS,
} from "./_components/matrix-chart-quadrants";
import type { AtividadePriorizada, MatrixPoint } from "@/lib/priorizacao/types";

const DONE_STATUSES = new Set(["DONE", "CONCLUIDO"]);

function toMatrixPoint(item: AtividadePriorizada): MatrixPoint {
  return {
    x: item.coordenada_x,
    y: item.coordenada_y,
    titulo: item.titulo,
  };
}

export default function ActivitiesPage() {
  const [items, setItems] = useState<AtividadePriorizada[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadActivities() {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        const response = await fetch("/api/priorizacao/atividades", { cache: "no-store" });
        const data = await response.json().catch(() => []);
        if (!response.ok) {
          throw new Error(
            data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
              ? data.detail
              : "Não foi possível carregar as atividades.",
          );
        }
        if (!cancelled) {
          setItems(Array.isArray(data) ? (data as AtividadePriorizada[]) : []);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Não foi possível carregar as atividades.",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadActivities();

    return () => {
      cancelled = true;
    };
  }, []);

  const bugPoints = useMemo(
    () => items.filter((item) => item.tipo_requisito === "BUG").map(toMatrixPoint),
    [items],
  );
  const incrementPoints = useMemo(
    () => items.filter((item) => item.tipo_requisito !== "BUG").map(toMatrixPoint),
    [items],
  );

  const stats = useMemo(
    () => ({
      bugs: items.filter((item) => item.tipo_requisito === "BUG").length,
      incrementos: items.filter((item) => item.tipo_requisito !== "BUG").length,
      concluidas: items.filter((item) =>
        DONE_STATUSES.has((item.status_atual || "").toUpperCase()),
      ).length,
      pendentesVisao: items.filter(
        (item) => !DONE_STATUSES.has((item.status_atual || "").toUpperCase()),
      ).length,
    }),
    [items],
  );

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-6 pb-8">
      <ActivitiesPageHeader />

      {errorMessage ? (
        <p className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-red-400">
          {errorMessage}
        </p>
      ) : null}

      <ActivitySummaryCards stats={stats} />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:gap-6">
        <ActivityMatrixScatter
          title="Matriz de BUGs"
          xLabel="Criticidade"
          yLabel="Severidade"
          color="#ef4444"
          data={bugPoints}
          quadrants={BUG_MATRIX_QUADRANTS}
          emptyMessage={isLoading ? "Carregando matriz..." : "Nenhum bug encontrado."}
          itemLabel={{ singular: "bug", plural: "bugs" }}
        />
        <ActivityMatrixScatter
          title="Matriz de INCREMENTOs"
          xLabel="Esforço"
          yLabel="Valor"
          color="#3b82f6"
          data={incrementPoints}
          quadrants={INCREMENT_MATRIX_QUADRANTS}
          emptyMessage={isLoading ? "Carregando matriz..." : "Nenhum incremento encontrado."}
          itemLabel={{ singular: "incremento", plural: "incrementos" }}
        />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:gap-6">
        <ActivityBugQuadrantBars data={bugPoints} />
        <ActivityIncrementQuadrantBars data={incrementPoints} />
      </div>
    </div>
  );
}
