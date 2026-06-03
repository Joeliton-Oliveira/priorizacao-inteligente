"use client";

import { useEffect, useMemo, useState } from "react";
import { CustomModal } from "@/components/ui/CustomModal";
import {
  ActivityDocumentationView,
  type DocumentationConfirmPhaseId,
  type DocumentationFillPhaseId,
} from "./activity-documentation-view";
import { BacklogPhaseFillForm } from "./backlog-phase-fill-form";
import { TestPhaseFillForm } from "./test-phase-fill-form";
import {
  buildMarcarComoFeitoDeploy,
  buildMarcarComoFeitoDevelop,
  buildMarcarComoFeitoEncerramento,
  buildMarcarComoFeitoToDo,
  getEmptyActivityDocumentation,
  type DocumentationPhaseKey,
  DOCUMENTATION_BY_CARD_ID,
  getActivityDocumentation,
  type ActivityDocumentation,
} from "./activity-documentation-data";
import {
  canFillPhase,
  canMarkPhaseComplete,
  getPhaseCompletionMap,
  getPhasesToClear,
} from "./documentation-phase-flow";

const FILL_PHASE_TITLES: Partial<Record<DocumentationFillPhaseId, string>> = {
  backlog: "BACKLOG — documento de requisito",
  test: "Casos de teste",
};

type ActivityDocumentationModalProps = {
  cardId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  requirementType?: string | null;
};

function clearPhaseInDoc(
  doc: ActivityDocumentation,
  phase: DocumentationPhaseKey,
): ActivityDocumentation {
  const empty = getEmptyActivityDocumentation();
  switch (phase) {
    case "backlog":
      return { ...doc, backlog: empty.backlog };
    case "to-do":
      return { ...doc, toDo: empty.toDo };
    case "develop":
      return { ...doc, develop: empty.develop };
    case "test":
      return { ...doc, test: empty.test };
    case "deploy":
      return { ...doc, deploy: empty.deploy };
    case "encerramento":
      return { ...doc, encerramento: "" };
    default:
      return doc;
  }
}

export function ActivityDocumentationModal({
  cardId,
  open,
  onOpenChange,
  requirementType = null,
}: ActivityDocumentationModalProps) {
  const [docsByCard, setDocsByCard] = useState<Record<string, ActivityDocumentation>>(
    DOCUMENTATION_BY_CARD_ID,
  );
  const [fillPhase, setFillPhase] = useState<DocumentationFillPhaseId | null>(null);
  const [reopenedPhase, setReopenedPhase] = useState<DocumentationPhaseKey | null>(null);

  useEffect(() => {
    if (!open) {
      setFillPhase(null);
      setReopenedPhase(null);
    }
  }, [open]);

  if (!cardId) return null;

  const data = docsByCard[cardId] ?? getActivityDocumentation(cardId);
  const fillTitle = fillPhase ? FILL_PHASE_TITLES[fillPhase] : undefined;
  const requisitoId = Number(cardId);

  const updateDoc = (patch: Partial<ActivityDocumentation>) => {
    setDocsByCard((prev) => ({
      ...prev,
      [cardId]: { ...(prev[cardId] ?? getActivityDocumentation(cardId)), ...patch },
    }));
    setFillPhase(null);
    setReopenedPhase(null);
  };

  const applyDoc = (next: ActivityDocumentation) => {
    setDocsByCard((prev) => ({ ...prev, [cardId]: next }));
  };

  const handleMarcarComoFeito = (phase: DocumentationConfirmPhaseId) => {
    const raw = getPhaseCompletionMap(data);
    if (!canMarkPhaseComplete(phase, raw)) return;

    if (phase === "to-do") {
      updateDoc({ toDo: buildMarcarComoFeitoToDo() });
      return;
    }
    if (phase === "develop") {
      updateDoc({
        develop: buildMarcarComoFeitoDevelop(
          Number.isNaN(requisitoId) ? 0 : requisitoId,
          data.backlog?.nomeFuncionalidade,
        ),
      });
      return;
    }
    if (phase === "deploy") {
      updateDoc({
        deploy: buildMarcarComoFeitoDeploy(),
        encerramento: buildMarcarComoFeitoEncerramento(data.encerramento),
      });
    }
  };

  const handleReabrirFase = (phase: DocumentationPhaseKey) => {
    const current = docsByCard[cardId] ?? getActivityDocumentation(cardId);
    const raw = getPhaseCompletionMap(current);
    let next = current;
    for (const key of getPhasesToClear(phase, raw)) {
      next = clearPhaseInDoc(next, key);
    }
    applyDoc(next);

    if (phase === "backlog" || phase === "test") {
      setReopenedPhase(phase);
      setFillPhase(phase);
    }
  };

  const handlePreencherFase = (phase: DocumentationFillPhaseId) => {
    const raw = getPhaseCompletionMap(data);
    if (!canFillPhase(phase, raw)) return;
    setReopenedPhase(null);
    setFillPhase(phase);
  };

  const handleCancelFill = () => {
    setFillPhase(null);
    setReopenedPhase(null);
  };

  const viewData = useMemo(
    () => docsByCard[cardId] ?? getActivityDocumentation(cardId),
    [cardId, docsByCard],
  );
  const isFillOpen = Boolean(fillPhase);

  return (
    <>
      <CustomModal
        open={open && !isFillOpen}
        onOpenChange={onOpenChange}
        title="Documentação por fase"
        description="Ao salvar cada fase, a esteira avança automaticamente se o gate e o WIP da coluna de destino permitirem."
        contentClassName="flex max-h-[min(90vh,820px)] max-w-3xl flex-col overflow-hidden sm:max-w-3xl"
      >
        <div className="-mx-1 flex-1 overflow-y-auto px-1 pb-1">
          <ActivityDocumentationView
            data={viewData}
            requirementType={requirementType}
            onPreencherFase={handlePreencherFase}
            onMarcarComoFeito={handleMarcarComoFeito}
            onReabrirFase={handleReabrirFase}
            reopenedPhase={reopenedPhase}
          />
        </div>
      </CustomModal>

      <CustomModal
        open={open && isFillOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) handleCancelFill();
        }}
        title={fillTitle ?? "Documentação"}
        contentClassName="flex max-h-[min(90vh,820px)] max-w-xl flex-col overflow-hidden sm:max-w-xl"
      >
        <div className="-mx-1 flex-1 overflow-y-auto px-1 pb-1">
          {fillPhase === "backlog" ? (
            <BacklogPhaseFillForm
              initial={viewData.backlog}
              requirementType={requirementType}
              onSave={(backlog) => updateDoc({ backlog })}
              onCancel={handleCancelFill}
            />
          ) : fillPhase === "test" ? (
            <TestPhaseFillForm
              cardId={cardId}
              initial={viewData.test}
              onSave={(test) => updateDoc({ test })}
              onCancel={handleCancelFill}
            />
          ) : null}
        </div>
      </CustomModal>
    </>
  );
}
