import { describe, expect, it } from "vitest";
import {
  columnToStatus,
  documentationPhaseToColumn,
  statusToColumn,
} from "@/lib/priorizacao/kanban-status";

describe("kanban-status", () => {
  it('statusToColumn("DEPLOY") retorna DEPLOY', () => {
    expect(statusToColumn("DEPLOY")).toBe("DEPLOY");
  });

  it("mapeia aliases de homologação e teste", () => {
    expect(statusToColumn("EM_HOMOLOGACAO")).toBe("DEPLOY");
    expect(statusToColumn("EM_TESTE")).toBe("TEST");
    expect(statusToColumn("AVALIADO")).toBe("TO DO");
  });

  it("columnToStatus é inverso das colunas principais", () => {
    expect(columnToStatus("DEPLOY")).toBe("EM_HOMOLOGACAO");
    expect(columnToStatus("DONE")).toBe("DONE");
  });

  it("documentationPhaseToColumn mapeia fases documentais para colunas Kanban", () => {
    expect(documentationPhaseToColumn("backlog")).toBe("BACKLOG");
    expect(documentationPhaseToColumn("to-do")).toBe("TO DO");
    expect(documentationPhaseToColumn("develop")).toBe("DEVELOP");
    expect(documentationPhaseToColumn("test")).toBe("TEST");
    expect(documentationPhaseToColumn("deploy")).toBe("DEPLOY");
    expect(documentationPhaseToColumn("encerramento")).toBe("DONE");
  });

  it("reabrir to-do deve usar status AVALIADO na API", () => {
    expect(columnToStatus(documentationPhaseToColumn("to-do"))).toBe("AVALIADO");
  });
});
