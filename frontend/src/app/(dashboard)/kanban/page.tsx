"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CustomModal } from "@/components/ui/CustomModal";
import { ActivityDocumentationModal } from "./_components/activity-documentation-modal";

type Column = {
  id: string;
  title: string;
  wipLimit: number | null;
};

type ActivityCard = {
  id: string;
  columnId: string;
  title: string;
  type: string;
  priority: string;
  projeto: string;
  solicitante: string;
  criadoEm: string;
};

const COLUMNS: Column[] = [
  { id: "backlog", title: "BACKLOG", wipLimit: null },
  { id: "to-do", title: "TO DO", wipLimit: 5 },
  { id: "develop", title: "DEVELOP", wipLimit: 2 },
  { id: "test", title: "TEST", wipLimit: 2 },
  { id: "deploy", title: "DEPLOY", wipLimit: 1 },
  { id: "done", title: "DONE", wipLimit: null },
];

const INITIAL_CARDS: ActivityCard[] = [
  {
    id: "1",
    columnId: "backlog",
    title: "[AUTO] Bug exibição gráfico v2",
    type: "BUG",
    priority: "MÉDIA",
    projeto: "Priorização Inteligente de Requisitos",
    solicitante: "Product Owner",
    criadoEm: "23/05/2026",
  },
  {
    id: "2",
    columnId: "backlog",
    title: "[AUTO] Incremento exibição gráfico v2",
    type: "INCREMENTO",
    priority: "MÉDIA",
    projeto: "Priorização Inteligente de Requisitos",
    solicitante: "Product Owner",
    criadoEm: "23/05/2026",
  },
  {
    id: "3",
    columnId: "done",
    title: "Falha na conclusão de pedido no checkout com pagamento processado",
    type: "BUG",
    priority: "MÉDIA",
    projeto: "Priorização Inteligente de Requisitos",
    solicitante: "Analista de Negócio",
    criadoEm: "20/05/2026",
  },
];

function ActivityDetailRow({ label, value }: { label: string; value: string }) {
  return (
    <p className="text-sm leading-relaxed">
      <span className="font-semibold">{label}:</span> {value}
    </p>
  );
}

function getColumnIndex(columnId: string) {
  return COLUMNS.findIndex((column) => column.id === columnId);
}

function SortableCard({
  card,
  onOpenDetails,
}: {
  card: ActivityCard;
  onOpenDetails: (card: ActivityCard) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: card.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`rounded-lg border border-border/60 bg-card p-3 shadow-sm transition hover:border-primary/30 hover:shadow-md ${
        isDragging ? "opacity-60 ring-2 ring-primary/30" : ""
      }`}
    >
      <div className="cursor-grab active:cursor-grabbing" {...attributes} {...listeners}>
        <h3 className="text-sm font-semibold leading-snug">{card.title}</h3>
      </div>

      <Button
        type="button"
        size="sm"
        variant="secondary"
        className="mt-2 h-10 w-full justify-between px-4 text-sm font-medium"
        onClick={() => onOpenDetails(card)}
      >
        <span>Ver detalhes da atividade</span>
        <ArrowRight className="size-4 shrink-0" aria-hidden="true" />
      </Button>
    </div>
  );
}

function BoardColumn({
  column,
  cards,
  onOpenDetails,
}: {
  column: Column;
  cards: ActivityCard[];
  onOpenDetails: (card: ActivityCard) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });
  const limitText = column.wipLimit === null ? `${cards.length}` : `${cards.length}/${column.wipLimit}`;

  const atWipLimit =
    column.wipLimit !== null && cards.length >= column.wipLimit;

  return (
    <div
      ref={setNodeRef}
      className={`flex w-[min(100%,280px)] shrink-0 flex-col rounded-xl border border-border/80 bg-muted/30 ${
        isOver ? "ring-2 ring-primary/50" : ""
      }`}
    >
      <div
        className={`border-b px-3 py-2.5 ${
          atWipLimit ? "bg-destructive/10" : "bg-card/80"
        }`}
      >
        <h2 className="text-xs font-bold tracking-wide text-foreground">
          {column.title}
        </h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {column.wipLimit === null ? `${cards.length} itens` : `WIP ${limitText}`}
        </p>
      </div>

      <SortableContext items={cards.map((card) => card.id)} strategy={verticalListSortingStrategy}>
        <div className="flex min-h-[420px] flex-1 flex-col gap-2 overflow-y-auto p-2">
          {cards.length === 0 ? (
            <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-border/60 bg-card/40 p-4 text-center text-xs text-muted-foreground">
              Nenhuma atividade nesta coluna.
            </div>
          ) : (
            cards.map((card) => (
              <SortableCard
                key={card.id}
                card={card}
                onOpenDetails={onOpenDetails}
              />
            ))
          )}
        </div>
      </SortableContext>
    </div>
  );
}

