"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Bug, ExternalLink, ListFilter, Package } from "lucide-react";
import { DashboardPanel } from "@/app/(dashboard)/activities/_components/dashboard-panel";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  classifyBugQuadrant,
  classifyIncrementQuadrant,
  getQuadrantBadgeClassName,
} from "@/app/(dashboard)/activities/_components/matrix-quadrants";
import { cn } from "@/lib/utils";
import type { FilaItem } from "@/lib/priorizacao/types";

type QueueVariant = "all" | "BUG" | "INCREMENTO";
type QueueAccent = "bug" | "increment";

const FILA_ORDER_TOOLTIP =
  "1º quadrante (corte 2,5); 2º distância ao ponto ideal daquele quadrante; 3º eixos (valor/esforço ou severidade/criticidade). Score não define a posição.";

const BUG_QUEUE_DESCRIPTION =
  "Criticidade × Severidade. Quadrantes Crítica-alta → Baixa; dentro de cada um, proximidade ao ideal do quadrante e maior severidade/criticidade.";

const INCREMENT_QUEUE_DESCRIPTION =
  "Esforço × Valor. Ganhos rápidos → Grandes projetos → Melhorias simples → Baixo retorno; dentro de cada quadrante, posição mais favorável (ex.: em Ganhos rápidos, maior valor e menor esforço).";

const INCREMENT_ORDER_LEGEND =
  "Quadrantes: 1 Ganhos rápidos → 2 Grandes projetos → 3 Melhorias simples → 4 Baixo retorno. Dentro de cada um: distância ao ideal do quadrante (Ganhos rápidos: alto valor e baixo esforço).";

const BUG_ORDER_LEGEND =
  "Quadrantes: 1 Crítica-alta → 2 Alta-média → 3 Média → 4 Baixa. Dentro de cada um: distância ao ideal do quadrante (maior criticidade e severidade).";


const SCORE_REF_TOOLTIP =
  "Score = eixo X × eixo Y (matriz de Atividades). Um score maior não empurra o item para cima se o quadrante ou a distância ao ideal do quadrante forem piores.";

const FILA_CONTEXT_NOTE =
  "Posição definida por quadrante (corte 2,5) e distância ao ideal daquele quadrante. Score, faixa e prioridade categórica são só referência.";

const QUADRANTE_TOOLTIP =
  "Quadrante da matriz (corte 2,5). Este é o 1º critério de ordenação da fila.";

const ORDEM_Q_TOOLTIP = "Prioridade do quadrante na fila (1 = mais urgente no tipo).";

type PriorityQueueViewProps = {
  variant: QueueVariant;
};

