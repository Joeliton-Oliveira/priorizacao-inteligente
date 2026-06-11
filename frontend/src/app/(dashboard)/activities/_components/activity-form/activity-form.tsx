"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  Bug,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  FolderKanban,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
  User,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ACTIVITY_FORM_STORAGE_KEY,
  INITIAL_ACTIVITY_FORM_DATA,
  parsePersistedDraftJson,
  serializeDraft,
  type ActivityFormData,
} from "@/lib/activity-form-draft";
import { buildAnaliseRequestBody } from "@/lib/priorizacao/map-form-to-analise";
import type {
  AnaliseRequisitoResponse,
  ProjetoListItem,
  SalvarAvaliacaoResponse,
} from "@/lib/priorizacao/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CustomModal } from "@/components/ui/CustomModal";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AiAnalysisStep } from "./ai-analysis-step";
import { ActivityFormStepper } from "./activity-form-stepper";
import {
  FormField,
  FormSection,
  FormTextareaWithCounter,
  formControlClassName,
} from "./activity-form-ui";
import {
  DEMAND_TYPE_OPTIONS,
  IMPACT_OPTIONS,
  FREQUENCY_OPTIONS,
  FORM_STEPS,
  URGENCY_OPTIONS,
} from "./options";

export type { ActivityFormData };

type ProjectOption = {
  id: string;
  name: string;
};

type InlineProjectFormState = {
  nome_projeto: string;
  descricao: string;
  responsavel: string;
  tipo_origem: "novo" | "existente";
  versao_atual: string;
  status_projeto: "ativo" | "arquivado" | "descontinuado";
};

const INITIAL_INLINE_PROJECT_STATE: InlineProjectFormState = {
  nome_projeto: "",
  descricao: "",
  responsavel: "",
  tipo_origem: "novo",
  versao_atual: "",
  status_projeto: "ativo",
};

function readDraft(): { formData: ActivityFormData; step: number } | null {
  if (typeof window === "undefined") return null;
  return parsePersistedDraftJson(
    window.localStorage.getItem(ACTIVITY_FORM_STORAGE_KEY),
  );
}

function clearDraft() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(ACTIVITY_FORM_STORAGE_KEY);
  } catch {
    // ignore
  }
}

function extractDetail(data: unknown, fallback: string) {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = data.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }

  return fallback;
}

function mapProjects(data: ProjetoListItem[]): ProjectOption[] {
  return data.map((project) => {
    const parts = [project.nome_projeto];
    if (project.versao_atual) {
      parts.push(`v${project.versao_atual}`);
    }
    if (project.status_projeto) {
      parts.push(project.status_projeto);
    }

    return {
      id: String(project.id_projeto),
      name: parts.join(" · "),
    };
  });
}

