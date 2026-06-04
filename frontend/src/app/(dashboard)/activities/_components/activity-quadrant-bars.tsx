"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Label,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MatrixPoint } from "@/lib/priorizacao/types";
import { QuadrantLegend, type QuadrantExplanationRow } from "./quadrant-explanation-table";
import { DashboardPanel, DashboardPanelHeader } from "./dashboard-panel";

export type QuadrantBarRow = {
  quadrante: string;
  quantidade: number;
};

type ActivityQuadrantBarsProps = {
  title: string;
  data: MatrixPoint[];
  chartData: QuadrantBarRow[];
  barColors: Record<string, string>;
  itemLabel: { one: string; many: string };
  explanation: {
    axisHint: string;
    rows: QuadrantExplanationRow[];
  };
};

export function ActivityQuadrantBars({
  title,
  data,
  chartData,
  barColors,
  itemLabel,
  explanation,
}: ActivityQuadrantBarsProps) {
  const maxCount = Math.max(1, ...chartData.map((d) => d.quantidade));
  const yAxisLabel = `Quantidade de ${itemLabel.many}`;

  const { colorByName, displayNameByQuadrante } = useMemo(() => {
    const colors: Record<string, string> = {};
    const labels: Record<string, string> = {};
    for (const row of explanation.rows) {
      const match = chartData.find(
        (entry) => entry.quadrante.toLowerCase() === row.nome.toLowerCase(),
      );
      if (match) {
        labels[match.quadrante] = row.nome;
        colors[row.nome] = barColors[match.quadrante] ?? "#64748b";
      }
    }
    for (const entry of chartData) {
      if (!labels[entry.quadrante]) {
        labels[entry.quadrante] = entry.quadrante;
      }
    }
    return { colorByName: colors, displayNameByQuadrante: labels };
  }, [chartData, explanation.rows, barColors]);

  return (
    <DashboardPanel>
      <DashboardPanelHeader title={title} />
      <div className="p-4 sm:p-5">
        {data.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            Sem dados para exibir a distribuição por quadrante.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(8.5rem,10.5rem)] lg:items-center lg:gap-4">
            <div className="min-h-[280px] min-w-0 [&_.recharts-cartesian-axis-tick-value]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-white/10 [&_.recharts-label]:fill-muted-foreground">
              <ResponsiveContainer width="100%" height={288}>
                <BarChart
                  data={chartData}
                  margin={{ top: 8, right: 12, bottom: 28, left: 8 }}
                  barCategoryGap="56%"
                >
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.08)" />
                  <XAxis
                    dataKey="quadrante"
                    tickLine={false}
                    axisLine={{ stroke: "rgba(255,255,255,0.15)" }}
                    interval={0}
                    height={56}
                    tickFormatter={(value) => displayNameByQuadrante[String(value)] ?? String(value)}
                    tick={{
                      fontSize: 10,
                      angle: -25,
                      textAnchor: "end",
                      dy: 4,
                    }}
                  />
                  <YAxis
                    allowDecimals={false}
                    domain={[0, maxCount]}
                    tickLine={false}
                    axisLine={{ stroke: "rgba(255,255,255,0.15)" }}
                    width={36}
                    tick={{ fontSize: 11 }}
                  >
                    <Label
                      value={yAxisLabel}
                      angle={-90}
                      position="insideLeft"
                      offset={12}
                      className="fill-muted-foreground text-[11px]"
                      style={{ textAnchor: "middle" }}
                    />
                  </YAxis>
                  <Tooltip
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const row = payload[0]?.payload as QuadrantBarRow;
                      const noun = row.quantidade === 1 ? itemLabel.one : itemLabel.many;
                      return (
                        <div className="rounded-lg border border-white/10 bg-card/95 px-3 py-2 text-sm shadow-lg backdrop-blur-sm">
                          <p className="font-medium capitalize">{row.quadrante}</p>
                          <p className="text-muted-foreground">
                            {row.quantidade} {noun}
                          </p>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="quantidade" radius={[6, 6, 0, 0]} maxBarSize={44} barSize={36}>
                    {chartData.map((entry) => (
                      <Cell
                        key={entry.quadrante}
                        fill={barColors[entry.quadrante] ?? "#64748b"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="min-w-0 pt-4 lg:pt-0">
              <QuadrantLegend
                layout="sidebar"
                axisHint={explanation.axisHint}
                rows={explanation.rows}
                colorByName={colorByName}
              />
            </div>
          </div>
        )}
      </div>
    </DashboardPanel>
  );
}
