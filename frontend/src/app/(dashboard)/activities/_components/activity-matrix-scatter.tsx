"use client";

import { Bug, Layers, type LucideIcon } from "lucide-react";
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
import type { MatrixPoint } from "@/lib/priorizacao/types";

const AXIS_DOMAIN: [number, number] = [0, 5];
const AXIS_TICKS = [0, 1, 2, 3, 4, 5];
const CHART_HEIGHT = 380;
const PLOT_INSET = { top: 12, right: 16, bottom: 36, left: 44 };

const QUADRANT_SLOTS = ["topLeft", "topRight", "bottomLeft", "bottomRight"] as const;

type MatrixItemKind = "bug" | "increment";

const ITEM_KIND_STYLES: Record<
  MatrixItemKind,
  { Icon: LucideIcon; iconWrapClass: string; iconClass: string }
> = {
  bug: {
    Icon: Bug,
    iconWrapClass: "bg-red-500/15 ring-red-500/25",
    iconClass: "text-red-400",
  },
  increment: {
    Icon: Layers,
    iconWrapClass: "bg-blue-500/15 ring-blue-500/25",
    iconClass: "text-blue-400",
  },
};

type ActivityMatrixScatterProps = {
  title: string;
  xLabel: string;
  yLabel: string;
  color: string;
  data: MatrixPoint[];
  emptyMessage: string;
  quadrants: MatrixQuadrantConfig;
  itemKind: MatrixItemKind;
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
  accentColor,
  itemKind,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  xLabel: string;
  yLabel: string;
  accentColor: string;
  itemKind: MatrixItemKind;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  const { Icon, iconWrapClass, iconClass } = ITEM_KIND_STYLES[itemKind];

  return (
    <div
      className="relative isolate max-w-[min(calc(100vw-2rem),18rem)] overflow-hidden rounded-2xl border border-white/20 bg-background/45 shadow-[0_8px_32px_rgba(0,0,0,0.45)] ring-1 ring-white/10 backdrop-blur-2xl backdrop-saturate-150 sm:max-w-xs"
      style={{ borderLeftWidth: 3, borderLeftColor: accentColor }}
    >
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/14 via-white/5 to-white/[0.02]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-x-3 top-0 h-px bg-gradient-to-r from-transparent via-white/35 to-transparent"
        aria-hidden
      />

      <div className="relative z-10 max-h-40 space-y-0 overflow-y-auto overscroll-contain px-3 py-2.5 sm:max-h-48 sm:px-3.5 sm:py-3">
        {point.titulos.map((titulo, index) => (
          <div
            key={`${titulo}-${index}`}
            className={cn(
              "flex gap-2.5",
              index > 0 && "mt-2.5 border-t border-white/15 pt-2.5",
            )}
          >
            <div
              className={cn(
                "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-background/50 ring-1 ring-inset backdrop-blur-sm",
                iconWrapClass,
              )}
              aria-hidden
            >
              <Icon className={cn("size-3.5", iconClass)} />
            </div>
            <p className="min-w-0 flex-1 text-sm font-semibold leading-snug tracking-tight text-foreground drop-shadow-sm">
              {titulo}
            </p>
          </div>
        ))}
      </div>

      <div className="relative z-10 flex flex-wrap gap-1.5 border-t border-white/15 bg-background/55 px-3 py-2 backdrop-blur-md sm:px-3.5">
        <span className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-background/70 px-2 py-0.5 text-[11px] shadow-sm backdrop-blur-sm sm:text-xs">
          <span className="text-muted-foreground">{xLabel}</span>
          <span className="font-semibold tabular-nums text-foreground">{point.x}</span>
        </span>
        <span className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-background/70 px-2 py-0.5 text-[11px] shadow-sm backdrop-blur-sm sm:text-xs">
          <span className="text-muted-foreground">{yLabel}</span>
          <span className="font-semibold tabular-nums text-foreground">{point.y}</span>
        </span>
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
  itemKind,
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
                    wrapperStyle={{ outline: "none", zIndex: 50 }}
                    contentStyle={{
                      background: "transparent",
                      border: "none",
                      padding: 0,
                      boxShadow: "none",
                    }}
                    content={
                      <MatrixTooltip
                        xLabel={xLabel}
                        yLabel={yLabel}
                        accentColor={color}
                        itemKind={itemKind}
                      />
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