export function ActivityForm() {
  const [formData, setFormData] = useState<ActivityFormData>(INITIAL_ACTIVITY_FORM_DATA);
  const [currentStep, setCurrentStep] = useState(1);
  const [projects, setProjects] = useState<ProjectOption[]>([]);
  const [isProjectsLoading, setIsProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [analise, setAnalise] = useState<AnaliseRequisitoResponse | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [evaluatorName, setEvaluatorName] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [stepError, setStepError] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [inlineProjectOpen, setInlineProjectOpen] = useState(false);
  const [inlineProjectState, setInlineProjectState] = useState(INITIAL_INLINE_PROJECT_STATE);
  const [inlineProjectError, setInlineProjectError] = useState<string | null>(null);
  const [successModalOpen, setSuccessModalOpen] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<SalvarAvaliacaoResponse | null>(null);

  const loadProjects = useCallback(async () => {
    setIsProjectsLoading(true);
    setProjectsError(null);

    try {
      const response = await fetch("/api/priorizacao/projetos", {
        cache: "no-store",
      });
      const data = (await response.json().catch(() => [])) as
        | ProjetoListItem[]
        | { detail?: string };

      if (!response.ok) {
        throw new Error(
          extractDetail(data, "Não foi possível carregar os projetos cadastrados."),
        );
      }

      setProjects(mapProjects(Array.isArray(data) ? data : []));
    } catch (error) {
      setProjects([]);
      setProjectsError(
        error instanceof Error
          ? error.message
          : "Não foi possível carregar os projetos cadastrados.",
      );
    } finally {
      setIsProjectsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (!formData.projectId.trim() || projects.length === 0) return;

    const hasSelectedProject = projects.some(
      (project) => project.id === formData.projectId,
    );

    if (!hasSelectedProject) {
      setFormData((prev) => ({ ...prev, projectId: "" }));
    }
  }, [formData.projectId, projects]);

  useEffect(() => {
    const draft = readDraft();
    if (draft) {
      setFormData(draft.formData);
      setCurrentStep(draft.step);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;

    const id = window.setTimeout(() => {
      try {
        window.localStorage.setItem(
          ACTIVITY_FORM_STORAGE_KEY,
          serializeDraft(formData, currentStep),
        );
      } catch {
        // ignore
      }
    }, 300);

    return () => window.clearTimeout(id);
  }, [currentStep, formData, hydrated]);

  const currentStepMeta = FORM_STEPS[currentStep - 1];
  const isLastStep = currentStep === FORM_STEPS.length;
  const canAnalyzeWithAi =
    formData.description.trim() !== "" &&
    formData.expectedResult.trim() !== "" &&
    formData.projectId.trim() !== "";

  const validateStep = (step: number) => {
    if (step === 1 && !formData.description.trim()) {
      return "Informe a descrição da demanda antes de avançar.";
    }

    return null;
  };

  const handleNextStep = () => {
    const error = validateStep(currentStep);
    if (error) {
      setStepError(error);
      return;
    }

    setStepError(null);
    setAnalyzeError(null);
    setValidationError(null);
    setCurrentStep((prev) => Math.min(prev + 1, FORM_STEPS.length));
  };

  const handlePreviousStep = () => {
    setStepError(null);
    setAnalyzeError(null);
    setValidationError(null);
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleStepClick = (targetStep: number) => {
    if (targetStep === currentStep) return;

    if (targetStep > currentStep) {
      for (let step = currentStep; step < targetStep; step += 1) {
        const error = validateStep(step);
        if (error) {
          setStepError(error);
          return;
        }
      }
    }

    setStepError(null);
    setAnalyzeError(null);
    setValidationError(null);
    setCurrentStep(targetStep);
  };

  const resetAll = useCallback(() => {
    setFormData(INITIAL_ACTIVITY_FORM_DATA);
    setCurrentStep(1);
    setAnalise(null);
    setAnswers({});
    setEvaluatorName("");
    setStepError(null);
    setAnalyzeError(null);
    setValidationError(null);
    clearDraft();
  }, []);

  const handleAnalyzeWithAI = async () => {
    if (!formData.description.trim()) {
      setAnalyzeError("Informe a descrição da demanda antes de analisar.");
      return;
    }

    if (!formData.projectId.trim()) {
      setAnalyzeError("Selecione um projeto antes de analisar a demanda.");
      return;
    }

    setStepError(null);
    setAnalyzeError(null);
    setValidationError(null);
    setIsAnalyzing(true);

    try {
      const payload = {
        ...buildAnaliseRequestBody(formData),
        formDraft: formData,
      };

      const response = await fetch("/api/priorizacao/analise", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(extractDetail(data, "Não foi possível analisar com IA."));
      }

      setAnalise(data as AnaliseRequisitoResponse);
      setAnswers({});
      setEvaluatorName(formData.requesterId.trim());
    } catch (error) {
      setAnalyzeError(
        error instanceof Error ? error.message : "Erro ao analisar com IA.",
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveAssessment = async () => {
    if (!analise) return;

    const trimmedEvaluator = evaluatorName.trim();
    if (!trimmedEvaluator) {
      setValidationError("Informe o responsável pela avaliação.");
      return;
    }

    const trimmedProjectId = formData.projectId.trim();
    if (!trimmedProjectId) {
      setValidationError("Selecione um projeto antes de salvar a avaliação.");
      return;
    }

    const missing = analise.perguntas_avaliacao.filter(
      (p) => answers[p.id_pergunta] === undefined,
    );
    if (missing.length > 0) {
      setValidationError("Responda todas as perguntas antes de salvar.");
      return;
    }

    setValidationError(null);
    setIsSaving(true);

    const respostas = analise.perguntas_avaliacao.map((p) => ({
      id_pergunta: p.id_pergunta,
      texto: p.texto,
      dimensao: p.dimensao,
      valor_resposta: answers[p.id_pergunta],
    }));

    try {
      const projectId = Number.parseInt(trimmedProjectId, 10);
      if (!Number.isInteger(projectId)) {
        throw new Error("Projeto selecionado inválido.");
      }

      const saveBody = {
        id_requisito_ou_titulo: analise.titulo_requisito,
        tipo_requisito: analise.tipo_requisito.toUpperCase(),
        texto_original: analise.texto_original,
        descricao_requisito: analise.descricao_requisito,
        objetivo: analise.objetivo,
        finalidade: analise.finalidade,
        usuario_avaliador: trimmedEvaluator,
        perfil_avaliador: formData.requesterId.trim() || undefined,
        respostas,
        cadastro: {
          id_projeto: projectId,
          perfil_solicitante: formData.requesterId.trim() || undefined,
          modulo_afetado: formData.systemArea.trim() || undefined,
          contexto_negocio: formData.businessImportance.trim() || undefined,
          objetivo_desejado: formData.expectedResult.trim() || undefined,
          sistema_ou_produto: formData.systemOrProduct.trim() || undefined,
          ha_contorno: formData.temporaryWorkaround.trim() || undefined,
          texto_original: formData.description.trim(),
        },
      };

      const response = await fetch("/api/priorizacao/salvar-avaliacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(saveBody),
      });
      const data = (await response.json().catch(() => ({}))) as
        | SalvarAvaliacaoResponse
        | { detail?: string };

      if (!response.ok) {
        throw new Error(extractDetail(data, "Não foi possível salvar a avaliação."));
      }

      setSaveSuccess(data as SalvarAvaliacaoResponse);
      setSuccessModalOpen(true);
      resetAll();
    } catch (error) {
      setValidationError(
        error instanceof Error
          ? error.message
          : "Não foi possível salvar a avaliação.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateProjectInline = async () => {
    try {
      setInlineProjectError(null);
      const response = await fetch("/api/priorizacao/projetos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...inlineProjectState,
          versao_atual:
            inlineProjectState.tipo_origem === "existente"
              ? inlineProjectState.versao_atual.trim()
              : undefined,
        }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(extractDetail(data, "Não foi possível criar o projeto."));
      }

      await loadProjects();
      const createdProject =
        data &&
        typeof data === "object" &&
        "id_projeto" in data &&
        typeof data.id_projeto === "number"
          ? String(data.id_projeto)
          : "";

      setFormData((prev) => ({
        ...prev,
        projectId: createdProject,
      }));
      setInlineProjectState(INITIAL_INLINE_PROJECT_STATE);
      setInlineProjectOpen(false);
    } catch (error) {
      setInlineProjectError(
        error instanceof Error ? error.message : "Não foi possível criar o projeto.",
      );
    }
  };

  const stepBadgeClass =
    currentStep === 1
      ? "bg-violet-500/15 text-violet-300 ring-violet-500/30"
      : "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30";

  return (
    <>
      <div className="w-full space-y-6">
        <Card className="overflow-hidden rounded-2xl border border-white/10 bg-card/80 shadow-2xl shadow-black/25 ring-1 ring-white/5 backdrop-blur-md">
          <CardHeader className="space-y-6 border-b border-white/[0.06] bg-white/[0.02] px-5 py-6 sm:px-8">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="space-y-2">
                <span
                  className={cn(
                    "inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset",
                    stepBadgeClass,
                  )}
                >
                  {currentStep} de {FORM_STEPS.length}
                </span>
                <h2 className="text-lg font-semibold tracking-tight sm:text-xl">
                  {currentStepMeta.title}
                </h2>
                <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">
                  {currentStepMeta.description}
                </p>
              </div>
            </div>

            <ActivityFormStepper
              currentStep={currentStep}
              onStepClick={handleStepClick}
            />
          </CardHeader>

          <CardContent className="space-y-6 px-5 py-6 sm:px-8">
            {currentStep === 1 ? (
              <div className="space-y-5">
                <FormSection>
                  <FormField label="Tipo do problema" icon={Bug}>
                    <Select
                      value={formData.demandType || undefined}
                      onValueChange={(value) =>
                        setFormData((prev) => ({ ...prev, demandType: value }))
                      }
                    >
                      <SelectTrigger className={cn("w-full", formControlClassName)}>
                        <SelectValue placeholder="Selecione se é Bug ou Feature" />
                      </SelectTrigger>
                      <SelectContent>
                        {DEMAND_TYPE_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormField>
                </FormSection>

                <FormSection>
                  <FormField
                    label="Descrição da demanda"
                    htmlFor="descricao-demanda"
                    hint="Explique o problema, melhoria ou funcionalidade com suas próprias palavras."
                  >
                    <FormTextareaWithCounter
                      id="descricao-demanda"
                      value={formData.description}
                      onChange={(description) =>
                        setFormData((prev) => ({ ...prev, description }))
                      }
                      minHeightClass="min-h-[160px]"
                      placeholder="Ex.: A tela de exportação trava ao gerar relatório..."
                    />
                  </FormField>
                </FormSection>

                <FormSection>
                  <FormField
                    label="Responsável pelo cadastro"
                    htmlFor="requester-id"
                    icon={User}
                  >
                    <Input
                      id="requester-id"
                      value={formData.requesterId}
                      onChange={(event) =>
                        setFormData((prev) => ({ ...prev, requesterId: event.target.value }))
                      }
                      className={formControlClassName}
                      placeholder="Ex.: João Silva, Product Owner"
                    />
                  </FormField>
                </FormSection>

                <FormSection>
                  <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                    <FormField label="Impacto percebido" icon={AlertTriangle}>
                      <Select
                        value={formData.perceivedImpact || undefined}
                        onValueChange={(value) =>
                          setFormData((prev) => ({ ...prev, perceivedImpact: value }))
                        }
                      >
                        <SelectTrigger className={cn("w-full", formControlClassName)}>
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent>
                          {IMPACT_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormField>

                    <FormField label="Frequência de ocorrência" icon={Clock}>
                      <Select
                        value={formData.frequency || undefined}
                        onValueChange={(value) =>
                          setFormData((prev) => ({ ...prev, frequency: value }))
                        }
                      >
                        <SelectTrigger className={cn("w-full", formControlClassName)}>
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent>
                          {FREQUENCY_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormField>

                    <FormField
                      label="Urgência percebida"
                      icon={Zap}
                      className="sm:col-span-2 lg:col-span-1"
                    >
                      <Select
                        value={formData.urgency || undefined}
                        onValueChange={(value) =>
                          setFormData((prev) => ({ ...prev, urgency: value }))
                        }
                      >
                        <SelectTrigger className={cn("w-full", formControlClassName)}>
                          <SelectValue placeholder="Selecione" />
                        </SelectTrigger>
                        <SelectContent>
                          {URGENCY_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormField>
                  </div>
                </FormSection>
              </div>
            ) : null}

            {currentStep === 2 ? (
              <div className="space-y-5">
                <FormSection>
                  <FormField
                    label="O que deveria acontecer?"
                    htmlFor="expected-result"
                    hint="Descreva qual seria o comportamento correto ou o resultado esperado."
                  >
                    <FormTextareaWithCounter
                      id="expected-result"
                      value={formData.expectedResult}
                      onChange={(expectedResult) =>
                        setFormData((prev) => ({ ...prev, expectedResult }))
                      }
                      minHeightClass="min-h-[140px]"
                      placeholder="Ex.: O sistema deveria exportar o relatório corretamente."
                    />
                  </FormField>
                </FormSection>

                <FormSection>
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <FormField
                      label="Projeto vinculado"
                      hint="Toda demanda precisa de um projeto associado."
                      icon={FolderKanban}
                      className="flex-1"
                    >
                      <Select
                        value={formData.projectId || undefined}
                        onValueChange={(value) =>
                          setFormData((prev) => ({ ...prev, projectId: value }))
                        }
                      >
                        <SelectTrigger className={cn("w-full", formControlClassName)}>
                          <SelectValue
                            placeholder={
                              isProjectsLoading
                                ? "Carregando projetos..."
                                : "Selecione um projeto"
                            }
                          />
                        </SelectTrigger>
                        <SelectContent>
                          {projects.map((project) => (
                            <SelectItem key={project.id} value={project.id}>
                              {project.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormField>
                    <Button
                      type="button"
                      variant="outline"
                      className="shrink-0 rounded-xl border-white/15 bg-white/[0.03] hover:bg-white/[0.06]"
                      onClick={() => setInlineProjectOpen(true)}
                    >
                      <Plus className="mr-2 size-4" />
                      Criar projeto
                    </Button>
                  </div>

                  {projectsError ? (
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-red-400">
                      <span>{projectsError}</span>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => void loadProjects()}
                      >
                        Tentar novamente
                      </Button>
                    </div>
                  ) : null}
                </FormSection>

              </div>
            ) : null}

            {stepError ? <p className="text-sm text-destructive">{stepError}</p> : null}
            {analyzeError ? <p className="text-sm text-destructive">{analyzeError}</p> : null}

            <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-6 sm:flex-row sm:items-center sm:justify-between">
              {currentStep > 1 ? (
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-xl border-white/15 bg-transparent hover:bg-white/[0.04]"
                  onClick={handlePreviousStep}
                >
                  <ChevronLeft className="mr-2 size-4" />
                  Voltar
                </Button>
              ) : null}

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                {currentStep === 1 ? (
                  <Button
                    type="button"
                    className="justify-start rounded-xl bg-destructive/70 text-destructive-foreground hover:bg-destructive/80"
                    onClick={resetAll}
                  >
                    <Trash2 className="mr-2 size-4" />
                    Limpar formulário
                  </Button>
                ) : null}

                {isLastStep ? (
                  <Button
                    type="button"
                    className="rounded-xl bg-emerald-600 text-white shadow-lg shadow-emerald-950/40 hover:bg-emerald-500"
                    onClick={() => void handleAnalyzeWithAI()}
                    disabled={isAnalyzing || !canAnalyzeWithAi}
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="mr-2 size-4 animate-spin" />
                        Analisando...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 size-4" />
                        Analisar e estruturar com IA
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    type="button"
                    className="rounded-xl bg-violet-600 text-white shadow-lg shadow-violet-950/40 hover:bg-violet-500"
                    onClick={handleNextStep}
                  >
                    Próximo
                    <ChevronRight className="ml-2 size-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {analise ? (
          <AiAnalysisStep
            direction="next"
            analise={analise}
            evaluatorName={evaluatorName}
            onEvaluatorNameChange={setEvaluatorName}
            answers={answers}
            onAnswerChange={(id, valor) =>
              setAnswers((prev) => ({ ...prev, [id]: valor }))
            }
            validationError={validationError}
            isSaving={isSaving}
            onBack={() => {
              setAnalise(null);
              setAnswers({});
              setValidationError(null);
            }}
            onSave={handleSaveAssessment}
          />
        ) : null}
      </div>

      <CustomModal
        open={inlineProjectOpen}
        onOpenChange={setInlineProjectOpen}
        title="Cadastrar projeto no fluxo"
        description="O projeto será criado no backend e selecionado automaticamente neste cadastro."
      >
        <div className="space-y-4">
          {inlineProjectError ? (
            <p className="text-sm text-destructive">{inlineProjectError}</p>
          ) : null}

          <div className="space-y-2">
            <Label>Nome do projeto</Label>
            <Input
              value={inlineProjectState.nome_projeto}
              onChange={(event) =>
                setInlineProjectState((prev) => ({ ...prev, nome_projeto: event.target.value }))
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Descrição</Label>
            <Textarea
              value={inlineProjectState.descricao}
              onChange={(event) =>
                setInlineProjectState((prev) => ({ ...prev, descricao: event.target.value }))
              }
            />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label>Origem</Label>
              <Select
                value={inlineProjectState.tipo_origem}
                onValueChange={(value) =>
                  setInlineProjectState((prev) => ({
                    ...prev,
                    tipo_origem: value as "novo" | "existente",
                  }))
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="novo">Novo</SelectItem>
                  <SelectItem value="existente">Existente</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={inlineProjectState.status_projeto}
                onValueChange={(value) =>
                  setInlineProjectState((prev) => ({
                    ...prev,
                    status_projeto: value as "ativo" | "arquivado" | "descontinuado",
                  }))
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ativo">Ativo</SelectItem>
                  <SelectItem value="arquivado">Arquivado</SelectItem>
                  <SelectItem value="descontinuado">Descontinuado</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Responsável</Label>
              <Input
                value={inlineProjectState.responsavel}
                onChange={(event) =>
                  setInlineProjectState((prev) => ({ ...prev, responsavel: event.target.value }))
                }
              />
            </div>
          </div>

          {inlineProjectState.tipo_origem === "existente" ? (
            <div className="space-y-2">
              <Label>Versão atual</Label>
              <Input
                value={inlineProjectState.versao_atual}
                onChange={(event) =>
                  setInlineProjectState((prev) => ({ ...prev, versao_atual: event.target.value }))
                }
              />
            </div>
          ) : null}

          <div className="flex gap-2">
            <Button onClick={() => void handleCreateProjectInline()}>
              Cadastrar projeto
            </Button>
            <Button variant="outline" onClick={() => setInlineProjectOpen(false)}>
              Cancelar
            </Button>
          </div>
        </div>
      </CustomModal>

      <CustomModal
        open={successModalOpen}
        onOpenChange={setSuccessModalOpen}
        title={
          <span className="flex items-center gap-2">
            <CheckCircle2 className="size-5 shrink-0 text-emerald-400" />
            Avaliação salva com sucesso
          </span>
        }
        contentClassName="sm:max-w-lg"
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-3.5 py-3">
            <p className="text-sm text-white">
              Tudo certo! A atividade já está disponível nas demais áreas do produto.
            </p>
          </div>

          {saveSuccess?.warning ? (
            <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
              {saveSuccess.warning}
            </p>
          ) : null}

          <div className="flex w-full flex-row gap-2">
            <Button className="flex-1" onClick={() => setSuccessModalOpen(false)}>
              Novo cadastro
            </Button>
            <Button asChild variant="outline" className="flex-1">
              <a href="/activities">Ver atividades</a>
            </Button>
          </div>
        </div>
      </CustomModal>
    </>
  );
}
