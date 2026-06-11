import { toast } from "sonner";
import type { KanbanColumnId } from "@/lib/priorizacao/kanban-status";
import { columnToStatus } from "@/lib/priorizacao/kanban-status";
import type { KanbanGatesResponse } from "@/lib/priorizacao/types";

export type AutoAdvanceStopReason = "ok" | "gate" | "wip" | "error" | "done";

export type AutoAdvanceResult = {
  stopped: AutoAdvanceStopReason;
  stepsCompleted: number;
  gates?: KanbanGatesResponse | null;
  detail?: string;
  lastColumn?: KanbanColumnId;
};

async function fetchGates(requisitoId: number): Promise<KanbanGatesResponse | null> {
  const response = await fetch(`/api/priorizacao/kanban/${requisitoId}/gates`, {
    cache: "no-store",
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) return null;
  return data as KanbanGatesResponse;
}

export async function postKanbanStatus(
  requisitoId: number,
  targetColumn: KanbanColumnId,
): Promise<{ ok: boolean; detail?: string }> {
  const status = columnToStatus(targetColumn);
  const response = await fetch(`/api/priorizacao/requisitos/${requisitoId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
        ? data.detail
        : "Não foi possível atualizar o status na esteira.";
    return { ok: false, detail };
  }
  return { ok: true };
}

async function postStatus(requisitoId: number, proximaColuna: string): Promise<{ ok: boolean; detail?: string }> {
  return postKanbanStatus(requisitoId, proximaColuna as KanbanColumnId);
}

function notifyWipBlocked(gates: KanbanGatesResponse) {
  const wip = gates.wip_destino;
  const coluna = wip?.coluna ?? gates.proxima_coluna ?? "destino";
  const ocupacao = wip?.ocupacao ?? "?";
  const limite = wip?.limite ?? "?";
  toast.error(`Limite WIP em ${coluna}`, {
    description: `A coluna já tem ${ocupacao} de ${limite} atividades. Conclua ou mova um card antes de avançar esta tarefa.`,
  });
}

function notifyGateBlocked(gates: KanbanGatesResponse) {
  const falta = gates.falta_documentacao;
  toast.error("Documentação incompleta", {
    description:
      falta.length > 0
        ? falta.slice(0, 3).join("; ") + (falta.length > 3 ? "…" : "")
        : `Conclua a documentação da coluna ${gates.coluna_kanban} antes de avançar.`,
  });
}

/** Feedback unificado após avanço silencioso (evita toast duplicado na página). */
export function reportKanbanAdvanceFeedback(
  advance: AutoAdvanceResult,
  successTitle: string,
  options?: { blockedHint?: string },
) {
  if (advance.stepsCompleted > 0) {
    toast.success(successTitle, {
      description:
        advance.stepsCompleted === 1
          ? "Esteira atualizada."
          : `Esteira avançou ${advance.stepsCompleted} colunas.`,
    });
    return;
  }

  toast.success(successTitle);

  if (advance.stopped === "gate" && advance.gates) {
    notifyGateBlocked(advance.gates);
    return;
  }
  if (advance.stopped === "wip" && advance.gates) {
    notifyWipBlocked(advance.gates);
    return;
  }
  if (advance.stopped === "error" && advance.detail) {
    toast.error("Não foi possível atualizar a esteira", { description: advance.detail });
    return;
  }
  if (advance.stopped === "gate" || advance.stopped === "wip") {
    toast.warning(
      options?.blockedHint ?? "Avanço na esteira bloqueado (gate ou WIP).",
    );
  }
}

/**
 * Tenta avançar a esteira após gravar documentação (gate → WIP → POST, uma coluna por passo).
 */
export async function tentarAvancoAutomaticoKanban(
  requisitoId: number,
  options?: { maxSteps?: number; silent?: boolean },
): Promise<AutoAdvanceResult> {
  const maxSteps = options?.maxSteps ?? 1;
  let stepsCompleted = 0;
  let lastGates: KanbanGatesResponse | null = null;

  for (let step = 0; step < maxSteps; step++) {
    const gates = await fetchGates(requisitoId);
    lastGates = gates;

    if (!gates) {
      if (!options?.silent) {
        toast.error("Não foi possível verificar a esteira.");
      }
      return { stopped: "error", stepsCompleted, detail: "Falha ao consultar gates." };
    }

    if (!gates.proxima_coluna) {
      return { stopped: "done", stepsCompleted, gates, lastColumn: gates.coluna_kanban as KanbanColumnId };
    }

    if (!gates.pode_avancar_documentacao) {
      if (!options?.silent) notifyGateBlocked(gates);
      return { stopped: "gate", stepsCompleted, gates };
    }

    if (gates.pode_avancar_wip === false) {
      if (!options?.silent) notifyWipBlocked(gates);
      return { stopped: "wip", stepsCompleted, gates };
    }

    const proxima = gates.proxima_coluna as KanbanColumnId;
    const result = await postStatus(requisitoId, proxima);
    if (!result.ok) {
      if (!options?.silent) {
        const msg = result.detail ?? "";
        if (msg.toLowerCase().includes("wip")) {
          notifyWipBlocked(gates);
          return { stopped: "wip", stepsCompleted, gates, detail: msg };
        }
        if (msg.toLowerCase().includes("documentação") || msg.toLowerCase().includes("transição bloqueada")) {
          toast.error("Não foi possível avançar", { description: msg });
          return { stopped: "gate", stepsCompleted, gates, detail: msg };
        }
        if (msg.toLowerCase().includes("salto")) {
          toast.error("Avance uma coluna de cada vez", { description: msg });
        } else {
          toast.error("Não foi possível avançar", { description: msg });
        }
      }
      return { stopped: "error", stepsCompleted, gates, detail: result.detail };
    }

    stepsCompleted += 1;
    if (!options?.silent) {
      toast.success(`Movido para ${proxima}`, {
        description: `Atividade #${requisitoId} avançou na esteira.`,
      });
    }
  }

  return {
    stopped: stepsCompleted > 0 ? "ok" : "gate",
    stepsCompleted,
    gates: lastGates,
    lastColumn: lastGates?.coluna_kanban as KanbanColumnId | undefined,
  };
}
