"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  closestCorners,
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { ArrowLeft, ArrowRight, GripVertical, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { tentarAvancoAutomaticoKanban } from "@/lib/priorizacao/kanban-auto-advance";
import {
  columnToStatus,
  getWipLimit,
  KANBAN_COLUMN_ORDER,
  statusToColumn,
  type KanbanColumnId,
} from "@/lib/priorizacao/kanban-status";
import { buildFilaRankMap, compareByFilaRank } from "@/lib/priorizacao/fila-order";
import { toast } from "sonner";
import type { AtividadePriorizada, ConfigFila, KanbanGatesResponse } from "@/lib/priorizacao/types";

type ColumnId = KanbanColumnId;

type KanbanItem = AtividadePriorizada & {
  columnId: ColumnId;
};

const COLUMN_ORDER = KANBAN_COLUMN_ORDER;

/** Quantidade de cards visíveis no corpo da coluna antes do scroll interno. */
const KANBAN_VISIBLE_CARD_SLOTS = 2;

/** Altura fixa do corpo (~2 cards com gate + ações). */
const KANBAN_COLUMN_BODY_HEIGHT = "min(30rem, calc(100svh - 12rem))";

const KANBAN_COLUMN_BODY_HEIGHT_CLASS = "h-[min(30rem,calc(100svh-12rem))] max-h-[min(30rem,calc(100svh-12rem))]";

function columnTitle(columnId: ColumnId, count: number, limit?: number | null) {
  if (!limit) return `${columnId} (${count})`;
  return `${columnId} (${count}/${limit})`;
}

function getPriorityBadgeClass(priority?: string | null) {
  const value = (priority || "").toUpperCase();
  if (value.includes("CRIT")) return "border-red-500/30 bg-red-500/15 text-red-300";
  if (value.includes("ALTA")) return "border-orange-500/30 bg-orange-500/15 text-orange-300";
  if (value.includes("MEDIA") || value.includes("MÉDIA"))
    return "border-amber-500/30 bg-amber-500/15 text-amber-300";
  return "border-sky-500/30 bg-sky-500/15 text-sky-300";
}

function getTypeBadgeClass(type?: string | null) {
  const value = (type || "").toUpperCase();
  if (value === "BUG") return "border-rose-500/30 bg-rose-500/15 text-rose-300";
  return "border-indigo-500/30 bg-indigo-500/15 text-indigo-300";
}

function getColumnTheme(columnId: ColumnId) {
  if (columnId === "BACKLOG")
    return {
      accent: "text-rose-300",
      header: "from-rose-500/12 to-transparent",
      border: "border-rose-500/30",
    };
  if (columnId === "TO DO")
    return {
      accent: "text-blue-300",
      header: "from-blue-500/12 to-transparent",
      border: "border-blue-500/30",
    };
  if (columnId === "DEVELOP")
    return {
      accent: "text-violet-300",
      header: "from-violet-500/12 to-transparent",
      border: "border-violet-500/30",
    };
  if (columnId === "TEST")
    return {
      accent: "text-emerald-300",
      header: "from-emerald-500/12 to-transparent",
      border: "border-emerald-500/30",
    };
  if (columnId === "DEPLOY")
    return {
      accent: "text-amber-300",
      header: "from-amber-500/12 to-transparent",
      border: "border-amber-500/30",
    };
  return {
    accent: "text-cyan-300",
    header: "from-cyan-500/12 to-transparent",
    border: "border-cyan-500/30",
  };
}

function getCardDragId(itemId: number) {
  return `card-${itemId}`;
}

function getColumnDropId(columnId: ColumnId) {
  return `column-${columnId}`;
}

function parseCardDragId(id: string | number) {
  if (typeof id !== "string" || !id.startsWith("card-")) return null;
  const parsed = Number(id.slice(5));
  return Number.isInteger(parsed) ? parsed : null;
}

function parseColumnDropId(id: string | number) {
  if (typeof id !== "string" || !id.startsWith("column-")) return null;
  const parsed = id.slice(7) as ColumnId;
  return COLUMN_ORDER.includes(parsed) ? parsed : null;
}

function resolveDropColumn(
  overId: string | number | undefined,
  boardItems: KanbanItem[],
): ColumnId | null {
  if (overId === undefined) return null;
  const column = parseColumnDropId(overId);
  if (column) return column;
  const cardId = parseCardDragId(overId);
  if (cardId !== null) {
    return boardItems.find((entry) => entry.id === cardId)?.columnId ?? null;
  }
  return null;
}

function canAdvanceToColumn(item: KanbanItem, targetColumn: ColumnId) {
  const currentIndex = COLUMN_ORDER.indexOf(item.columnId);
  const targetIndex = COLUMN_ORDER.indexOf(targetColumn);
  return targetIndex === currentIndex + 1;
}

function isAdjacentColumn(item: KanbanItem, targetColumn: ColumnId) {
  const currentIndex = COLUMN_ORDER.indexOf(item.columnId);
  const targetIndex = COLUMN_ORDER.indexOf(targetColumn);
  return Math.abs(targetIndex - currentIndex) === 1;
}

type KanbanCardContentProps = {
  item: KanbanItem;
  blocked: boolean;
  wipBlocked: boolean;
  pendingCount: number;
  gates?: KanbanGatesResponse | null;
  movingId: number | null;
  onMovePrev: () => void;
  onMoveNext: () => void;
  isOverlay?: boolean;
  dragHandle?: React.ReactNode;
};

function KanbanCardContent({
  item,
  blocked,
  wipBlocked,
  pendingCount,
  gates,
  movingId,
  onMovePrev,
  onMoveNext,
  isOverlay = false,
  dragHandle,
}: KanbanCardContentProps) {
  return (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold leading-snug text-foreground">{item.titulo}</p>
        {dragHandle}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span
          className={`rounded-md border px-1.5 py-0.5 text-[10px] font-semibold tracking-wide ${getTypeBadgeClass(item.tipo_requisito)}`}
        >
          {item.tipo_requisito || "—"}
        </span>
        <span
          className={`rounded-md border px-1.5 py-0.5 text-[10px] font-semibold tracking-wide ${getPriorityBadgeClass(item.prioridade_categorica)}`}
        >
          {item.prioridade_categorica || "—"}
        </span>
      </div>
      {item.nome_projeto || item.versao_projeto ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Projeto: {item.nome_projeto || "—"}
          {item.versao_projeto ? ` · Versão: ${item.versao_projeto}` : ""}
        </p>
      ) : null}

      {gates ? (
        <p className="mt-2 text-[11px] text-muted-foreground">
          Esteira: <span className="font-medium text-foreground">{gates.coluna_kanban}</span>
          {gates.proxima_coluna ? (
            <>
              {" "}
              → <span className="font-medium text-foreground">{gates.proxima_coluna}</span>
            </>
          ) : null}
          {gates.wip_destino?.limite ? (
            <span className="ml-1">
              · WIP {gates.wip_destino.coluna}: {gates.wip_destino.ocupacao}/{gates.wip_destino.limite}
            </span>
          ) : null}
        </p>
      ) : null}

      <div
        className={`mt-3 rounded-xl border px-3 py-2.5 ${
          blocked
            ? "border-amber-500/35 bg-amber-500/10 text-amber-300"
            : "border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
        }`}
      >
        {blocked ? (
          <>
            <div className="flex items-center gap-2 text-xs font-semibold">
              <TriangleAlert className="size-3.5" />
              <span>Gate documental bloqueado</span>
            </div>
            <p className="mt-1 text-xs text-amber-200/90">
              {pendingCount} {pendingCount === 1 ? "pendência documental" : "pendências documentais"}
            </p>
          </>
        ) : (
          <>
            <p className="text-xs font-semibold">Gate documental liberado</p>
            <p className="mt-1 text-xs text-emerald-200/90">
              {pendingCount === 0
                ? "Sem pendências documentais"
                : `${pendingCount} ${pendingCount === 1 ? "pendência documental" : "pendências documentais"}`}
            </p>
          </>
        )}
      </div>

      {wipBlocked ? (
        <p className="mt-2 text-xs text-red-300/90">
          WIP da coluna de destino cheio — libere vaga antes de avançar.
        </p>
      ) : null}

      <div className="mt-3 space-y-2">
        <Button
          asChild
          type="button"
          variant="outline"
          size="sm"
          className="w-full justify-center rounded-lg border-white/10 bg-white/[0.02] hover:bg-white/[0.06]"
          onPointerDown={(event) => event.stopPropagation()}
        >
          <Link href={`/kanban/list/${item.id}`}>Detalhe da atividade</Link>
        </Button>
        <div className="grid grid-cols-2 gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full justify-center rounded-lg border-white/10 bg-white/[0.02] hover:bg-white/[0.06]"
            disabled={isOverlay || item.columnId === "BACKLOG" || movingId === item.id}
            onPointerDown={(event) => event.stopPropagation()}
            onClick={onMovePrev}
          >
            <ArrowLeft className="mr-1 size-3.5" />
            Voltar
          </Button>
          <Button
            type="button"
            size="sm"
            className="w-full justify-center rounded-lg bg-gradient-to-r from-violet-500 to-indigo-500 text-white hover:from-violet-400 hover:to-indigo-400"
            disabled={
              isOverlay || item.columnId === "DONE" || movingId === item.id || blocked || wipBlocked
            }
            onPointerDown={(event) => event.stopPropagation()}
            onClick={onMoveNext}
          >
            Avançar
            <ArrowRight className="ml-1 size-3.5" />
          </Button>
        </div>
      </div>
    </>
  );
}

