"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  ArrowLeft,
  Brain,
  ClipboardList,
  Crosshair,
  FileText,
  Flag,
  Target,
  TrendingUp,
  UserRound,
} from "lucide-react";
import { DashboardPanel } from "@/app/(dashboard)/activities/_components/dashboard-panel";
import {
  ActivityDocumentationView,
  type DocumentationConfirmPhaseId,
  type DocumentationFillPhaseId,
} from "@/app/(dashboard)/kanban/_components/activity-documentation-view";
import { BacklogPhaseFillForm } from "@/app/(dashboard)/kanban/_components/backlog-phase-fill-form";
import { TestPhaseFillForm } from "@/app/(dashboard)/kanban/_components/test-phase-fill-form";
import {
  buildMarcarComoFeitoBacklog,
  buildMarcarComoFeitoDeploy,
  buildMarcarComoFeitoDevelop,
  buildMarcarComoFeitoEncerramento,
  buildMarcarComoFeitoTest,
  buildMarcarComoFeitoToDo,
  serializeClearPhaseContent,
  type DocumentationPhaseKey,
  getEmptyActivityDocumentation,
  parseBackendDocumentation,
  serializeBacklogDocumentacao,
  serializeDeployDocumentacao,
  serializeDevelopDocumentacao,
  serializeTestDocumentacao,
  serializeToDoDocumentacao,
} from "@/app/(dashboard)/kanban/_components/activity-documentation-data";
import {
  backlogPassesGate,
  deployPassesGate,
  testPassesGate,
} from "@/app/(dashboard)/kanban/_components/documentation-gate-client";
import {
  canFillPhase,
  canMarkPhaseComplete,
  getDependencyHint,
  getPhaseCompletionMap,
  getPhasesToClear,
} from "@/app/(dashboard)/kanban/_components/documentation-phase-flow";
import { Button } from "@/components/ui/button";
import { CustomModal } from "@/components/ui/CustomModal";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  postKanbanStatus,
  reportKanbanAdvanceFeedback,
  tentarAvancoAutomaticoKanban,
} from "@/lib/priorizacao/kanban-auto-advance";
import { toast } from "sonner";
import {
  documentationPhaseToColumn,
  statusToColumn,
  type KanbanColumnId,
} from "@/lib/priorizacao/kanban-status";
import type { KanbanGatesResponse, Visao360DemandaResponse } from "@/lib/priorizacao/types";

function detailFromPayload(payload: unknown, fallback: string) {
  if (payload && typeof payload === "object" && "detail" in payload && typeof payload.detail === "string") {
    return payload.detail;
  }
  return fallback;
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

function getStatusBadgeClass(status?: string | null) {
  const normalized = normalizeKey(status || "BACKLOG");
  if (normalized === "BACKLOG") return "border-slate-500/35 bg-slate-500/15 text-slate-200";
  if (normalized === "AVALIADO") return "border-violet-500/35 bg-violet-500/15 text-violet-300";
  if (normalized === "EM_DESENVOLVIMENTO")
    return "border-blue-500/35 bg-blue-500/15 text-blue-300";
  if (normalized === "EM_TESTE") return "border-emerald-500/35 bg-emerald-500/15 text-emerald-300";
  if (normalized === "EM_HOMOLOGACAO")
    return "border-amber-500/35 bg-amber-500/15 text-amber-300";
  return "border-cyan-500/35 bg-cyan-500/15 text-cyan-300";
}

function getPriorityBadgeClass(priority?: string | null) {
  const normalized = normalizeKey(priority);
  if (normalized === "ALTA") return "border-rose-500/35 bg-rose-500/15 text-rose-300";
  if (normalized === "MEDIA") return "border-amber-500/35 bg-amber-500/15 text-amber-300";
  if (normalized === "BAIXA") return "border-cyan-500/35 bg-cyan-500/15 text-cyan-300";
  return "border-slate-500/35 bg-slate-500/15 text-slate-300";
}

function getDimensionBadgeClass(dimension?: string | null) {
  const normalized = normalizeKey(dimension);
  if (normalized === "CRITICIDADE") return "border-violet-500/35 bg-violet-500/15 text-violet-300";
  if (normalized === "SEVERIDADE") return "border-blue-500/35 bg-blue-500/15 text-blue-300";
  return "border-slate-500/35 bg-slate-500/15 text-slate-300";
}

function Badge({ className, children }: { className: string; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold",
        className,
      )}
    >
      {children}
    </span>
  );
}

