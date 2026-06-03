"use client";

import { useMemo, type ReactNode } from "react";
import {
  Check,
  ChevronRight,
  ClipboardList,
  Code2,
  FlaskConical,
  ListChecks,
  Pencil,
  Rocket,
  RotateCcw,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import {
  isBacklogDocumentacaoEmpty,
  type ActivityDocumentation,
  type DocumentationPhaseKey,
  type BacklogDocumentacao,
  type TestDocumentacao,
} from "./activity-documentation-data";
import {
  getDependencyHint,
  getDocumentationFlowState,
  type PhaseFlowStatus,
} from "./documentation-phase-flow";
import { CASO_TESTE_STATUS_OPTIONS } from "./test-case-types";

export type DocumentationPhaseId = "backlog" | "to-do" | "develop" | "test" | "deploy";
export type DocumentationFillPhaseId = "backlog" | "test";
export type DocumentationConfirmPhaseId = Exclude<
  DocumentationPhaseId,
  DocumentationFillPhaseId
>;

const INTRO_TEXT =
  "Para avançar no Kanban, cada coluna valida a documentação gravada no banco (gate). BACKLOG e TEST precisam de conteúdo completo; TO DO, DEVELOP e DEPLOY podem ser confirmadas aqui; DONE encerra ao concluir DEPLOY.";

type ActivityDocumentationViewProps = {
  data: ActivityDocumentation;
  requirementType?: string | null;
  onPreencherFase?: (phase: DocumentationFillPhaseId) => void;
  onMarcarComoFeito?: (phase: DocumentationConfirmPhaseId) => void;
  onReabrirFase?: (phase: DocumentationPhaseKey) => void;
  reopenedPhase?: DocumentationPhaseKey | null;
  isSaving?: boolean;
};

const FILL_BUTTON_CLASS =
  "h-8 shrink-0 rounded-lg border-violet-500/30 bg-violet-500/10 px-3 text-violet-200 hover:bg-violet-500/20 hover:text-violet-100";

const CONFIRM_BUTTON_CLASS =
  "h-8 shrink-0 rounded-lg border-emerald-500/30 bg-emerald-500/10 px-3 text-emerald-200 hover:bg-emerald-500/25 hover:text-emerald-100";

const REOPEN_BUTTON_CLASS =
  "h-8 shrink-0 rounded-lg border-amber-500/30 bg-amber-500/10 px-3 text-amber-200 hover:bg-amber-500/20 hover:text-amber-100";

const CLEAR_STALE_BUTTON_CLASS =
  "h-8 shrink-0 rounded-lg border-orange-500/30 bg-orange-500/10 px-3 text-orange-200 hover:bg-orange-500/20 hover:text-orange-100";

function formatDateBr(iso: string) {
  if (!iso) return "—";
  const [year, month, day] = iso.split("-");
  if (!year || !month || !day) return iso;
  return `${day}/${month}/${year}`;
}

function parsePhaseTitle(title: string) {
  const [phase, ...rest] = title.split(" — ");
  return {
    phase: phase?.trim() || title,
    description: rest.join(" — ").trim() || "",
  };
}

function PhaseIcon({ phase }: { phase: string }) {
  const normalized = phase.toUpperCase();
  const className = "size-4";
  if (normalized.startsWith("BACKLOG")) return <ClipboardList className={cn(className, "text-slate-300")} />;
  if (normalized.startsWith("TO DO")) return <ListChecks className={cn(className, "text-blue-300")} />;
  if (normalized.startsWith("DEVELOP")) return <Code2 className={cn(className, "text-violet-300")} />;
  if (normalized.startsWith("TEST")) return <FlaskConical className={cn(className, "text-amber-300")} />;
  if (normalized.startsWith("DEPLOY")) return <Rocket className={cn(className, "text-emerald-300")} />;
  if (normalized.startsWith("DONE")) return <Check className={cn(className, "text-emerald-300")} />;
  return <ClipboardList className={className} />;
}

function statusBadge(flowStatus: PhaseFlowStatus) {
  if (flowStatus === "done") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/35 bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
        <Check className="size-3" />
        Feito
      </span>
    );
  }
  if (flowStatus === "reopened") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/35 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold text-amber-200">
        <RotateCcw className="size-3" />
        Reaberta
      </span>
    );
  }
  if (flowStatus === "blocked") {
    return (
      <span className="inline-flex rounded-md border border-white/15 bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
        Bloqueada
      </span>
    );
  }
  if (flowStatus === "stale") {
    return (
      <span className="inline-flex rounded-md border border-orange-500/30 bg-orange-500/10 px-2 py-0.5 text-[10px] font-medium text-orange-200">
        Pendente
      </span>
    );
  }
  return (
    <span className="inline-flex rounded-md border border-blue-500/25 bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-200">
      Disponível
    </span>
  );
}