function formatNumber(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

function normalizeKey(value?: string | null) {
  return (value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .trim();
}

function getTypeBadgeClass(type?: string | null) {
  const normalized = normalizeKey(type);
  if (normalized === "BUG") return "border-rose-500/35 bg-rose-500/15 text-rose-300";
  return "border-blue-500/35 bg-blue-500/15 text-blue-300";
}

function getScoreClass(faixa?: string | null, score?: number) {
  const normalized = normalizeKey(faixa);
  if (normalized === "ALTA") return "font-bold tabular-nums text-rose-400";
  if (normalized === "MEDIA") return "font-semibold tabular-nums text-amber-300";
  if (normalized === "BAIXA") return "font-semibold tabular-nums text-emerald-400";

  if (typeof score === "number" && !Number.isNaN(score)) {
    if (score >= 12) return "font-bold tabular-nums text-rose-400";
    if (score >= 7) return "font-semibold tabular-nums text-amber-300";
    return "font-semibold tabular-nums text-emerald-400";
  }

  return "font-medium tabular-nums text-muted-foreground";
}

function resolveQuadrantLabel(item: FilaItem, accent: QueueAccent): string {
  if (item.fila_quadrante_nome) return item.fila_quadrante_nome;
  const x = item.coordenada_x ?? 0;
  const y = item.coordenada_y ?? 0;
  if (accent === "bug") return classifyBugQuadrant(x, y);
  return classifyIncrementQuadrant(x, y);
}

function axisLabels(accent: QueueAccent) {
  if (accent === "bug") {
    return { x: "Criticidade", y: "Severidade" };
  }
  return { x: "Esforço", y: "Valor" };
}

function resolveQuadrantOrder(item: FilaItem, accent: QueueAccent): number {
  if (typeof item.fila_ordem_quadrante === "number") return item.fila_ordem_quadrante;
  const x = item.coordenada_x ?? 0;
  const y = item.coordenada_y ?? 0;
  if (accent === "bug") {
    const t = 2.5;
    if (x > t && y > t) return 1;
    if (x > t && y <= t) return 2;
    if (x <= t && y > t) return 3;
    return 4;
  }
  const t = 2.5;
  if (x <= t && y > t) return 1;
  if (x > t && y > t) return 2;
  if (x <= t && y <= t) return 3;
  return 4;
}

function ColumnHeader({
  label,
  tooltip,
  align = "left",
}: {
  label: string;
  tooltip?: string;
  align?: "left" | "right" | "center";
}) {
  const className = cn(
    "text-xs font-semibold uppercase tracking-wide text-muted-foreground",
    align === "right" && "text-right",
    align === "center" && "text-center",
  );
  if (!tooltip) {
    return <span className={className}>{label}</span>;
  }
  return (
    <Tooltip>
      <TooltipTrigger
        className={cn(
          className,
          "cursor-help underline decoration-dotted underline-offset-2",
        )}
      >
        {label}
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
        {tooltip}
      </TooltipContent>
    </Tooltip>
  );
}

function Badge({ className, children }: { className: string; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center justify-center rounded-md border px-2 py-0.5 text-[11px] font-semibold leading-tight",
        className,
      )}
    >
      {children}
    </span>
  );
}