type KanbanCardProps = {
  item: KanbanItem;
  blocked: boolean;
  wipBlocked: boolean;
  pendingCount: number;
  gates?: KanbanGatesResponse | null;
  movingId: number | null;
  onMovePrev: () => void;
  onMoveNext: () => void;
};

function KanbanCard(props: KanbanCardProps) {
  const { item, blocked, wipBlocked, pendingCount, gates, movingId, onMovePrev, onMoveNext } = props;
  const { attributes, listeners, setActivatorNodeRef, setNodeRef, transform, isDragging } =
    useDraggable({
      id: getCardDragId(item.id),
      disabled: movingId === item.id,
    });

  return (
    <div
      ref={setNodeRef}
      draggable={false}
      aria-hidden={isDragging}
      onDragStart={(event) => event.preventDefault()}
      style={{
        transform: CSS.Transform.toString(transform),
      }}
      className={`select-none rounded-2xl border border-white/10 bg-card/85 p-3 shadow-md shadow-black/20 ring-1 ring-white/5 ${
        isDragging
          ? "pointer-events-none opacity-0"
          : "transition-[box-shadow,border-color] hover:border-primary/40 hover:shadow-lg hover:shadow-primary/15"
      }`}
    >
      <KanbanCardContent
        item={item}
        blocked={blocked}
        wipBlocked={wipBlocked}
        pendingCount={pendingCount}
        gates={gates}
        movingId={movingId}
        onMovePrev={onMovePrev}
        onMoveNext={onMoveNext}
        dragHandle={
          <button
            ref={setActivatorNodeRef}
            type="button"
            draggable={false}
            {...listeners}
            {...attributes}
            style={{ touchAction: "none" }}
            className="inline-flex shrink-0 cursor-grab items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] p-1 text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground active:cursor-grabbing"
            aria-label={`Arrastar atividade ${item.titulo}`}
            onClick={(event) => event.preventDefault()}
            onDragStart={(event) => event.preventDefault()}
            onMouseDown={(event) => event.preventDefault()}
            onPointerDownCapture={() => {
              if (typeof window !== "undefined") {
                window.getSelection()?.removeAllRanges();
              }
            }}
          >
            <GripVertical className="size-4" />
          </button>
        }
      />
    </div>
  );
}

