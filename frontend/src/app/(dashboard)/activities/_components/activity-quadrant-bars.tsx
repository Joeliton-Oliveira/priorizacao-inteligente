"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MatrixPoint } from "./mock-matrix-data";
import {
  QuadrantExplanationTable,
  type QuadrantExplanationRow,
} from "./quadrant-explanation-table";

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

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Sem dados para exibir a distribuição por quadrante.
          </p>
        ) : (
          <div className="h-[220px] w-full [&_.recharts-cartesian-axis-tick-value]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-border">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 8, right: 12, bottom: 8, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="quadrante"
                  tickLine={false}
                  axisLine={{ stroke: "var(--border)" }}
                  interval={0}
                  tick={{ fontSize: 11 }}
                />
                <YAxis
                  allowDecimals={false}
                  domain={[0, maxCount]}
                  tickLine={false}
                  axisLine={{ stroke: "var(--border)" }}
                  width={32}
                />
                <Tooltip
                  cursor={{ fill: "var(--muted)", opacity: 0.4 }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const row = payload[0]?.payload as QuadrantBarRow;
                    const noun =
                      row.quantidade === 1 ? itemLabel.one : itemLabel.many;
                    return (
                      <div className="rounded-lg border bg-card px-3 py-2 text-sm shadow-md">
                        <p className="font-medium">{row.quadrante}</p>
                        <p className="text-muted-foreground">
                          {row.quantidade} {noun}
                        </p>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="quantidade" radius={[4, 4, 0, 0]} maxBarSize={48} barSize={40}>
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
        )}
        <QuadrantExplanationTable
          axisHint={explanation.axisHint}
          rows={explanation.rows}
        />
      </CardContent>
    </Card>
  );
}