export default function KanbanPage() {
  const [cards, setCards] = useState<ActivityCard[]>(INITIAL_CARDS);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [detailsCard, setDetailsCard] = useState<ActivityCard | null>(null);
  const [documentationCardId, setDocumentationCardId] = useState<string | null>(null);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const cardsByColumn = useMemo(() => {
    return COLUMNS.reduce<Record<string, ActivityCard[]>>((acc, column) => {
      acc[column.id] = cards.filter((card) => card.columnId === column.id);
      return acc;
    }, {});
  }, [cards]);

  const findCardColumn = (cardId: string) => cards.find((card) => card.id === cardId)?.columnId;

  const canMoveToColumn = (cardId: string, targetColumnId: string) => {
    const targetColumn = COLUMNS.find((column) => column.id === targetColumnId);
    if (!targetColumn || targetColumn.wipLimit === null) return true;
    const targetCount = cards.filter((card) => card.columnId === targetColumnId).length;
    const sourceColumnId = findCardColumn(cardId);
    const sameColumn = sourceColumnId === targetColumnId;
    return sameColumn || targetCount < targetColumn.wipLimit;
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(String(event.active.id));
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const activeId = String(event.active.id);
    const overId = event.over ? String(event.over.id) : null;
    setActiveCardId(null);

    if (!overId) return;

    const sourceColumnId = findCardColumn(activeId);
    if (!sourceColumnId) return;

    let targetColumnId = COLUMNS.some((column) => column.id === overId)
      ? overId
      : findCardColumn(overId) ?? sourceColumnId;

    if (!canMoveToColumn(activeId, targetColumnId)) {
      setWarning("Não é possível mover o cartão nesta direção.");
      return;
    }

    setWarning(null);
    setCards((prev) => {
      const sourceCards = prev.filter((card) => card.columnId === sourceColumnId);
      const targetCards = prev.filter((card) => card.columnId === targetColumnId);
      const moving = prev.find((card) => card.id === activeId);
      if (!moving) return prev;

      if (sourceColumnId === targetColumnId) {
        const oldIndex = sourceCards.findIndex((card) => card.id === activeId);
        const newIndex = targetCards.findIndex((card) => card.id === overId);
        if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return prev;
        const reordered = [...sourceCards];
        const [item] = reordered.splice(oldIndex, 1);
        reordered.splice(newIndex, 0, item);
        return [
          ...prev.filter((card) => card.columnId !== sourceColumnId),
          ...reordered,
        ];
      }

      const overIsCard = prev.some((card) => card.id === overId);
      const nextTargetCards = targetCards.slice();
      const insertIndex = overIsCard
        ? nextTargetCards.findIndex((card) => card.id === overId)
        : nextTargetCards.length;
      nextTargetCards.splice(insertIndex < 0 ? nextTargetCards.length : insertIndex, 0, {
        ...moving,
        columnId: targetColumnId,
      });

      return [
        ...prev.filter((card) => card.id !== activeId && card.columnId !== targetColumnId),
        ...nextTargetCards,
      ];
    });
  };

  const activeCard = cards.find((card) => card.id === activeCardId) ?? null;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Esteira Kanban de Requisitos</h1>

      {warning ? (
        <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-red-500">
          {warning}
        </p>
      ) : null}

      <div className="overflow-x-auto rounded-xl border bg-card/50 p-3 shadow-sm">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex min-w-max gap-3 pb-1">
            {COLUMNS.map((column) => (
              <BoardColumn
                key={column.id}
                column={column}
                cards={cardsByColumn[column.id] ?? []}
                onOpenDetails={setDetailsCard}
              />
            ))}
          </div>

          <DragOverlay>
            {activeCard ? (
              <div className="min-w-[280px] rounded-lg border bg-background p-3 shadow-lg">
                <p className="text-sm font-semibold">{activeCard.title}</p>
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </div>

      <CustomModal
        open={detailsCard !== null}
        onOpenChange={(open) => {
          if (!open) setDetailsCard(null);
        }}
        title="Detalhes da atividade"
      >
        {detailsCard ? (
          <div className="space-y-4">
            <div className="space-y-2.5">
              <ActivityDetailRow label="Título" value={detailsCard.title} />
              <ActivityDetailRow label="Tipo" value={detailsCard.type} />
              <ActivityDetailRow label="Prioridade" value={detailsCard.priority} />
              <ActivityDetailRow label="Projeto" value={detailsCard.projeto} />
              <ActivityDetailRow label="Solicitante" value={detailsCard.solicitante} />
              <ActivityDetailRow label="Criado em" value={detailsCard.criadoEm} />
            </div>
            <Button
              type="button"
              className="w-full"
              onClick={() => setDocumentationCardId(detailsCard.id)}
            >
              Documentação
            </Button>
          </div>
        ) : null}
      </CustomModal>

      <ActivityDocumentationModal
        cardId={documentationCardId}
        open={documentationCardId !== null}
        onOpenChange={(open) => {
          if (!open) setDocumentationCardId(null);
        }}
      />
    </div>
  );
}
