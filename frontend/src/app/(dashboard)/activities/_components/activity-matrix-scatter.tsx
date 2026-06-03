"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Label,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import { QUADRANT_CUTOFF } from "./matrix-quadrants";
import type { MatrixQuadrantConfig } from "./matrix-chart-quadrants";
import { DashboardPanel, DashboardPanelHeader } from "./dashboard-panel";
import type { MatrixPoint } from "./mock-matrix-data";

const AXIS_DOMAIN: [number, number] = [0, 5];
const AXIS_TICKS = [0, 1, 2, 3, 4, 5];
const CHART_HEIGHT = 380;
const PLOT_INSET = { top: 12, right: 16, bottom: 36, left: 44 };

const QUADRANT_SLOTS = ["topLeft", "topRight", "bottomLeft", "bottomRight"] as const;

type ActivityMatrixScatterProps = {
  title: string;
  xLabel: string;
  yLabel: string;
  color: string;
  data: MatrixPoint[];
  emptyMessage: string;
  quadrants: MatrixQuadrantConfig;
  itemLabel: {
    singular: string;
    plural: string;
  };
};

type TooltipPayload = {
  payload?: ScatterPoint;
};

type ScatterPoint = MatrixPoint & {
  duplicateCount: number;
  titulos: string[];
};

function getPointRadius(duplicateCount: number) {
  return 6 + Math.sqrt(Math.max(duplicateCount - 1, 0)) * 4;
}

function MatrixTooltip({
  active,
  payload,
  xLabel,
  yLabel,
  itemLabel,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  xLabel: string;
  yLabel: string;
  itemLabel: { singular: string; plural: string };
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="rounded-lg border border-white/10 bg-card/95 px-3 py-2 text-sm shadow-xl backdrop-blur-sm">
      <p className="font-medium">
        {point.duplicateCount}{" "}
        {point.duplicateCount > 1 ? itemLabel.plural : itemLabel.singular} neste ponto
      </p>
      <p className="text-muted-foreground">
        {xLabel}: {point.x} · {yLabel}: {point.y}
      </p>
      <div className="mt-2 max-h-32 space-y-1 overflow-y-auto">
        {point.titulos.map((titulo) => (
          <p key={titulo} className="text-xs text-muted-foreground">
            · {titulo}
          </p>
        ))}
      </div>
    </div>
  );
}

function MatrixQuadrantOverlay({ quadrants }: { quadrants: MatrixQuadrantConfig }) {
  return (
    <div
      className="pointer-events-none absolute z-10 grid grid-cols-2 grid-rows-2"
      style={{
        top: PLOT_INSET.top,
        right: PLOT_INSET.right,
        bottom: PLOT_INSET.bottom,
        left: PLOT_INSET.left,
      }}
    >
      {QUADRANT_SLOTS.map((slot) => {
        const quadrant = quadrants[slot];
        return (
          <div key={slot} className="flex items-center justify-center p-1 sm:p-1.5">
            <span
              className={cn(
                "max-w-[92%] rounded border px-1 py-0.5 text-center text-[8px] leading-tight font-medium sm:max-w-[85%] sm:px-1.5 sm:py-1 sm:text-[9px]",
                quadrant.textClass,
                quadrant.borderClass,
                quadrant.bgClass,
              )}
            >
              {quadrant.label}
            </span>
          </div>
        );
      })}
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
  quadrants,
  itemLabel,
}: ActivityMatrixScatterProps) {
  const scatterData = useMemo(() => {
    const grouped = new Map<string, ScatterPoint>();

    for (const point of data) {
      const key = `${point.x}|${point.y}`;
      const existing = grouped.get(key);

      if (existing) {
        existing.duplicateCount += 1;
        existing.titulos.push(point.titulo);
        continue;
      }

      grouped.set(key, {
        ...point,
        duplicateCount: 1,
        titulos: [point.titulo],
      });
    }

    return Array.from(grouped.values());
  }, [data]);

  const isEmpty = scatterData.length === 0;

  return (
    <DashboardPanel>
      <DashboardPanelHeader title={title} />
      <div className="px-3 pb-4 pt-2 sm:px-4">
        <div className="relative w-full" style={{ height: CHART_HEIGHT }}>
          <MatrixQuadrantOverlay quadrants={quadrants} />
          {isEmpty ? (
            <div
              className="absolute z-20 flex items-center justify-center"
              style={{
                top: PLOT_INSET.top,
                right: PLOT_INSET.right,
                bottom: PLOT_INSET.bottom,
                left: PLOT_INSET.left,
              }}
            >
              <p className="rounded-lg border border-white/10 bg-background/90 px-4 py-2 text-center text-sm text-muted-foreground backdrop-blur-sm">
                {emptyMessage}
              </p>
            </div>
          ) : null}
          <div className="h-full w-full [&_.recharts-cartesian-axis-tick-value]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-white/10">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart
                margin={{
                  top: PLOT_INSET.top,
                  right: PLOT_INSET.right,
                  bottom: PLOT_INSET.bottom,
                  left: PLOT_INSET.left,
                }}
              >
                <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.1)" />
                <ReferenceLine
                  x={QUADRANT_CUTOFF}
                  stroke="rgba(255,255,255,0.32)"
                  strokeDasharray="6 4"
                  strokeWidth={1.5}
                />
                <ReferenceLine
                  y={QUADRANT_CUTOFF}
                  stroke="rgba(255,255,255,0.32)"
                  strokeDasharray="6 4"
                  strokeWidth={1.5}
                />
                <XAxis
                  type="number"
                  dataKey="x"
                  domain={AXIS_DOMAIN}
                  ticks={AXIS_TICKS}
                  tickLine={false}
                  axisLine={{ stroke: "rgba(255,255,255,0.18)" }}
                >
                  <Label
                    value={xLabel}
                    position="bottom"
                    offset={4}
                    className="fill-foreground text-xs font-medium"
                  />
                </XAxis>
                <YAxis
                  type="number"
                  dataKey="y"
                  domain={AXIS_DOMAIN}
                  ticks={AXIS_TICKS}
                  tickLine={false}
                  axisLine={{ stroke: "rgba(255,255,255,0.18)" }}
                  width={40}
                >
                  <Label
                    value={yLabel}
                    angle={-90}
                    position="insideLeft"
                    offset={8}
                    className="fill-foreground text-xs font-medium"
                  />
                </YAxis>
                {!isEmpty ? (
                  <Tooltip
                    cursor={{ strokeDasharray: "4 4", stroke: "rgba(255,255,255,0.25)" }}
                    content={
                      <MatrixTooltip xLabel={xLabel} yLabel={yLabel} itemLabel={itemLabel} />
                    }
                  />
                ) : null}
                <Scatter
                  data={isEmpty ? [] : scatterData}
                  fill={color}
                  shape={({ cx, cy, payload }) => {
                    if (typeof cx !== "number" || typeof cy !== "number" || !payload) return null;
                    const point = payload as ScatterPoint;

                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={getPointRadius(point.duplicateCount)}
                        fill={color}
                        fillOpacity={0.95}
                        stroke={color}
                        strokeWidth={2}
                      />
                    );
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </DashboardPanel>
  );
}