function InfoField({
  label,
  value,
  children,
}: {
  label: string;
  value?: string | number | null;
  children?: ReactNode;
}) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      {children ?? (
        <p className="text-sm font-medium leading-relaxed text-foreground">{value ?? "—"}</p>
      )}
    </div>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  highlight,
}: {
  icon: typeof Target;
  label: string;
  value: ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className="flex min-w-0 flex-col rounded-xl border border-white/10 bg-black/20 p-3">
      <div className="mb-2 flex min-w-0 items-start gap-2 text-muted-foreground">
        <Icon className="mt-0.5 size-3.5 shrink-0" />
        <span className="min-w-0 text-[10px] font-semibold uppercase leading-tight tracking-wide">
          {label}
        </span>
      </div>
      <div
        className={cn(
          "min-w-0 break-words text-sm font-semibold leading-snug",
          highlight && "text-rose-400",
        )}
      >
        {value}
      </div>
    </div>
  );
}

function PanelHeader({
  icon: Icon,
  title,
  accentClass,
  ringClass,
}: {
  icon: typeof FileText;
  title: string;
  accentClass: string;
  ringClass: string;
}) {
  return (
    <div className={cn("flex items-center gap-3 border-b px-5 py-4", accentClass)}>
      <div
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-xl ring-1",
          ringClass,
        )}
      >
        <Icon className="size-5" />
      </div>
      <h2 className="text-base font-semibold tracking-tight">{title}</h2>
    </div>
  );
}

const FILL_PHASE_TITLES: Partial<Record<DocumentationFillPhaseId, string>> = {
  backlog: "BACKLOG — documento de requisito",
  test: "Casos de teste",
};

