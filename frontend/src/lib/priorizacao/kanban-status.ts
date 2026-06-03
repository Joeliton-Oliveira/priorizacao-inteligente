/** Colunas da esteira Kanban (alinhado ao backend `KANBAN_COLUNAS`). */
export type KanbanColumnId = "BACKLOG" | "TO DO" | "DEVELOP" | "TEST" | "DEPLOY" | "DONE";

export const KANBAN_COLUMN_ORDER: KanbanColumnId[] = [
  "BACKLOG",
  "TO DO",
  "DEVELOP",
  "TEST",
  "DEPLOY",
  "DONE",
];

export const KANBAN_NEXT: Record<KanbanColumnId, KanbanColumnId | null> = {
  BACKLOG: "TO DO",
  "TO DO": "DEVELOP",
  DEVELOP: "TEST",
  TEST: "DEPLOY",
  DEPLOY: "DONE",
  DONE: null,
};

/** Status persistido na API ao avançar para cada coluna. */
export const COLUMN_TO_STATUS: Record<KanbanColumnId, string> = {
  BACKLOG: "BACKLOG",
  "TO DO": "AVALIADO",
  DEVELOP: "EM_DESENVOLVIMENTO",
  TEST: "EM_TESTE",
  DEPLOY: "EM_HOMOLOGACAO",
  DONE: "DONE",
};

/** Chaves das fases documentais (alinhado a `DocumentationPhaseKey`). */
export type DocumentationPhaseKey =
  | "backlog"
  | "to-do"
  | "develop"
  | "test"
  | "deploy"
  | "encerramento";

export const DOCUMENTATION_PHASE_TO_COLUMN: Record<DocumentationPhaseKey, KanbanColumnId> = {
  backlog: "BACKLOG",
  "to-do": "TO DO",
  develop: "DEVELOP",
  test: "TEST",
  deploy: "DEPLOY",
  encerramento: "DONE",
};

/** Coluna Kanban correspondente à fase documental reaberta. */
export function documentationPhaseToColumn(phase: DocumentationPhaseKey): KanbanColumnId {
  return DOCUMENTATION_PHASE_TO_COLUMN[phase];
}

const STATUS_TO_COLUMN_MAP: Record<string, KanbanColumnId> = {
  BACKLOG: "BACKLOG",
  TO_DO: "TO DO",
  TODO: "TO DO",
  DEVELOP: "DEVELOP",
  EM_DESENVOLVIMENTO: "DEVELOP",
  TEST: "TEST",
  EM_TESTE: "TEST",
  DEPLOY: "DEPLOY",
  EM_HOMOLOGACAO: "DEPLOY",
  DONE: "DONE",
  CONCLUIDO: "DONE",
  CONCLUÍDO: "DONE",
  AVALIADO: "TO DO",
  PRIORIZADO: "TO DO",
};

/** Espelha `status_api_para_coluna_kanban` no backend. */
export function statusToColumn(statusRaw?: string | null): KanbanColumnId {
  const s = (statusRaw || "BACKLOG").trim().toUpperCase().replace(/\s/g, "_");
  if (STATUS_TO_COLUMN_MAP[s]) {
    return STATUS_TO_COLUMN_MAP[s];
  }
  for (const col of KANBAN_COLUMN_ORDER) {
    if (s === col.toUpperCase().replace(/\s/g, "_")) {
      return col;
    }
  }
  return "BACKLOG";
}

export function columnToStatus(columnId: KanbanColumnId): string {
  return COLUMN_TO_STATUS[columnId];
}

export type WipConfigKey = "TO_DO" | "DEVELOP" | "TEST" | "DEPLOY";

const COLUMN_TO_WIP_KEY: Partial<Record<KanbanColumnId, WipConfigKey>> = {
  "TO DO": "TO_DO",
  DEVELOP: "DEVELOP",
  TEST: "TEST",
  DEPLOY: "DEPLOY",
};

export function columnToWipConfigKey(columnId: KanbanColumnId): WipConfigKey | null {
  return COLUMN_TO_WIP_KEY[columnId] ?? null;
}

export function getWipLimit(
  wip: { TO_DO: number; DEVELOP: number; TEST: number; DEPLOY: number } | undefined,
  columnId: KanbanColumnId,
): number | null {
  if (!wip) return null;
  const key = columnToWipConfigKey(columnId);
  if (!key) return null;
  const limit = wip[key];
  return typeof limit === "number" && limit > 0 ? limit : null;
}
