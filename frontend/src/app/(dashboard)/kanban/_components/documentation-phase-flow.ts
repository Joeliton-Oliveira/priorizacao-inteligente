import {
  isDevelopDocumentacaoEmpty,
  isToDoDocumentacaoEmpty,
  type ActivityDocumentation,
  type DocumentationPhaseKey,
} from "./activity-documentation-data";
import { backlogPassesGate, deployPassesGate, testPassesGate } from "./documentation-gate-client";

export const DOCUMENTATION_FLOW_ORDER: DocumentationPhaseKey[] = [
  "backlog",
  "to-do",
  "develop",
  "test",
  "deploy",
  "encerramento",
];

export const PHASE_DISPLAY_NAME: Record<DocumentationPhaseKey, string> = {
  backlog: "BACKLOG",
  "to-do": "TO DO",
  develop: "DEVELOP",
  test: "TEST",
  deploy: "DEPLOY",
  encerramento: "DONE",
};

export const STALE_PHASE_HINT =
  "Conclua as etapas anteriores; esta confirmação não vale no fluxo atual.";

export type PhaseCompletionMap = Record<DocumentationPhaseKey, boolean>;

export type PhaseFlowStatus = "blocked" | "available" | "done" | "reopened" | "stale";

type PhaseFlowOptions = {
  exigirRegrasECriteriosBacklog?: boolean;
  dispensarBacklogDoc?: boolean;
};

export function getPhaseCompletionMap(
  data: ActivityDocumentation,
  options?: PhaseFlowOptions,
): PhaseCompletionMap {
  return {
    backlog: backlogPassesGate(data.backlog, {
      exigirRegrasECriterios: options?.exigirRegrasECriteriosBacklog ?? true,
      dispensarDocRequisito: options?.dispensarBacklogDoc ?? false,
    }),
    "to-do": !isToDoDocumentacaoEmpty(data.toDo),
    develop: !isDevelopDocumentacaoEmpty(data.develop),
    test: testPassesGate(data.test),
    deploy: deployPassesGate(data.deploy),
    encerramento: Boolean(data.encerramento?.trim()),
  };
}

/** Conclusão válida no fluxo: prefixo contínuo desde BACKLOG. */
export function getEffectiveCompletionMap(raw: PhaseCompletionMap): PhaseCompletionMap {
  const effective = Object.fromEntries(
    DOCUMENTATION_FLOW_ORDER.map((key) => [key, false]),
  ) as PhaseCompletionMap;

  for (const key of DOCUMENTATION_FLOW_ORDER) {
    if (!raw[key]) break;
    effective[key] = true;
  }

  return effective;
}

export function isPhaseStale(phase: DocumentationPhaseKey, raw: PhaseCompletionMap): boolean {
  const effective = getEffectiveCompletionMap(raw);
  return raw[phase] && !effective[phase];
}

export function phasesAfter(phase: DocumentationPhaseKey): DocumentationPhaseKey[] {
  const index = DOCUMENTATION_FLOW_ORDER.indexOf(phase);
  if (index < 0) return [];
  return DOCUMENTATION_FLOW_ORDER.slice(index + 1);
}

/** Fases gravadas como vazias ao reabrir uma etapa concluída (cascata). */
export function getPhasesToClearOnReopen(phase: DocumentationPhaseKey): DocumentationPhaseKey[] {
  const subsequent = phasesAfter(phase);
  if (phase === "backlog" || phase === "test") {
    return subsequent;
  }
  return [phase, ...subsequent];
}

/** Fases a limpar quando há dado órfão fora da cadeia (botão Limpar etapa). */
export function getPhasesToClearOnStale(phase: DocumentationPhaseKey): DocumentationPhaseKey[] {
  return [phase, ...phasesAfter(phase)];
}

export function getPhasesToClear(
  phase: DocumentationPhaseKey,
  raw: PhaseCompletionMap,
): DocumentationPhaseKey[] {
  if (isPhaseStale(phase, raw)) {
    return getPhasesToClearOnStale(phase);
  }
  return getPhasesToClearOnReopen(phase);
}

export function arePrerequisitesMet(
  phase: DocumentationPhaseKey,
  completed: PhaseCompletionMap,
): boolean {
  const index = DOCUMENTATION_FLOW_ORDER.indexOf(phase);
  if (index <= 0) return true;
  return DOCUMENTATION_FLOW_ORDER.slice(0, index).every((key) => completed[key]);
}

export function getBlockingPhaseKey(
  phase: DocumentationPhaseKey,
  completed: PhaseCompletionMap,
): DocumentationPhaseKey | null {
  const index = DOCUMENTATION_FLOW_ORDER.indexOf(phase);
  for (let i = 0; i < index; i++) {
    const key = DOCUMENTATION_FLOW_ORDER[i];
    if (!completed[key]) return key;
  }
  return null;
}

export function getDependencyHint(
  phase: DocumentationPhaseKey,
  raw: PhaseCompletionMap,
): string | null {
  if (isPhaseStale(phase, raw)) return STALE_PHASE_HINT;
  const effective = getEffectiveCompletionMap(raw);
  const blocker = getBlockingPhaseKey(phase, effective);
  if (!blocker) return null;
  return `Conclua ${PHASE_DISPLAY_NAME[blocker]} para liberar esta etapa.`;
}

export function getPhaseFlowStatus(
  phase: DocumentationPhaseKey,
  raw: PhaseCompletionMap,
  reopenedPhase: DocumentationPhaseKey | null,
): PhaseFlowStatus {
  if (reopenedPhase === phase) return "reopened";
  if (isPhaseStale(phase, raw)) return "stale";
  const effective = getEffectiveCompletionMap(raw);
  if (effective[phase]) return "done";
  if (!arePrerequisitesMet(phase, effective)) return "blocked";
  return "available";
}

export function canMarkPhaseComplete(
  phase: DocumentationPhaseKey,
  raw: PhaseCompletionMap,
): boolean {
  const effective = getEffectiveCompletionMap(raw);
  return arePrerequisitesMet(phase, effective) && !effective[phase];
}

export function canFillPhase(phase: "backlog" | "test", raw: PhaseCompletionMap): boolean {
  const effective = getEffectiveCompletionMap(raw);
  return arePrerequisitesMet(phase, effective);
}

export function canReopenPhase(phase: DocumentationPhaseKey, raw: PhaseCompletionMap): boolean {
  const effective = getEffectiveCompletionMap(raw);
  return effective[phase];
}

export function getStalePhases(raw: PhaseCompletionMap): DocumentationPhaseKey[] {
  return DOCUMENTATION_FLOW_ORDER.filter((phase) => isPhaseStale(phase, raw));
}

export function getDocumentationFlowState(
  data: ActivityDocumentation,
  reopenedPhase: DocumentationPhaseKey | null = null,
  options?: PhaseFlowOptions,
) {
  const raw = getPhaseCompletionMap(data, options);
  const effective = getEffectiveCompletionMap(raw);
  const statusByPhase = Object.fromEntries(
    DOCUMENTATION_FLOW_ORDER.map((phase) => [
      phase,
      getPhaseFlowStatus(phase, raw, reopenedPhase),
    ]),
  ) as Record<DocumentationPhaseKey, PhaseFlowStatus>;
  const stalePhases = getStalePhases(raw);

  return {
    raw,
    effective,
    statusByPhase,
    stalePhases,
    hasStalePhases: stalePhases.length > 0,
  };
}