type KanbanColumnProps = {
  columnId: ColumnId;
  count: number;
  limit: number | null;
  isAtLimit: boolean;
  canAcceptDrop: boolean;
  isHoverTarget: boolean;
  children: React.ReactNode;
};

function KanbanColumn({
  columnId,
  count,
  limit,
  isAtLimit,
  canAcceptDrop,
  isHoverTarget,
  children,
}: KanbanColumnProps) {
  const { isOver, setNodeRef } = useDroppable({
    id: getColumnDropId(columnId),
    disabled: !canAcceptDrop,
  });

  const theme = getColumnTheme(columnId);
  const highlightDrop = canAcceptDrop && (isOver || isHoverTarget);

  return (
    <div
      className={`flex w-[320px] min-w-[320px] shrink-0 flex-col overflow-hidden rounded-2xl border border-white/10 bg-card/55 ring-1 ring-white/5 transition-all ${
        highlightDrop
          ? "border-primary/60 bg-primary/10 shadow-xl shadow-primary/20 ring-primary/30"
          : ""
      }`}
    >
      <div
        className={`shrink-0 border-b border-white/10 bg-gradient-to-r px-3 py-3 ${
          isAtLimit ? "from-destructive/20 to-transparent" : theme.header
        }`}
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className={`text-xs font-bold tracking-wide ${theme.accent}`}>{columnId}</h2>
          <span
            className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${
              isAtLimit
                ? "border-destructive/40 bg-destructive/15 text-red-300"
                : `${theme.border} bg-black/25 text-foreground`
            }`}
          >
            {limit ? `${count}/${limit}` : count}
          </span>
        </div>
      </div>

      <div
        ref={setNodeRef}
        style={{ height: KANBAN_COLUMN_BODY_HEIGHT, maxHeight: KANBAN_COLUMN_BODY_HEIGHT }}
        className={`kanban-column-body flex shrink-0 flex-col gap-2 overflow-x-hidden overflow-y-auto overscroll-y-contain p-2.5 ${KANBAN_COLUMN_BODY_HEIGHT_CLASS}`}
      >
        {children}
      </div>
    </div>
  );
}

export default function KanbanPage() {
  const [items, setItems] = useState<KanbanItem[]>([]);
  const [filaRank, setFilaRank] = useState<Map<number, number>>(new Map());
  const [config, setConfig] = useState<ConfigFila | null>(null);
  const [gatesById, setGatesById] = useState<Record<number, KanbanGatesResponse>>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [movingId, setMovingId] = useState<number | null>(null);
  const [activeDragItemId, setActiveDragItemId] = useState<number | null>(null);
  const [hoverColumnId, setHoverColumnId] = useState<ColumnId | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  );

  const mapActivitiesToItems = (activitiesData: unknown): KanbanItem[] =>
    Array.isArray(activitiesData)
      ? (activitiesData as AtividadePriorizada[]).map((item) => ({
          ...item,
          columnId: statusToColumn(item.status_atual),
        }))
      : [];

  const refreshGatesForItem = async (itemId: number) => {
    const response = await fetch(`/api/priorizacao/kanban/${itemId}/gates`, {
      cache: "no-store",
    });
    const data = await response.json().catch(() => null);
    if (response.ok && data) {
      setGatesById((prev) => ({ ...prev, [itemId]: data as KanbanGatesResponse }));
    }
  };

  const refreshGatesForItems = async (itemIds: number[]) => {
    const uniqueIds = [...new Set(itemIds)];
    await Promise.all(uniqueIds.map((id) => refreshGatesForItem(id)));
  };

  const refreshActivitiesSilent = async () => {
    const [activitiesResponse, filaResponse] = await Promise.all([
      fetch("/api/priorizacao/atividades", { cache: "no-store" }),
      fetch("/api/priorizacao/fila", { cache: "no-store" }),
    ]);
    const [activitiesData, filaData] = await Promise.all([
      activitiesResponse.json().catch(() => []),
      filaResponse.json().catch(() => []),
    ]);
    if (activitiesResponse.ok) {
      setItems(mapActivitiesToItems(activitiesData));
    }
    if (filaResponse.ok && Array.isArray(filaData)) {
      setFilaRank(buildFilaRankMap(filaData as { id: number }[]));
    }
  };

  const applyOptimisticColumnMove = (itemId: number, targetColumn: ColumnId) => {
    setItems((prev) =>
      prev.map((entry) =>
        entry.id === itemId
          ? { ...entry, columnId: targetColumn, status_atual: columnToStatus(targetColumn) }
          : entry,
      ),
    );
  };

  const rollbackItem = (snapshot: KanbanItem) => {
    setItems((prev) => prev.map((entry) => (entry.id === snapshot.id ? snapshot : entry)));
  };

  const loadBoard = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const [activitiesResponse, configResponse, filaResponse] = await Promise.all([
        fetch("/api/priorizacao/atividades", { cache: "no-store" }),
        fetch("/api/priorizacao/config-fila", { cache: "no-store" }),
        fetch("/api/priorizacao/fila", { cache: "no-store" }),
      ]);
      const [activitiesData, configData, filaData] = await Promise.all([
        activitiesResponse.json().catch(() => []),
        configResponse.json().catch(() => null),
        filaResponse.json().catch(() => []),
      ]);
      if (!activitiesResponse.ok) {
        throw new Error(
          activitiesData &&
            typeof activitiesData === "object" &&
            "detail" in activitiesData &&
            typeof activitiesData.detail === "string"
            ? activitiesData.detail
            : "Não foi possível carregar a esteira.",
        );
      }
      if (!configResponse.ok) {
        throw new Error(
          configData &&
            typeof configData === "object" &&
            "detail" in configData &&
            typeof configData.detail === "string"
            ? configData.detail
            : "Não foi possível carregar a calibragem do Kanban.",
        );
      }

      const nextItems = mapActivitiesToItems(activitiesData);

      setItems(nextItems);
      setConfig((configData as ConfigFila | null) ?? null);
      if (filaResponse.ok && Array.isArray(filaData)) {
        setFilaRank(buildFilaRankMap(filaData as { id: number }[]));
      } else {
        setFilaRank(new Map());
      }

      const gateResponses = await Promise.all(
        nextItems.map(async (item) => {
          const response = await fetch(`/api/priorizacao/kanban/${item.id}/gates`, {
            cache: "no-store",
          });
          const data = await response.json().catch(() => null);
          return response.ok ? ([item.id, data] as const) : null;
        }),
      );

      const gateMap: Record<number, KanbanGatesResponse> = {};
      for (const entry of gateResponses) {
        if (!entry) continue;
        const [id, gate] = entry;
        gateMap[id] = gate as KanbanGatesResponse;
      }
      setGatesById(gateMap);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível carregar a esteira.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadBoard();
  }, []);

  useEffect(() => {
    const onFocus = () => void loadBoard();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  const itemsByColumn = useMemo(() => {
    return COLUMN_ORDER.reduce<Record<ColumnId, KanbanItem[]>>((acc, columnId) => {
      const columnItems = items.filter((item) => item.columnId === columnId);
      if (filaRank.size > 0) {
        columnItems.sort((a, b) => compareByFilaRank(a, b, filaRank));
      } else {
        columnItems.sort((a, b) => a.id - b.id);
      }
      acc[columnId] = columnItems;
      return acc;
    }, {
      BACKLOG: [],
      "TO DO": [],
      DEVELOP: [],
      TEST: [],
      DEPLOY: [],
      DONE: [],
    });
  }, [items, filaRank]);

  const activeDragItem = useMemo(
    () => items.find((item) => item.id === activeDragItemId) ?? null,
    [activeDragItemId, items],
  );

  const moveItemToColumn = async (
    item: KanbanItem,
    targetColumn: ColumnId,
    mode: "next" | "adjacent" = "adjacent",
  ) => {
    const canMove =
      mode === "next" ? canAdvanceToColumn(item, targetColumn) : isAdjacentColumn(item, targetColumn);

    if (!canMove) {
      return;
    }

    const snapshot: KanbanItem = { ...item };
    const sourceColumn = item.columnId;
    const currentIndex = COLUMN_ORDER.indexOf(sourceColumn);
    const targetIndex = COLUMN_ORDER.indexOf(targetColumn);
    const isRetrocesso = targetIndex < currentIndex;

    const affectedPeerIds = items
      .filter((entry) => entry.columnId === sourceColumn || entry.columnId === targetColumn)
      .map((entry) => entry.id);

    try {
      setMovingId(item.id);
      setErrorMessage(null);

      applyOptimisticColumnMove(item.id, targetColumn);
      setActiveDragItemId((current) => (current === item.id ? null : current));

      if (isRetrocesso) {
        const response = await fetch(`/api/priorizacao/requisitos/${item.id}/status`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: columnToStatus(targetColumn) }),
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
          rollbackItem(snapshot);
          const detail =
            data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
              ? data.detail
              : "Não foi possível atualizar o status da atividade.";
          toast.error("Não foi possível mover", { description: detail });
          return;
        }
        toast.success(`Movido para ${targetColumn}`, {
          description: `Atividade #${item.id} atualizada na esteira.`,
        });
        await Promise.all([refreshActivitiesSilent(), refreshGatesForItems([item.id, ...affectedPeerIds])]);
        return;
      }

      const advance = await tentarAvancoAutomaticoKanban(item.id, { maxSteps: 1, silent: true });
      if (advance.stopped === "ok" && advance.stepsCompleted > 0) {
        toast.success(`Movido para ${targetColumn}`, {
          description: `Atividade #${item.id} avançou na esteira.`,
        });
        await Promise.all([refreshActivitiesSilent(), refreshGatesForItems([item.id, ...affectedPeerIds])]);
        return;
      }

      rollbackItem(snapshot);
      if (advance.stopped === "gate" && advance.gates) {
        const falta = advance.gates.falta_documentacao;
        toast.error("Documentação incompleta", {
          description:
            falta.length > 0
              ? falta.slice(0, 3).join("; ") + (falta.length > 3 ? "…" : "")
              : `Conclua a documentação da coluna ${advance.gates.coluna_kanban} antes de avançar.`,
        });
      } else if (advance.stopped === "wip" && advance.gates) {
        const wip = advance.gates.wip_destino;
        const coluna = wip?.coluna ?? advance.gates.proxima_coluna ?? "destino";
        toast.error(`Limite WIP em ${coluna}`, {
          description: `A coluna já tem ${wip?.ocupacao ?? "?"} de ${wip?.limite ?? "?"} atividades.`,
        });
      } else if (advance.detail) {
        toast.error("Não foi possível mover", { description: advance.detail });
      } else {
        toast.error("Não foi possível mover");
      }
    } catch (error) {
      rollbackItem(snapshot);
      const msg =
        error instanceof Error ? error.message : "Não foi possível atualizar o status da atividade.";
      toast.error("Não foi possível mover", { description: msg });
    } finally {
      setMovingId(null);
    }
  };

  const moveItem = async (item: KanbanItem, direction: "next" | "prev") => {
    const currentIndex = COLUMN_ORDER.indexOf(item.columnId);
    const targetIndex = direction === "next" ? currentIndex + 1 : currentIndex - 1;
    const targetColumn = COLUMN_ORDER[targetIndex];
    if (!targetColumn) {
      toast.error("Não é possível mover o cartão nesta direção.");
      return;
    }

    await moveItemToColumn(item, targetColumn, "adjacent");
  };

  const handleDragStart = (event: DragStartEvent) => {
    if (typeof window !== "undefined") {
      window.getSelection()?.removeAllRanges();
    }
    const itemId = parseCardDragId(event.active.id);
    setActiveDragItemId(itemId);
    setHoverColumnId(null);
    setErrorMessage(null);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const draggedId = parseCardDragId(event.active.id);
    if (!draggedId) {
      setHoverColumnId(null);
      return;
    }
    const item = items.find((entry) => entry.id === draggedId);
    if (!item) {
      setHoverColumnId(null);
      return;
    }
    const column = event.over ? resolveDropColumn(event.over.id, items) : null;
    if (column && isAdjacentColumn(item, column)) {
      setHoverColumnId(column);
      return;
    }
    setHoverColumnId(null);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const draggedId = parseCardDragId(event.active.id);
    const targetColumn = event.over ? resolveDropColumn(event.over.id, items) : null;
    setHoverColumnId(null);

    if (!draggedId) {
      setActiveDragItemId(null);
      return;
    }

    const item = items.find((entry) => entry.id === draggedId);
    if (!item) {
      setActiveDragItemId(null);
      return;
    }

    if (!targetColumn) {
      setActiveDragItemId(null);
      toast.error("Solte o cartão sobre uma coluna ou sobre um cartão da coluna de destino.");
      return;
    }

    if (targetColumn === item.columnId) {
      setActiveDragItemId(null);
      return;
    }

    if (!isAdjacentColumn(item, targetColumn)) {
      setActiveDragItemId(null);
      toast.error(
        "Só é possível mover para a coluna imediata. Use Voltar várias vezes para chegar ao BACKLOG.",
      );
      return;
    }

    await moveItemToColumn(
      item,
      targetColumn,
      canAdvanceToColumn(item, targetColumn) ? "next" : "adjacent",
    );
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">Esteira Kanban de Requisitos</h1>
        <Link href="/kanban/list" className="text-sm text-primary/90 underline-offset-4 hover:underline">
          Ver todas as atividades da esteira em lista
        </Link>
      </div>

      {errorMessage ? (
        <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-red-500">
          {errorMessage}
        </p>
      ) : null}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={(event) => void handleDragEnd(event)}
        onDragCancel={() => {
          setActiveDragItemId(null);
          setHoverColumnId(null);
        }}
      >
        <div className="select-none overflow-x-auto rounded-2xl border border-white/10 bg-card/45 p-3 shadow-xl shadow-black/20 ring-1 ring-white/5">
          <div className="flex min-w-max items-start gap-3">
            {COLUMN_ORDER.map((columnId) => {
              const columnItems = itemsByColumn[columnId];
              const limit = getWipLimit(config?.wip, columnId);
              const isAtLimit =
                typeof limit === "number" && limit > 0 && columnItems.length >= limit;
              const canAcceptDrop =
                activeDragItem !== null && isAdjacentColumn(activeDragItem, columnId);

              return (
                <KanbanColumn
                  key={columnId}
                  columnId={columnId}
                  count={columnItems.length}
                  limit={limit}
                  isAtLimit={isAtLimit}
                  canAcceptDrop={canAcceptDrop}
                  isHoverTarget={hoverColumnId === columnId}
                >
                  {isLoading ? (
                    <div className="rounded-xl border border-dashed border-white/20 bg-black/20 p-4 text-center text-xs text-muted-foreground">
                      Carregando coluna...
                    </div>
                  ) : columnItems.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-white/20 bg-black/20 p-4 text-center text-xs text-muted-foreground">
                      Nenhuma atividade nesta coluna.
                    </div>
                  ) : (
                    columnItems.map((item) => {
                      const gates = gatesById[item.id];
                      const pendingCount =
                        gates && Array.isArray(gates.falta_documentacao)
                          ? gates.falta_documentacao.length
                          : 0;
                      const blocked =
                        columnId !== "DONE" &&
                        pendingCount > 0 &&
                        directionWouldAdvance(columnId);
                      const wipBlocked =
                        Boolean(gates?.proxima_coluna) && gates?.pode_avancar_wip === false;

                      return (
                        <KanbanCard
                          key={item.id}
                          item={item}
                          blocked={blocked}
                          wipBlocked={wipBlocked}
                          pendingCount={pendingCount}
                          gates={gates}
                          movingId={movingId}
                          onMovePrev={() => void moveItem(item, "prev")}
                          onMoveNext={() => void moveItem(item, "next")}
                        />
                      );
                    })
                  )}
                </KanbanColumn>
              );
            })}
          </div>
        </div>

        <DragOverlay dropAnimation={null}>
          {activeDragItem ? (
            <div className="pointer-events-none w-[320px] cursor-grabbing rounded-2xl border border-primary/40 bg-card/95 p-3 shadow-2xl shadow-primary/30 ring-1 ring-white/5">
              <KanbanCardContent
                item={activeDragItem}
                blocked={
                  Array.isArray(gatesById[activeDragItem.id]?.falta_documentacao) &&
                  gatesById[activeDragItem.id]!.falta_documentacao.length > 0 &&
                  directionWouldAdvance(activeDragItem.columnId)
                }
                wipBlocked={
                  Boolean(gatesById[activeDragItem.id]?.proxima_coluna) &&
                  gatesById[activeDragItem.id]?.pode_avancar_wip === false
                }
                gates={gatesById[activeDragItem.id]}
                pendingCount={gatesById[activeDragItem.id]?.falta_documentacao.length ?? 0}
                movingId={movingId}
                onMovePrev={() => undefined}
                onMoveNext={() => undefined}
                isOverlay
              />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}

function directionWouldAdvance(columnId: ColumnId) {
  return columnId !== "DONE";
}