function DocField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="text-sm whitespace-pre-wrap">{value || "—"}</p>
    </div>
  );
}

function DocList({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">—</p>
      ) : (
        <ul className="list-inside list-disc space-y-0.5 text-sm">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ReabrirButton({
  isSaving,
  onReabrir,
}: {
  isSaving?: boolean;
  onReabrir?: () => void;
}) {
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={REOPEN_BUTTON_CLASS}
      disabled={isSaving}
      onClick={onReabrir}
    >
      <RotateCcw className="size-3.5" />
      Reabrir
    </Button>
  );
}

function LimparEtapaButton({
  isSaving,
  onLimpar,
}: {
  isSaving?: boolean;
  onLimpar?: () => void;
}) {
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={CLEAR_STALE_BUTTON_CLASS}
      disabled={isSaving}
      onClick={onLimpar}
    >
      <Trash2 className="size-3.5" />
      Limpar etapa
    </Button>
  );
}

function PhaseRowShell({
  title,
  flowStatus,
  dependencyHint,
  children,
  action,
  statusBadgeOverride,
}: {
  title: string;
  flowStatus: PhaseFlowStatus;
  dependencyHint?: string | null;
  children?: ReactNode;
  action?: ReactNode;
  statusBadgeOverride?: ReactNode;
}) {
  const { phase, description } = parsePhaseTitle(title);
  const isDone = flowStatus === "done";
  const isBlocked = flowStatus === "blocked";
  const isReopened = flowStatus === "reopened";
  const isStale = flowStatus === "stale";

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border bg-black/15 transition-colors",
        isDone && "border-emerald-500/25 bg-emerald-500/[0.04]",
        isReopened && "border-amber-500/30 bg-amber-500/[0.06]",
        isStale && "border-orange-500/25 bg-orange-500/[0.04]",
        isBlocked && "border-white/10 opacity-60",
        flowStatus === "available" && "border-white/10",
      )}
    >
      <div className="flex items-center justify-between gap-3 p-3">
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={cn(
              "flex size-9 shrink-0 items-center justify-center rounded-lg border bg-white/[0.04]",
              isDone && "border-emerald-500/25",
              isReopened && "border-amber-500/30",
              isStale && "border-orange-500/30",
              !isDone && !isReopened && !isStale && "border-white/10",
            )}
          >
            <PhaseIcon phase={phase} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold leading-tight">{phase}</p>
              {statusBadgeOverride ?? statusBadge(flowStatus)}
            </div>
            {description ? (
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{description}</p>
            ) : null}
            {dependencyHint ? (
              <p className="mt-1 text-xs text-amber-200/80">{dependencyHint}</p>
            ) : null}
          </div>
        </div>
        {action ?? null}
      </div>
      {children ? <div className="border-t border-white/10 px-3 pb-3 pt-2">{children}</div> : null}
    </div>
  );
}

