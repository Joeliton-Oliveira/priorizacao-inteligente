"use client";

import { useEffect, useState } from "react";
import { CustomModal } from "@/components/ui/CustomModal";
import { ActivityDocumentationView, type DocumentationPhaseId } from "./activity-documentation-view";
import { BacklogPhaseFillForm } from "./backlog-phase-fill-form";
import { DevelopPhaseFillForm } from "./develop-phase-fill-form";
import { DeployPhaseFillForm } from "./deploy-phase-fill-form";
import { TestPhaseFillForm } from "./test-phase-fill-form";
import { ToDoPhaseFillForm } from "./todo-phase-fill-form";
import {
  DOCUMENTATION_BY_CARD_ID,
  getActivityDocumentation,
  type ActivityDocumentation,
} from "./activity-documentation-data";

const FILL_PHASE_TITLES: Partial<Record<DocumentationPhaseId, string>> = {
  backlog: "BACKLOG — documento de requisito",
  "to-do": "TO DO — prontidão para desenvolvimento",
  develop: "DEVELOP — entrega de desenvolvimento",
  test: "TEST — casos de teste",
  deploy: "DEPLOY — deploy",
};

type ActivityDocumentationModalProps = {
  cardId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function ActivityDocumentationModal({
  cardId,
  open,
  onOpenChange,
}: ActivityDocumentationModalProps) {
  const [docsByCard, setDocsByCard] = useState<Record<string, ActivityDocumentation>>(
    DOCUMENTATION_BY_CARD_ID,
  );
  const [fillPhase, setFillPhase] = useState<DocumentationPhaseId | null>(null);

  useEffect(() => {
    if (!open) setFillPhase(null);
  }, [open]);

  if (!cardId) return null;

  const data = docsByCard[cardId] ?? getActivityDocumentation(cardId);
  const fillTitle = fillPhase ? FILL_PHASE_TITLES[fillPhase] : undefined;

  const updateDoc = (patch: Partial<ActivityDocumentation>) => {
    setDocsByCard((prev) => ({
      ...prev,
      [cardId]: { ...(prev[cardId] ?? getActivityDocumentation(cardId)), ...patch },
    }));
    setFillPhase(null);
  };

  return (
    <CustomModal
      open={open}
      onOpenChange={onOpenChange}
      title={fillTitle ?? "Documentação"}
      contentClassName="flex max-h-[min(90vh,820px)] max-w-3xl flex-col overflow-hidden sm:max-w-3xl"
    >
      <div className="-mx-1 flex-1 overflow-y-auto px-1 pb-1">
        {fillPhase === "backlog" ? (
          <BacklogPhaseFillForm
            initial={data.backlog}
            onSave={(backlog) => updateDoc({ backlog })}
            onCancel={() => setFillPhase(null)}
          />
        ) : fillPhase === "to-do" ? (
          <ToDoPhaseFillForm
            initial={data.toDo}
            onSave={(toDo) => updateDoc({ toDo })}
            onCancel={() => setFillPhase(null)}
          />
        ) : fillPhase === "develop" ? (
          <DevelopPhaseFillForm
            cardId={cardId}
            initial={data.develop}
            onSave={(develop) => updateDoc({ develop })}
            onCancel={() => setFillPhase(null)}
          />
        ) : fillPhase === "test" ? (
          <TestPhaseFillForm
            cardId={cardId}
            initial={data.test}
            onSave={(test) => updateDoc({ test })}
            onCancel={() => setFillPhase(null)}
          />
        ) : fillPhase === "deploy" ? (
          <DeployPhaseFillForm
            cardId={cardId}
            initial={data.deploy}
            onSave={(deploy) => updateDoc({ deploy })}
            onCancel={() => setFillPhase(null)}
          />
        ) : (
          <ActivityDocumentationView
            data={data}
            onPreencherFase={(phase) => setFillPhase(phase)}
          />
        )}
      </div>
    </CustomModal>
  );
}
