"use client";

import {
  CartesianGrid,
  Label,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MatrixPoint } from "./mock-matrix-data";

const AXIS_DOMAIN: [number, number] = [-0.35, 5.35];
const AXIS_TICKS = [0, 1, 2, 3, 4, 5];

type ActivityMatrixScatterProps = {
  title: string;
  xLabel: string;
  yLabel: string;
  color: string;
  data: MatrixPoint[];
  emptyMessage: string;
};

type TooltipPayload = {
  payload?: MatrixPoint;
};

function MatrixTooltip({
  active,
  payload,
  xLabel,
  yLabel,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  xLabel: string;
  yLabel: string;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 text-sm shadow-md">
      <p className="font-medium">{point.titulo}</p>
      <p className="text-muted-foreground">
        {xLabel}: {point.x} · {yLabel}: {point.y}
      </p>
    </div>
  );
}

export function ActivityMatrixScatter({
  title,
  xLabel,
  yLabel,
  color,
  data,
  emptyMessage,
}: ActivityMatrixScatterProps) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="py-16 text-center text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <div className="h-[360px] w-full [&_.recharts-cartesian-axis-tick-value]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-border">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 8, right: 12, bottom: 28, left: 4 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="x"
                  domain={AXIS_DOMAIN}
                  ticks={AXIS_TICKS}
                  tickLine={false}
                  axisLine={{ stroke: "var(--border)" }}
                >
                  <Label
                    value={xLabel}
                    position="bottom"
                    offset={8}
                    className="fill-foreground text-sm"
                  />
                </XAxis>
                <YAxis
                  type="number"
                  dataKey="y"
                  domain={AXIS_DOMAIN}
                  ticks={AXIS_TICKS}
                  tickLine={false}
                  axisLine={{ stroke: "var(--border)" }}
                  width={36}
                >
                  <Label
                    value={yLabel}
                    angle={-90}
                    position="insideLeft"
                    offset={12}
                    className="fill-foreground text-sm"
                  />
                </YAxis>
                <Tooltip
                  cursor={{ strokeDasharray: "4 4" }}
                  content={<MatrixTooltip xLabel={xLabel} yLabel={yLabel} />}
                />
                <Scatter data={data} fill={color} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
