import { describe, expect, it } from "vitest";
import { parseBackendDocumentation } from "./activity-documentation-data";
import {
  DOCUMENTATION_FLOW_ORDER,
  getDocumentationFlowState,
  getEffectiveCompletionMap,
  getPhaseFlowStatus,
  getPhasesToClear,
  getPhasesToClearOnReopen,
  getPhasesToClearOnStale,
  isPhaseStale,
  type PhaseCompletionMap,
} from "./documentation-phase-flow";

function map(partial: Partial<PhaseCompletionMap>): PhaseCompletionMap {
  return Object.fromEntries(
    DOCUMENTATION_FLOW_ORDER.map((key) => [key, partial[key] ?? false]),
  ) as PhaseCompletionMap;
}

describe("documentation-phase-flow", () => {
  it("getEffectiveCompletionMap mantém só o prefixo contínuo desde BACKLOG", () => {
    const raw = map({
      backlog: false,
      "to-do": true,
      develop: true,
      test: false,
      deploy: true,
      encerramento: true,
    });
    const effective = getEffectiveCompletionMap(raw);
    expect(effective.backlog).toBe(false);
    expect(effective["to-do"]).toBe(false);
    expect(effective.develop).toBe(false);
    expect(effective.deploy).toBe(false);
    expect(effective.encerramento).toBe(false);
  });

  it("getEffectiveCompletionMap para na primeira fase incompleta", () => {
    const raw = map({
      backlog: true,
      "to-do": true,
      develop: false,
      test: true,
      deploy: true,
    });
    const effective = getEffectiveCompletionMap(raw);
    expect(effective.backlog).toBe(true);
    expect(effective["to-do"]).toBe(true);
    expect(effective.develop).toBe(false);
    expect(effective.test).toBe(false);
    expect(effective.deploy).toBe(false);
  });

  it("isPhaseStale detecta TO DO órfão sem BACKLOG", () => {
    const raw = map({ backlog: false, "to-do": true });
    expect(isPhaseStale("to-do", raw)).toBe(true);
    expect(isPhaseStale("backlog", raw)).toBe(false);
  });

  it("getPhaseFlowStatus marca fase órfã como stale", () => {
    const raw = map({ backlog: false, "to-do": true });
    expect(getPhaseFlowStatus("to-do", raw, null)).toBe("stale");
    expect(getPhaseFlowStatus("develop", raw, null)).toBe("blocked");
  });

  it("getPhasesToClearOnReopen em backlog limpa só posteriores", () => {
    expect(getPhasesToClearOnReopen("backlog")).toEqual([
      "to-do",
      "develop",
      "test",
      "deploy",
      "encerramento",
    ]);
  });

  it("getPhasesToClearOnReopen em TO DO limpa a fase e posteriores", () => {
    expect(getPhasesToClearOnReopen("to-do")).toEqual([
      "to-do",
      "develop",
      "test",
      "deploy",
      "encerramento",
    ]);
  });

  it("getPhasesToClearOnStale sempre inclui a fase e posteriores", () => {
    expect(getPhasesToClearOnStale("test")).toEqual(["test", "deploy", "encerramento"]);
  });

  it("getPhasesToClear usa stale quando fase é órfã", () => {
    const raw = map({ backlog: false, "to-do": true, develop: true });
    expect(getPhasesToClear("to-do", raw)).toEqual(getPhasesToClearOnStale("to-do"));
    expect(getPhasesToClear("to-do", map({ backlog: true, "to-do": true }))).toEqual(
      getPhasesToClearOnReopen("to-do"),
    );
  });

  it("dados reais sem doc_requisito marcam posteriores como stale", () => {
    const docs = parseBackendDocumentation({
      doc_requisito: "",
      prontidao_dev: JSON.stringify({
        responsavel_desenvolvimento: "Confirmado na esteira",
        registrado_por: "Confirmado na esteira",
        data_prontidao: "2026-05-29",
        observacoes_tecnicas: "Confirmado",
        checklist: ["a"],
      }),
      entrega_dev: JSON.stringify({
        nome_entrega: "X",
        descricao_desenvolvido: "Y",
        alteracoes: "N/A",
        validacao_qa: "Z",
        branch_referencia: "N/A",
        commit_referencia: "N/A",
        desenvolvedor: "Dev",
        data_entrega_teste: "2026-05-29",
      }),
      casos_teste: "",
      deploy: JSON.stringify({
        versao_entregue: "1",
        ambiente: "Prod",
        data_deploy: "2026-05-29",
        responsavel_deploy: "Ops",
        observacoes: "Ok",
      }),
      encerramento: "Atividade encerrada na esteira Kanban.",
    });
    const state = getDocumentationFlowState(docs);
    expect(state.raw.backlog).toBe(false);
    expect(state.statusByPhase["to-do"]).toBe("stale");
    expect(state.statusByPhase.develop).toBe("stale");
    expect(state.statusByPhase.deploy).toBe("stale");
    expect(state.statusByPhase.encerramento).toBe("stale");
    expect(state.hasStalePhases).toBe(true);
  });
});