export default function ActivityDetailPage() {
  const params = useParams<{ id: string }>();
  const activityId = Number(params.id);
  const [view360, setView360] = useState<Visao360DemandaResponse | null>(null);
  const [activePhase, setActivePhase] = useState<DocumentationFillPhaseId | null>(null);
  const [reopenedPhase, setReopenedPhase] = useState<DocumentationPhaseKey | null>(null);
  /** Força remontagem do formulário após reabrir/limpar etapa (estado local não acompanha o fetch). */
  const [formSessionKey, setFormSessionKey] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [kanbanGates, setKanbanGates] = useState<KanbanGatesResponse | null>(null);

  const loadKanbanGates = async () => {
    if (Number.isNaN(activityId)) return;
    try {
      const response = await fetch(`/api/priorizacao/kanban/${activityId}/gates`, {
        cache: "no-store",
      });
      const data = await response.json().catch(() => null);
      if (response.ok) {
        setKanbanGates(data as KanbanGatesResponse);
      }
    } catch {
      setKanbanGates(null);
    }
  };

  const loadDetail = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const viewResponse = await fetch(`/api/priorizacao/demandas/${activityId}/visao-360`, {
        cache: "no-store",
      });

      const viewData = await viewResponse.json().catch(() => null);

      if (!viewResponse.ok) {
        throw new Error(detailFromPayload(viewData, "Não foi possível carregar a atividade."));
      }

      setView360((viewData as Visao360DemandaResponse) ?? null);
      await loadKanbanGates();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível carregar a atividade.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const persistPhaseContent = async (phaseCode: string, conteudo: string) => {
    const response = await fetch(
      `/api/priorizacao/requisitos/${activityId}/documentacao-fase/${phaseCode}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conteudo }),
      },
    );
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(detailFromPayload(data, "Não foi possível guardar a fase documental."));
    }
  };

  useEffect(() => {
    if (Number.isNaN(activityId)) {
      setErrorMessage("ID de atividade inválido.");
      setIsLoading(false);
      return;
    }
    void loadDetail();
  }, [activityId]);

  const docs = useMemo(
    () => parseBackendDocumentation(view360?.documentacao_fase ?? {}),
    [view360?.documentacao_fase],
  );
  const requirementType = useMemo(
    () => normalizeKey(view360?.identificacao?.tipo_requisito),
    [view360?.identificacao?.tipo_requisito],
  );
  const isBugRequirement = requirementType === "BUG";

  const phaseApiCode: Record<DocumentationPhaseKey, string> = {
    backlog: "doc_requisito",
    "to-do": "prontidao_dev",
    develop: "entrega_dev",
    test: "casos_teste",
    deploy: "deploy",
    encerramento: "encerramento",
  };

  const handleSavePhase = async (phaseCode: string, conteudo: string, successMessage = "Gravado no banco de dados.") => {
    try {
      setIsSaving(true);
      setErrorMessage(null);
      await persistPhaseContent(phaseCode, conteudo);
      const advance = await tentarAvancoAutomaticoKanban(activityId, { maxSteps: 1, silent: true });
      reportKanbanAdvanceFeedback(advance, successMessage);
      setActivePhase(null);
      setReopenedPhase(null);
      await loadDetail();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Não foi possível guardar a fase documental.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleCompletarDocumentacaoEsteira = async () => {
    if (!view360) return;
    const titulo = view360.identificacao.titulo;
    try {
      setIsSaving(true);
      setErrorMessage(null);
      if (
        !isBugRequirement &&
        !backlogPassesGate(docs.backlog, { dispensarDocRequisito: false })
      ) {
        await persistPhaseContent(
          "doc_requisito",
          serializeBacklogDocumentacao(buildMarcarComoFeitoBacklog(titulo)),
        );
      }
      if (!testPassesGate(docs.test)) {
        await persistPhaseContent(
          "casos_teste",
          serializeTestDocumentacao(buildMarcarComoFeitoTest(), activityId),
        );
      }
      if (!deployPassesGate(docs.deploy)) {
        await persistPhaseContent(
          "deploy",
          serializeDeployDocumentacao(buildMarcarComoFeitoDeploy(), activityId),
        );
      }
      if (!docs.encerramento?.trim()) {
        await persistPhaseContent("encerramento", buildMarcarComoFeitoEncerramento(docs.encerramento));
      }
      const advance = await tentarAvancoAutomaticoKanban(activityId, { maxSteps: 5, silent: true });
      reportKanbanAdvanceFeedback(advance, "Documentação gravada.", {
        blockedHint: "Documentação gravada. Avanço na esteira bloqueado (gate ou WIP).",
      });
      setActivePhase(null);
      setReopenedPhase(null);
      await loadDetail();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Não foi possível completar a documentação.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const documentationCompletionInput = () => ({
    backlog: docs.backlog ?? getEmptyActivityDocumentation().backlog,
    toDo: docs.toDo,
    develop: docs.develop,
    test: docs.test,
    deploy: docs.deploy,
    encerramento: docs.encerramento,
  });

  const phaseFlowOptions = () => ({
    dispensarBacklogDoc: isBugRequirement,
  });

  const handleCancelFill = useCallback(() => {
    const phase = activePhase;
    const isReopenFlow =
      Boolean(phase) &&
      reopenedPhase === phase &&
      (phase === "backlog" || phase === "test");

    setActivePhase(null);

    if (!isReopenFlow) {
      setReopenedPhase(null);
      return;
    }

    setFormSessionKey((key) => key + 1);
    requestAnimationFrame(() => {
      setActivePhase(phase);
    });
  }, [activePhase, reopenedPhase]);

  const handleReabrirFase = async (phase: DocumentationPhaseKey) => {
    const raw = getPhaseCompletionMap(documentationCompletionInput(), phaseFlowOptions());
    const phasesToClear = getPhasesToClear(phase, raw);
    try {
      setIsSaving(true);
      setErrorMessage(null);
      setActivePhase(null);
      for (const key of phasesToClear) {
        const conteudo = serializeClearPhaseContent(key, activityId);
        const response = await fetch(
          `/api/priorizacao/requisitos/${activityId}/documentacao-fase/${phaseApiCode[key]}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ conteudo }),
          },
        );
        const data = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(detailFromPayload(data, "Não foi possível reabrir a etapa."));
        }
      }

      const targetColumn = documentationPhaseToColumn(phase);
      const currentColumn = (kanbanGates?.coluna_kanban ??
        statusToColumn(view360?.identificacao?.status_atual)) as KanbanColumnId;

      if (targetColumn !== currentColumn) {
        const statusResult = await postKanbanStatus(activityId, targetColumn);
        if (!statusResult.ok) {
          throw new Error(
            statusResult.detail ??
              "Documentação reaberta, mas não foi possível mover o card no Kanban.",
          );
        }
      }

      const docMessage =
        phasesToClear.length > 1
          ? "Etapa limpa. As fases afetadas voltaram para pendente."
          : "Etapa reaberta. As fases posteriores voltaram para pendente.";

      await loadDetail();
      setFormSessionKey((key) => key + 1);

      toast.success(docMessage, {
        description:
          targetColumn !== currentColumn
            ? `Card movido para ${targetColumn} no Kanban.`
            : undefined,
      });

      if (phase === "backlog" || phase === "test") {
        setReopenedPhase(phase);
        setActivePhase(phase);
      } else {
        setReopenedPhase(null);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Não foi possível reabrir a etapa.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handlePreencherFase = (phase: DocumentationFillPhaseId) => {
    if (phase === "backlog" && isBugRequirement) return;
    const raw = getPhaseCompletionMap(documentationCompletionInput(), phaseFlowOptions());
    if (!canFillPhase(phase, raw)) return;
    setReopenedPhase(null);
    setActivePhase(phase);
  };

  const handleMarcarComoFeito = async (phase: DocumentationConfirmPhaseId) => {
    if (!view360) return;
    const titulo = view360.identificacao.titulo;
    try {
      setIsSaving(true);
      setErrorMessage(null);

      const input = documentationCompletionInput();
      if (
        !isBugRequirement &&
        !backlogPassesGate(input.backlog, { dispensarDocRequisito: false })
      ) {
        await persistPhaseContent(
          "doc_requisito",
          serializeBacklogDocumentacao(buildMarcarComoFeitoBacklog(titulo)),
        );
        input.backlog = buildMarcarComoFeitoBacklog(titulo);
      }

      const raw = getPhaseCompletionMap(input, {
        dispensarBacklogDoc: isBugRequirement,
      });
      if (!canMarkPhaseComplete(phase, raw)) {
        toast.error(
          getDependencyHint(phase, raw) ?? "Conclua as etapas anteriores antes de avançar.",
        );
        return;
      }

      if (phase === "to-do") {
        const payload = buildMarcarComoFeitoToDo();
        await persistPhaseContent("prontidao_dev", serializeToDoDocumentacao(payload, activityId));
      } else if (phase === "develop") {
        const payload = buildMarcarComoFeitoDevelop(activityId, titulo);
        await persistPhaseContent(
          "entrega_dev",
          serializeDevelopDocumentacao(payload, activityId),
        );
      } else if (phase === "deploy") {
        const payload = buildMarcarComoFeitoDeploy();
        await persistPhaseContent(
          "deploy",
          serializeDeployDocumentacao(payload, activityId),
        );
        const texto = buildMarcarComoFeitoEncerramento(docs.encerramento);
        await persistPhaseContent("encerramento", texto);
      }

      const advance = await tentarAvancoAutomaticoKanban(activityId, { maxSteps: 1, silent: true });
      reportKanbanAdvanceFeedback(advance, "Fase gravada no banco de dados.");
      setActivePhase(null);
      setReopenedPhase(null);
      await loadDetail();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Não foi possível marcar a fase como feita.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const phaseEditor = useMemo(() => {
    if (!view360) return null;
    if (activePhase === "backlog") {
      return (
        <BacklogPhaseFillForm
          key={`backlog-${formSessionKey}`}
          initial={docs.backlog}
          requirementType={requirementType}
          onSave={(value) => void handleSavePhase("doc_requisito", serializeBacklogDocumentacao(value))}
          onCancel={handleCancelFill}
        />
      );
    }
    if (activePhase === "test") {
      return (
        <TestPhaseFillForm
          key={`test-${formSessionKey}`}
          cardId={String(activityId)}
          initial={docs.test}
          onSave={(value) => void handleSavePhase("casos_teste", serializeTestDocumentacao(value, activityId))}
          onCancel={handleCancelFill}
        />
      );
    }
    return null;
  }, [
    activePhase,
    activityId,
    docs,
    formSessionKey,
    handleCancelFill,
    isSaving,
    requirementType,
    view360,
  ]);
  const fillTitle = activePhase ? FILL_PHASE_TITLES[activePhase] : undefined;

  if (isLoading) {
    return (
      <p className="mx-auto max-w-[1440px] py-8 text-sm text-muted-foreground">
        Carregando detalhe da atividade...
      </p>
    );
  }

  if (!view360) {
    return (
      <div className="mx-auto max-w-[1440px] space-y-4">
        <p className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-red-400">
          {errorMessage || "Atividade não encontrada."}
        </p>
        <Link
          href="/activities"
          className="inline-flex items-center gap-1.5 text-sm text-violet-300 underline-offset-4 hover:text-violet-200 hover:underline"
        >
          <ArrowLeft className="size-3.5" />
          Voltar às atividades
        </Link>
      </div>
    );
  }

  const identificacao = view360.identificacao;
  const origem = view360.origem_demanda;
  const estruturacao = view360.estruturacao_ia;
  const avaliacao = view360.avaliacao;
  const project = identificacao.projeto;
  const emptyDocs = getEmptyActivityDocumentation();
  const scoreDisplay =
    typeof avaliacao.score === "number" && !Number.isNaN(avaliacao.score)
      ? avaliacao.score.toFixed(2)
      : avaliacao.score ?? "—";

  return (
    <div className="mx-auto w-full max-w-[1440px] space-y-5 pb-8">
      <div className="flex items-start gap-4">
        <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600/30 to-indigo-600/20 ring-1 ring-violet-500/30">
          <ClipboardList className="size-6 text-violet-300" />
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">Detalhe da atividade</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Hub operacional com leitura consolidada e registro de documentação por fase.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <DashboardPanel className="overflow-hidden border-blue-500/10">
          <PanelHeader
            icon={FileText}
            title="Identificação da atividade"
            accentClass="border-blue-500/10 bg-gradient-to-r from-blue-500/[0.06] to-transparent"
            ringClass="bg-blue-500/15 text-blue-300 ring-blue-500/25"
          />
          <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
            <InfoField label="ID" value={identificacao.id_requisito} />
            <InfoField label="Tipo">
              <Badge className={getTypeBadgeClass(identificacao.tipo_requisito)}>
                {identificacao.tipo_requisito}
              </Badge>
            </InfoField>
            <InfoField label="Projeto" value={project?.nome_projeto} />
            <InfoField label="Responsável pelo cadastro" value={origem.perfil_solicitante} />
            <InfoField label="Título" value={identificacao.titulo} />
            <InfoField label="Status atual">
              <Badge className={getStatusBadgeClass(identificacao.status_atual)}>
                {identificacao.status_atual}
              </Badge>
            </InfoField>
            <InfoField label="Versão do projeto">
              <Badge className="border-slate-500/35 bg-slate-500/15 text-slate-200">
                {project?.versao_atual || "—"}
              </Badge>
            </InfoField>
          </div>
        </DashboardPanel>

        <DashboardPanel className="overflow-hidden border-violet-500/10">
          <PanelHeader
            icon={Brain}
            title="Estruturação da IA"
            accentClass="border-violet-500/10 bg-gradient-to-r from-violet-500/[0.06] to-transparent"
            ringClass="bg-violet-500/15 text-violet-300 ring-violet-500/25"
          />
          <div className="divide-y divide-white/10 p-5">
            <div className="pb-4">
              <InfoField label="Título sugerido" value={estruturacao.titulo_requisito} />
            </div>
            <div className="py-4">
              <InfoField label="Descrição estruturada">
                <p className="max-h-40 overflow-y-auto text-sm leading-relaxed text-foreground">
                  {estruturacao.descricao_requisito || "—"}
                </p>
              </InfoField>
            </div>
            <div className="grid grid-cols-1 gap-4 py-4 sm:grid-cols-2">
              <InfoField label="Tipo identificado">
                <Badge className={getTypeBadgeClass(estruturacao.tipo_requisito)}>
                  {estruturacao.tipo_requisito}
                </Badge>
              </InfoField>
              <InfoField label="Objetivo" value={estruturacao.objetivo} />
            </div>
            <div className="pt-4">
              <InfoField label="Finalidade">
                <p className="max-h-32 overflow-y-auto text-sm leading-relaxed text-foreground">
                  {estruturacao.finalidade || "—"}
                </p>
              </InfoField>
            </div>
          </div>
        </DashboardPanel>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <DashboardPanel className="overflow-hidden border-amber-500/10 xl:col-span-2">
          <PanelHeader
            icon={Crosshair}
            title="Avaliação e plotagem"
            accentClass="border-amber-500/10 bg-gradient-to-r from-amber-500/[0.06] to-transparent"
            ringClass="bg-amber-500/15 text-amber-300 ring-amber-500/25"
          />
          <div className="space-y-4 p-5">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 2xl:grid-cols-6">
              <MetricTile icon={Target} label="coordenada_x" value={avaliacao.coordenada_x ?? "—"} />
              <MetricTile icon={Target} label="coordenada_y" value={avaliacao.coordenada_y ?? "—"} />
              <MetricTile
                icon={Crosshair}
                label="Eixos"
                value={
                  <span className="text-xs leading-snug sm:text-sm">{avaliacao.eixos || "—"}</span>
                }
              />
              <MetricTile
                icon={Flag}
                label="Prioridade"
                value={
                  <Badge className={getPriorityBadgeClass(avaliacao.prioridade_categorica)}>
                    {avaliacao.prioridade_categorica}
                  </Badge>
                }
              />
              <MetricTile
                icon={TrendingUp}
                label="Score"
                value={scoreDisplay}
                highlight={normalizeKey(avaliacao.prioridade_categorica) === "ALTA"}
              />
              <MetricTile icon={UserRound} label="Avaliador" value={avaliacao.usuario_avaliador || "—"} />
            </div>

            <div className="overflow-x-auto rounded-xl border border-white/10">
              <Table className="min-w-[640px]">
                <TableHeader>
                  <TableRow className="border-white/10 bg-white/[0.03] hover:bg-white/[0.03]">
                    <TableHead className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Pergunta
                    </TableHead>
                    <TableHead className="w-36 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Dimensão
                    </TableHead>
                    <TableHead className="w-20 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Valor
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {view360.respostas.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
                        Nenhuma resposta registada.
                      </TableCell>
                    </TableRow>
                  ) : (
                    view360.respostas.map((resposta) => (
                      <TableRow
                        key={`${resposta.id_pergunta}-${resposta.dimensao}`}
                        className="border-white/10 transition-colors hover:bg-white/[0.04]"
                      >
                        <TableCell className="max-w-[420px] text-sm leading-relaxed">
                          {resposta.texto}
                        </TableCell>
                        <TableCell>
                          <Badge className={getDimensionBadgeClass(resposta.dimensao)}>
                            {resposta.dimensao}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center text-sm font-bold tabular-nums text-amber-300">
                          {resposta.valor_resposta}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </DashboardPanel>

        <DashboardPanel className="overflow-hidden border-emerald-500/10">
          <div className="border-b border-emerald-500/10 bg-gradient-to-r from-emerald-500/[0.06] to-transparent px-5 py-4">
            <div className="flex items-start gap-3">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/25">
                <FileText className="size-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold tracking-tight">Documentação por fase</h2>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  Ao salvar cada fase, a esteira avança automaticamente se o gate e o WIP da coluna
                  de destino permitirem.
                </p>
              </div>
            </div>
          </div>

          <div className="p-5">
            <div className="space-y-4">
              {kanbanGates && kanbanGates.falta_documentacao.length > 0 ? (
                <div className="rounded-xl border border-amber-500/35 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                  <p className="font-semibold">
                    Gate documental na coluna {kanbanGates.coluna_kanban} — não é possível avançar
                    ainda
                  </p>
                  <ul className="mt-2 list-inside list-disc text-xs leading-relaxed text-amber-100/90">
                    {kanbanGates.falta_documentacao.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="mt-3 border-amber-500/40 bg-amber-500/10 text-amber-100 hover:bg-amber-500/20"
                    disabled={isSaving}
                    onClick={() => void handleCompletarDocumentacaoEsteira()}
                  >
                    Completar documentação mínima da esteira
                  </Button>
                </div>
              ) : kanbanGates?.pode_avancar_documentacao ? (
                <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                  Gate documental liberado para avançar de {kanbanGates.coluna_kanban} para{" "}
                  {kanbanGates.proxima_coluna ?? "—"}.
                </p>
              ) : null}
              <ActivityDocumentationView
                data={{
                  backlog: docs.backlog ?? emptyDocs.backlog,
                  toDo: docs.toDo,
                  develop: docs.develop,
                  test: docs.test,
                  deploy: docs.deploy,
                  encerramento: docs.encerramento,
                }}
                  requirementType={requirementType}
                onPreencherFase={handlePreencherFase}
                onMarcarComoFeito={(phase) => void handleMarcarComoFeito(phase)}
                onReabrirFase={(phase) => void handleReabrirFase(phase)}
                reopenedPhase={reopenedPhase}
                isSaving={isSaving}
              />
            </div>
          </div>
        </DashboardPanel>
      </div>

      <CustomModal
        open={Boolean(activePhase)}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setActivePhase(null);
          }
        }}
        title={fillTitle ?? "Documentação"}
        contentClassName="flex max-h-[min(90vh,820px)] max-w-xl flex-col overflow-hidden sm:max-w-xl"
      >
        <div className="-mx-1 flex-1 overflow-y-auto px-1 pb-1">{phaseEditor}</div>
      </CustomModal>
    </div>
  );
}