function QueueSection({
  accent,
  title,
  description,
  orderLegend,
  items,
  isLoading,
}: {
  accent: QueueAccent;
  title: string;
  description: string;
  orderLegend: string;
  items: FilaItem[];
  isLoading: boolean;
}) {
  const isBug = accent === "bug";
  const Icon = isBug ? Bug : Package;
  const axes = axisLabels(accent);
  const colSpan = 11;

  return (
    <DashboardPanel
      className={cn(
        "overflow-hidden",
        isBug
          ? "border-rose-500/15 shadow-rose-950/10"
          : "border-blue-500/15 shadow-blue-950/10",
      )}
    >
      <div
        className={cn(
          "flex flex-col gap-1 border-b px-5 py-4 sm:flex-row sm:items-start sm:justify-between",
          isBug
            ? "border-rose-500/10 bg-gradient-to-r from-rose-500/[0.06] to-transparent"
            : "border-blue-500/10 bg-gradient-to-r from-blue-500/[0.06] to-transparent",
        )}
      >
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "flex size-10 shrink-0 items-center justify-center rounded-xl ring-1",
              isBug
                ? "bg-rose-500/15 text-rose-300 ring-rose-500/25"
                : "bg-blue-500/15 text-blue-300 ring-blue-500/25",
            )}
          >
            <Icon className="size-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold tracking-tight">{title}</h2>
            <p className="mt-0.5 max-w-2xl text-sm text-muted-foreground">{description}</p>
            <p className="mt-1.5 max-w-3xl text-xs text-muted-foreground/90">{orderLegend}</p>
            <p className="mt-1 max-w-3xl text-xs text-sky-300/80">{FILA_CONTEXT_NOTE}</p>
          </div>
        </div>
        <p className="text-xs font-medium text-muted-foreground sm:pt-2">
          {isLoading ? "Carregando…" : `${items.length} ${items.length === 1 ? "item" : "itens"}`}
        </p>
      </div>

      <div className="p-4 sm:p-5">
        <div className="overflow-x-auto rounded-xl border border-white/10">
          <Table className="min-w-[1100px]">
            <TableHeader>
              <TableRow className="border-white/10 bg-white/[0.03] hover:bg-white/[0.03]">
                <TableHead className="w-12">
                  <ColumnHeader label="Pos." tooltip={FILA_ORDER_TOOLTIP} />
                </TableHead>
                <TableHead className="w-14">
                  <ColumnHeader label="ID" />
                </TableHead>
                <TableHead className="min-w-[200px]">
                  <ColumnHeader label="Título" />
                </TableHead>
                <TableHead className="w-12 text-center">
                  <ColumnHeader label="Ordem Q" tooltip={ORDEM_Q_TOOLTIP} align="center" />
                </TableHead>
                <TableHead className="w-32">
                  <ColumnHeader label="Quadrante" tooltip={QUADRANTE_TOOLTIP} />
                </TableHead>
                <TableHead className="w-20 text-right">
                  <ColumnHeader label={axes.x} align="right" />
                </TableHead>
                <TableHead className="w-20 text-right">
                  <ColumnHeader label={axes.y} align="right" />
                </TableHead>
                <TableHead className="w-24">
                  <ColumnHeader label="Tipo" />
                </TableHead>
                <TableHead className="w-24 text-right">
                  <ColumnHeader label="Score (ref.)" tooltip={SCORE_REF_TOOLTIP} align="right" />
                </TableHead>
                <TableHead className="w-20 text-center">
                  <ColumnHeader label="Dias parado" align="center" />
                </TableHead>
                <TableHead className="w-24 text-right">
                  <ColumnHeader label="Detalhe" align="right" />
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={colSpan} className="py-10 text-center text-sm text-muted-foreground">
                    Carregando fila...
                  </TableCell>
                </TableRow>
              ) : items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={colSpan} className="py-10 text-center text-sm text-muted-foreground">
                    Nenhum item nesta fila.
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item, index) => {
                  const ordemQ = resolveQuadrantOrder(item, accent);
                  const quadranteLabel = resolveQuadrantLabel(item, accent);

                  return (
                    <TableRow
                      key={item.id}
                      className="border-white/10 transition-colors hover:bg-white/[0.04]"
                    >
                      <TableCell className="tabular-nums text-muted-foreground">
                        {index + 1}
                      </TableCell>
                      <TableCell className="font-medium tabular-nums">{item.id}</TableCell>
                      <TableCell className="max-w-[340px]">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="block truncate font-medium leading-relaxed">
                              {item.titulo}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-sm text-xs leading-relaxed">
                            {item.titulo}
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell className="text-center tabular-nums font-medium text-muted-foreground">
                        {ordemQ}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={getQuadrantBadgeClassName(
                            accent === "bug" ? "bug" : "increment",
                            quadranteLabel,
                            ordemQ,
                          )}
                        >
                          {quadranteLabel}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {formatNumber(item.coordenada_x)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {formatNumber(item.coordenada_y)}
                      </TableCell>
                      <TableCell>
                        <Badge className={getTypeBadgeClass(item.tipo_requisito)}>
                          {item.tipo_requisito}
                        </Badge>
                      </TableCell>
                      <TableCell className={getScoreClass(item.faixa, item.score_final)}>
                        {formatNumber(item.score_final)}
                      </TableCell>
                      <TableCell className="text-center tabular-nums text-muted-foreground">
                        {typeof item.dias_parado === "number" ? item.dias_parado : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          asChild
                          size="sm"
                          variant="outline"
                          className="h-8 rounded-lg border-violet-500/30 bg-violet-500/10 text-violet-200 hover:bg-violet-500/20 hover:text-violet-100"
                        >
                          <Link href={`/kanban/list/${item.id}`}>
                            <ExternalLink className="size-3.5" />
                            Abrir
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </DashboardPanel>
  );
}

export function PriorityQueueView({ variant }: PriorityQueueViewProps) {
  const [bugs, setBugs] = useState<FilaItem[]>([]);
  const [incrementos, setIncrementos] = useState<FilaItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadQueues() {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        const [bugsResponse, incrementsResponse] = await Promise.all([
          fetch("/api/priorizacao/fila/bugs", { cache: "no-store" }),
          fetch("/api/priorizacao/fila/incrementos", { cache: "no-store" }),
        ]);
        const [bugsData, incrementsData] = await Promise.all([
          bugsResponse.json().catch(() => []),
          incrementsResponse.json().catch(() => []),
        ]);

        if (!bugsResponse.ok) {
          throw new Error(
            bugsData &&
              typeof bugsData === "object" &&
              "detail" in bugsData &&
              typeof bugsData.detail === "string"
              ? bugsData.detail
              : "Não foi possível carregar a fila de bugs.",
          );
        }
        if (!incrementsResponse.ok) {
          throw new Error(
            incrementsData &&
              typeof incrementsData === "object" &&
              "detail" in incrementsData &&
              typeof incrementsData.detail === "string"
              ? incrementsData.detail
              : "Não foi possível carregar a fila de incrementos.",
          );
        }

        if (!cancelled) {
          setBugs(Array.isArray(bugsData) ? (bugsData as FilaItem[]) : []);
          setIncrementos(Array.isArray(incrementsData) ? (incrementsData as FilaItem[]) : []);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Não foi possível carregar a fila.",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadQueues();

    return () => {
      cancelled = true;
    };
  }, []);

  const sections = useMemo(() => {
    if (variant === "BUG") {
      return [
        {
          key: "bugs",
          accent: "bug" as const,
          title: "Fila de bugs",
          description: BUG_QUEUE_DESCRIPTION,
          orderLegend: BUG_ORDER_LEGEND,
          items: bugs,
        },
      ];
    }

    if (variant === "INCREMENTO") {
      return [
        {
          key: "incrementos",
          accent: "increment" as const,
          title: "Fila de incrementos",
          description: INCREMENT_QUEUE_DESCRIPTION,
          orderLegend: INCREMENT_ORDER_LEGEND,
          items: incrementos,
        },
      ];
    }

    return [
      {
        key: "bugs",
        accent: "bug" as const,
        title: "Fila de bugs",
        description: BUG_QUEUE_DESCRIPTION,
        orderLegend: BUG_ORDER_LEGEND,
        items: bugs,
      },
      {
        key: "incrementos",
        accent: "increment" as const,
        title: "Fila de incrementos",
        description: INCREMENT_QUEUE_DESCRIPTION,
        orderLegend: INCREMENT_ORDER_LEGEND,
        items: incrementos,
      },
    ];
  }, [bugs, incrementos, variant]);

  const pageTitle =
    variant === "BUG"
      ? "Filas — Bug"
      : variant === "INCREMENTO"
        ? "Filas — Incremento"
        : "Fila de priorização";

  const pageSubtitle =
    "Ordenação por quadrante da matriz (corte 2,5) e, no mesmo quadrante, pelo maior score final. Bugs e incrementos seguem regras distintas de desempate.";

  return (
    <TooltipProvider>
      <div className="mx-auto w-full max-w-[1440px] space-y-5 pb-8">
        <div className="flex items-start gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600/30 to-indigo-600/20 ring-1 ring-violet-500/30">
            <ListFilter className="size-6 text-violet-300" />
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">{pageTitle}</h1>
            <p className="max-w-3xl text-sm text-muted-foreground">{pageSubtitle}</p>
          </div>
        </div>

        {errorMessage ? (
          <p className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-red-400">
            {errorMessage}
          </p>
        ) : null}

        <div className="space-y-5">
          {sections.map((section) => (
            <QueueSection
              key={section.key}
              accent={section.accent}
              title={section.title}
              description={section.description}
              orderLegend={section.orderLegend}
              items={section.items}
              isLoading={isLoading}
            />
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}