function FillPhaseActions({
  flowStatus,
  isSaving,
  onPreencher,
  onReabrir,
}: {
  flowStatus: PhaseFlowStatus;
  isSaving?: boolean;
  onPreencher?: () => void;
  onReabrir?: () => void;
}) {
  if (flowStatus === "blocked") {
    return (
      <Button
        type="button"
        variant="outline"
        size="sm"
        className={FILL_BUTTON_CLASS}
        disabled
      >
        <Pencil className="size-3.5" />
        Preencher
      </Button>
    );
  }

  if (flowStatus === "stale") {
    return <LimparEtapaButton isSaving={isSaving} onLimpar={onReabrir} />;
  }

  if (flowStatus === "done") {
    return <ReabrirButton isSaving={isSaving} onReabrir={onReabrir} />;
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={FILL_BUTTON_CLASS}
      disabled={isSaving}
      onClick={onPreencher}
    >
      <Pencil className="size-3.5" />
      Preencher
    </Button>
  );
}

function ConfirmPhaseActions({
  flowStatus,
  isSaving,
  onMarcar,
  onReabrir,
  buttonClassName = CONFIRM_BUTTON_CLASS,
}: {
  flowStatus: PhaseFlowStatus;
  isSaving?: boolean;
  onMarcar?: () => void;
  onReabrir?: () => void;
  buttonClassName?: string;
}) {
  if (flowStatus === "blocked") {
    return (
      <Button
        type="button"
        variant="outline"
        size="sm"
        className={buttonClassName}
        disabled
      >
        <Check className="size-3.5" />
        Marcar como feito
      </Button>
    );
  }

  if (flowStatus === "stale") {
    return <LimparEtapaButton isSaving={isSaving} onLimpar={onReabrir} />;
  }

  if (flowStatus === "done") {
    return <ReabrirButton isSaving={isSaving} onReabrir={onReabrir} />;
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={buttonClassName}
      disabled={isSaving}
      onClick={onMarcar}
    >
      <Check className="size-3.5" />
      Marcar como feito
    </Button>
  );
}

