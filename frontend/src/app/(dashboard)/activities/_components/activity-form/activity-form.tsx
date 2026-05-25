"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ACTIVITY_FORM_STORAGE_KEY,
  INITIAL_ACTIVITY_FORM_DATA,
  parsePersistedDraftJson,
  serializeDraft,
  type ActivityFormData,
} from "@/lib/activity-form-draft";
import { buildAnaliseRequestBody } from "@/lib/priorizacao/map-form-to-analise";
import { computeCoordinatesFromAnswers } from "@/lib/priorizacao/compute-coordinates";
import { appendUserMatrixPoint } from "@/lib/priorizacao/matrix-points-storage";
import type { AnaliseRequisitoResponse } from "@/lib/priorizacao/types";
import { FORM_STEPS } from "./options";
import { StepIndicator } from "./step-indicator";
import { IdentificationStep } from "./identification-step";
import { ImpactStep } from "./impact-step";
import { ContextStep } from "./context-step";
import { AiAnalysisStep } from "./ai-analysis-step";

export type { ActivityFormData };

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

export function ActivityForm() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState<"next" | "prev">("next");
  const [formData, setFormData] = useState<ActivityFormData>(INITIAL_ACTIVITY_FORM_DATA);
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [analise, setAnalise] = useState<AnaliseRequisitoResponse | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [evaluatorName, setEvaluatorName] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setProjects([]);
  }, []);

  useEffect(() => {
    const draft = readDraft();
    if (draft) {
      setFormData(draft.formData);
      setStep(Math.min(draft.step, 3));
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated || typeof window === "undefined" || step > 3) return;

    const id = window.setTimeout(() => {
      try {
        window.localStorage.setItem(
          ACTIVITY_FORM_STORAGE_KEY,
          serializeDraft(formData, step),
        );
      } catch {
        // ignore
      }
    }, 300);

    return () => window.clearTimeout(id);
  }, [formData, step, hydrated]);

  const finalizeAndLeave = useCallback(() => {
    clearDraft();
    router.push("/activities");
  }, [router]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (step < 3) {
      setDirection("next");
      setStep((current) => current + 1);
    }
  };

  const handleAnalyzeWithAI = async () => {
    if (!formData.description.trim()) {
      setAnalyzeError("Informe a descrição da demanda antes de analisar.");
      return;
    }

    setAnalyzeError(null);
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
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Não foi possível analisar com IA.",
        );
      }

      setAnalise(data as AnaliseRequisitoResponse);
      setAnswers({});
      setEvaluatorName(formData.requesterId.trim());
      setDirection("next");
      setStep(4);
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

    const tipo = analise.tipo_requisito.toUpperCase() as "BUG" | "INCREMENTO";
    const { coordenada_x, coordenada_y } = computeCoordinatesFromAnswers(
      analise.perguntas_avaliacao,
      answers,
    );

    const point = {
      x: coordenada_x,
      y: coordenada_y,
      titulo: analise.titulo_requisito,
    };

    try {
      if (formData.projectId) {
        const saveBody = {
          id_requisito_ou_titulo: analise.titulo_requisito,
          tipo_requisito: tipo,
          texto_original: analise.texto_original,
          descricao_requisito: analise.descricao_requisito,
          objetivo: analise.objetivo,
          finalidade: analise.finalidade,
          usuario_avaliador: trimmedEvaluator,
          respostas,
          cadastro: {
            id_projeto: Number.parseInt(formData.projectId, 10),
            perfil_solicitante: formData.requesterId.trim() || undefined,
            modulo_afetado: formData.systemArea.trim() || undefined,
            contexto_negocio: formData.businessImportance.trim() || undefined,
          },
        };

        const response = await fetch("/api/priorizacao/salvar-avaliacao", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(saveBody),
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(
            typeof err.detail === "string"
              ? err.detail
              : "Não foi possível salvar na API. O ponto foi guardado localmente.",
          );
        }
      }

      appendUserMatrixPoint(point, tipo);
      finalizeAndLeave();
    } catch (error) {
      appendUserMatrixPoint(point, tipo);
      setValidationError(
        error instanceof Error
          ? `${error.message} A atividade foi adicionada à matriz localmente.`
          : "Salvo localmente na matriz.",
      );
      window.setTimeout(() => finalizeAndLeave(), 1800);
    } finally {
      setIsSaving(false);
    }
  };

  const canGoNext = (step === 1 && formData.description.trim().length > 0) || step > 1;

  const goToStep = (targetStep: number) => {
    setDirection(targetStep > step ? "next" : "prev");
    setStep(targetStep);
    if (targetStep <= 3) {
      setAnalyzeError(null);
    }
  };

  const indicatorSteps =
    step === 4
      ? [
          ...FORM_STEPS,
          { id: 4, title: "Avaliação com IA" },
        ]
      : FORM_STEPS;

  return (
    <form onSubmit={handleSubmit} className="flex min-h-0 flex-col gap-3">
      <StepIndicator steps={indicatorSteps} currentStep={step} />

      {step === 1 && (
        <IdentificationStep
          direction={direction}
          formData={formData}
          setFormData={setFormData}
          canGoNext={canGoNext}
        />
      )}

      {step === 2 && (
        <ImpactStep
          direction={direction}
          formData={formData}
          setFormData={setFormData}
          goToStep={goToStep}
        />
      )}

      {step === 3 && (
        <>
          <ContextStep
            direction={direction}
            formData={formData}
            setFormData={setFormData}
            projects={projects}
            goToStep={goToStep}
            onAnalyzeWithAI={handleAnalyzeWithAI}
            isAnalyzing={isAnalyzing}
          />
          {analyzeError ? (
            <p className="text-sm text-destructive">{analyzeError}</p>
          ) : null}
        </>
      )}

      {step === 4 && analise && (
        <AiAnalysisStep
          direction={direction}
          analise={analise}
          evaluatorName={evaluatorName}
          onEvaluatorNameChange={setEvaluatorName}
          answers={answers}
          onAnswerChange={(id, valor) =>
            setAnswers((prev) => ({ ...prev, [id]: valor }))
          }
          validationError={validationError}
          isSaving={isSaving}
          onBack={() => goToStep(3)}
          onSave={handleSaveAssessment}
        />
      )}
    </form>
  );
}