function BacklogPhaseSection({
  backlog,
  requirementType,
  flowStatus,
  dependencyHint,
  isSaving,
  onPreencher,
  onReabrir,
}: {
  backlog: BacklogDocumentacao;
  requirementType?: string | null;
  flowStatus: PhaseFlowStatus;
  dependencyHint?: string | null;
  isSaving?: boolean;
  onPreencher?: () => void;
  onReabrir?: () => void;
}) {
  const title = "BACKLOG — documento de requisito";
  const isBug = (requirementType || "").trim().toUpperCase() === "BUG";
  const backlogEmpty = isBacklogDocumentacaoEmpty(backlog);
  const backlogDispensado = isBug && backlogEmpty;
  const showContent = flowStatus === "done" && !backlogDispensado;

  const dispensadoBadge = (
    <span className="inline-flex items-center gap-1 rounded-md border border-slate-500/35 bg-slate-500/15 px-2 py-0.5 text-[10px] font-semibold text-slate-300">
      Dispensado
    </span>
  );

  return (
    <PhaseRowShell
      title={title}
      flowStatus={flowStatus}
      dependencyHint={dependencyHint}
      statusBadgeOverride={backlogDispensado ? dispensadoBadge : undefined}
      action={
        backlogDispensado ? null : (
          <FillPhaseActions
            flowStatus={flowStatus}
            isSaving={isSaving}
            onPreencher={onPreencher}
            onReabrir={onReabrir}
          />
        )
      }
    >
      {backlogDispensado ? (
        <p className="text-sm text-muted-foreground">
          Classificação feita na entrada da atividade; documento de requisito não é obrigatório
          para bugs. Pode avançar na esteira sem preencher esta fase.
        </p>
      ) : null}
      {showContent ? (
        <Collapsible defaultOpen={false} className="group/phase space-y-3">
          <CollapsibleTrigger className="flex w-full items-center gap-2 text-left text-xs text-muted-foreground hover:text-foreground">
            <ChevronRight className="size-3.5 shrink-0 transition-transform group-data-[state=open]/phase:rotate-90" />
            Ver documentação preenchida
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="space-y-4 rounded-lg border border-white/10 bg-black/20 p-4">
              <DocField label="Nome da funcionalidade" value={backlog.nomeFuncionalidade} />
              <DocField label="Descrição detalhada" value={backlog.descricaoDetalhada} />
              <DocField label="Restrições" value={backlog.restricoes} />
              <DocList label="Requisitos funcionais (RF)" items={backlog.requisitosFuncionais} />
              <DocList
                label="Requisitos não funcionais (RNF)"
                items={backlog.requisitosNaoFuncionais}
              />
              {!isBug ? (
                <>
                  <DocList label="Regras de negócio" items={backlog.regrasNegocio} />
                  <DocList label="Critérios de aceitação" items={backlog.criteriosAceitacao} />
                </>
              ) : null}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </PhaseRowShell>
  );
}

function ConfirmPhaseSection({
  title,
  flowStatus,
  dependencyHint,
  isSaving,
  onMarcar,
  onReabrir,
  summary,
}: {
  title: string;
  flowStatus: PhaseFlowStatus;
  dependencyHint?: string | null;
  isSaving?: boolean;
  onMarcar?: () => void;
  onReabrir?: () => void;
  summary?: string;
}) {
  return (
    <PhaseRowShell
      title={title}
      flowStatus={flowStatus}
      dependencyHint={dependencyHint}
      action={
        <ConfirmPhaseActions
          flowStatus={flowStatus}
          isSaving={isSaving}
          onMarcar={onMarcar}
          onReabrir={onReabrir}
        />
      }
    >
      {flowStatus === "done" && summary ? (
        <p className="text-sm text-muted-foreground">{summary}</p>
      ) : null}
    </PhaseRowShell>
  );
}

function statusLabel(status: string) {
  return (
    CASO_TESTE_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status
  );
}

function TestPhaseSection({
  test,
  flowStatus,
  dependencyHint,
  isSaving,
  onPreencher,
  onReabrir,
}: {
  test?: TestDocumentacao;
  flowStatus: PhaseFlowStatus;
  dependencyHint?: string | null;
  isSaving?: boolean;
  onPreencher?: () => void;
  onReabrir?: () => void;
}) {
  const title = "TEST — casos de teste";
  const showContent = flowStatus === "done" && test;

  return (
    <PhaseRowShell
      title={title}
      flowStatus={flowStatus}
      dependencyHint={dependencyHint}
      action={
        <FillPhaseActions
          flowStatus={flowStatus}
          isSaving={isSaving}
          onPreencher={onPreencher}
          onReabrir={onReabrir}
        />
      }
    >
      {showContent ? (
        <Collapsible defaultOpen={false} className="group/phase space-y-3">
          <CollapsibleTrigger className="flex w-full items-center gap-2 text-left text-xs text-muted-foreground hover:text-foreground">
            <ChevronRight className="size-3.5 shrink-0 transition-transform group-data-[state=open]/phase:rotate-90" />
            Ver casos de teste preenchidos
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="space-y-3">
              {test!.casos.map((caso, index) => (
                <div key={index} className="space-y-2 rounded-lg border border-white/10 bg-black/20 p-3">
                  <p className="text-sm font-semibold">Caso de teste {index + 1}</p>
                  <DocField label="Resumo" value={caso.resumo} />
                  <DocField label="Status" value={statusLabel(caso.status)} />
                  <DocField label="Executor" value={caso.executor} />
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </PhaseRowShell>
  );
}

function DonePhaseSection({
  encerramento,
  flowStatus,
  dependencyHint,
  isSaving,
  onReabrir,
}: {
  encerramento?: string;
  flowStatus: PhaseFlowStatus;
  dependencyHint?: string | null;
  isSaving?: boolean;
  onReabrir?: () => void;
}) {
  const title = "DONE — encerramento";

  return (
    <PhaseRowShell
      title={title}
      flowStatus={flowStatus}
      dependencyHint={dependencyHint}
      action={
        flowStatus === "stale" ? (
          <LimparEtapaButton isSaving={isSaving} onLimpar={onReabrir} />
        ) : undefined
      }
    >
      {flowStatus === "done" ? (
        <p className="text-sm whitespace-pre-wrap text-muted-foreground">
          {encerramento?.trim() || "Atividade encerrada na esteira Kanban."}
        </p>
      ) : flowStatus === "available" ? (
        <p className="text-sm text-muted-foreground">
          Será concluída automaticamente ao marcar DEPLOY como feito.
        </p>
      ) : null}
    </PhaseRowShell>
  );
}

export function ActivityDocumentationView({
  data,
  requirementType = null,
  onPreencherFase,
  onMarcarComoFeito,
  onReabrirFase,
  reopenedPhase = null,
  isSaving,
}: ActivityDocumentationViewProps) {
  const isBug = (requirementType || "").trim().toUpperCase() === "BUG";
  const flow = useMemo(
    () =>
      getDocumentationFlowState(data, reopenedPhase, {
        dispensarBacklogDoc: isBug,
      }),
    [data, reopenedPhase, isBug],
  );

  const status = (phase: DocumentationPhaseKey) => flow.statusByPhase[phase];

  const hint = (phase: DocumentationPhaseKey) => {
    const flowStatus = status(phase);
    if (flowStatus !== "blocked" && flowStatus !== "stale") return null;
    return getDependencyHint(phase, flow.raw);
  };

  return (
    <div className="space-y-3">
      {flow.hasStalePhases ? (
        <p className="rounded-lg border border-orange-500/30 bg-orange-500/10 px-3 py-2 text-xs leading-relaxed text-orange-100">
          Existem etapas marcadas fora de ordem (sem BACKLOG ou etapas anteriores concluídas).
          Use <span className="font-semibold">Limpar etapa</span> em cada uma antes de seguir o fluxo.
        </p>
      ) : null}
      <p className="rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 text-xs leading-relaxed text-muted-foreground">
        {INTRO_TEXT}
      </p>

      <BacklogPhaseSection
        backlog={data.backlog}
        requirementType={requirementType}
        flowStatus={status("backlog")}
        dependencyHint={hint("backlog")}
        isSaving={isSaving}
        onPreencher={() => onPreencherFase?.("backlog")}
        onReabrir={() => onReabrirFase?.("backlog")}
      />

      <ConfirmPhaseSection
        title="TO DO — prontidão para desenvolvimento"
        flowStatus={status("to-do")}
        dependencyHint={hint("to-do")}
        isSaving={isSaving}
        onMarcar={() => onMarcarComoFeito?.("to-do")}
        onReabrir={() => onReabrirFase?.("to-do")}
        summary={
          flow.effective["to-do"]
            ? `Prontidão confirmada${data.toDo?.dataProntidao ? ` em ${formatDateBr(data.toDo.dataProntidao)}` : ""}.`
            : undefined
        }
      />

      <ConfirmPhaseSection
        title="DEVELOP — entrega de desenvolvimento"
        flowStatus={status("develop")}
        dependencyHint={hint("develop")}
        isSaving={isSaving}
        onMarcar={() => onMarcarComoFeito?.("develop")}
        onReabrir={() => onReabrirFase?.("develop")}
        summary={
          flow.effective.develop
            ? `Desenvolvimento confirmado${data.develop?.dataEntregaTeste ? ` em ${formatDateBr(data.develop.dataEntregaTeste)}` : ""}.`
            : undefined
        }
      />

      <TestPhaseSection
        test={data.test}
        flowStatus={status("test")}
        dependencyHint={hint("test")}
        isSaving={isSaving}
        onPreencher={() => onPreencherFase?.("test")}
        onReabrir={() => onReabrirFase?.("test")}
      />

      <ConfirmPhaseSection
        title="DEPLOY — deploy"
        flowStatus={status("deploy")}
        dependencyHint={hint("deploy")}
        isSaving={isSaving}
        onMarcar={() => onMarcarComoFeito?.("deploy")}
        onReabrir={() => onReabrirFase?.("deploy")}
        summary={
          flow.effective.deploy
            ? `Deploy confirmado${data.deploy?.dataDeploy ? ` em ${formatDateBr(data.deploy.dataDeploy)}` : ""}.`
            : undefined
        }
      />

      <DonePhaseSection
        encerramento={data.encerramento}
        flowStatus={status("encerramento")}
        dependencyHint={hint("encerramento")}
        isSaving={isSaving}
        onReabrir={() => onReabrirFase?.("encerramento")}
      />
    </div>
  );
}
