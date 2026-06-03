import { isCasoTestePreenchido, type CasoTeste } from "./test-case-types";
import { TODO_CHECKLIST_OPTIONS } from "./todo-checklist";

const MARCAR_FEITO_OBS = "Confirmado na esteira (sem formulário detalhado).";

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export type BacklogDocumentacao = {
  nomeFuncionalidade: string;
  descricaoDetalhada: string;
  restricoes: string;
  requisitosFuncionais: string[];
  requisitosNaoFuncionais: string[];
  regrasNegocio: string[];
  criteriosAceitacao: string[];
};

export type ToDoDocumentacao = {
  responsavelDesenvolvimento: string;
  registradoPor: string;
  dataProntidao: string;
  observacoesTecnicas: string;
  checklist: string[];
};

export type DevelopDocumentacao = {
  nomeEntrega: string;
  descricaoDesenvolvido: string;
  alteracoes: string;
  validacaoQa: string;
  branchReferencia: string;
  commitReferencia: string;
  desenvolvedor: string;
  dataEntregaTeste: string;
};

export type TestDocumentacao = {
  casos: CasoTeste[];
};

export type DeployDocumentacao = {
  versaoEntregue: string;
  ambiente: string;
  dataDeploy: string;
  responsavelDeploy: string;
  observacoes: string;
};

export type ActivityDocumentation = {
  backlog: BacklogDocumentacao;
  toDo?: ToDoDocumentacao;
  develop?: DevelopDocumentacao;
  test?: TestDocumentacao;
  deploy?: DeployDocumentacao;
  encerramento?: string;
};

export const DOCUMENTATION_BY_CARD_ID: Record<string, ActivityDocumentation> = {};

function safeJsonParse(raw: string | undefined) {
  if (!raw?.trim()) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function stringList(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item ?? "").trim()).filter(Boolean);
}

export function getEmptyActivityDocumentation(): ActivityDocumentation {
  return {
    backlog: {
      nomeFuncionalidade: "",
      descricaoDetalhada: "",
      restricoes: "",
      requisitosFuncionais: [],
      requisitosNaoFuncionais: [],
      regrasNegocio: [],
      criteriosAceitacao: [],
    },
    toDo: {
      responsavelDesenvolvimento: "",
      registradoPor: "",
      dataProntidao: "",
      observacoesTecnicas: "",
      checklist: [],
    },
    develop: {
      nomeEntrega: "",
      descricaoDesenvolvido: "",
      alteracoes: "",
      validacaoQa: "",
      branchReferencia: "",
      commitReferencia: "",
      desenvolvedor: "",
      dataEntregaTeste: "",
    },
    test: { casos: [] },
    deploy: {
      versaoEntregue: "",
      ambiente: "",
      dataDeploy: "",
      responsavelDeploy: "",
      observacoes: "",
    },
    encerramento: "",
  };
}

function parseBacklog(raw: string | undefined): BacklogDocumentacao {
  const parsed = safeJsonParse(raw);
  if (!parsed || typeof parsed !== "object") {
    return {
      ...getEmptyActivityDocumentation().backlog,
      requisitosFuncionais: raw?.trim() ? [raw.trim()] : [],
    };
  }
  const data = parsed as Record<string, unknown>;
  return {
    nomeFuncionalidade: String(data.nome_funcionalidade ?? "").trim(),
    descricaoDetalhada: String(data.descricao_detalhada ?? "").trim(),
    restricoes: String(data.restricoes ?? "").trim(),
    requisitosFuncionais: stringList(data.requisitos_funcionais),
    requisitosNaoFuncionais: stringList(data.requisitos_nao_funcionais),
    regrasNegocio: stringList(data.regras_negocio),
    criteriosAceitacao: stringList(data.criterios_aceitacao),
  };
}

function parseToDo(raw: string | undefined): ToDoDocumentacao | undefined {
  const parsed = safeJsonParse(raw);
  if (!parsed || typeof parsed !== "object") {
    if (!raw?.trim()) return undefined;
    return {
      ...getEmptyActivityDocumentation().toDo!,
      observacoesTecnicas: raw.trim(),
    };
  }
  const data = parsed as Record<string, unknown>;
  return {
    responsavelDesenvolvimento: String(data.responsavel_desenvolvimento ?? "").trim(),
    registradoPor: String(data.registrado_por ?? "").trim(),
    dataProntidao: String(data.data_prontidao ?? "").trim(),
    observacoesTecnicas: String(data.observacoes_tecnicas ?? "").trim(),
    checklist: stringList(data.checklist),
  };
}

function parseDevelop(raw: string | undefined): DevelopDocumentacao | undefined {
  const parsed = safeJsonParse(raw);
  if (!parsed || typeof parsed !== "object") {
    if (!raw?.trim()) return undefined;
    return {
      ...getEmptyActivityDocumentation().develop!,
      descricaoDesenvolvido: raw.trim(),
    };
  }
  const data = parsed as Record<string, unknown>;
  return {
    nomeEntrega: String(data.nome_entrega ?? data.nome_funcionalidade ?? "").trim(),
    descricaoDesenvolvido: String(
      data.descricao_desenvolvido ?? data.o_que_foi_desenvolvido ?? "",
    ).trim(),
    alteracoes: String(data.alteracoes ?? data.o_que_foi_alterado ?? "").trim(),
    validacaoQa: String(data.validacao_qa ?? data.o_que_deve_ser_validado ?? "").trim(),
    branchReferencia: String(data.branch_referencia ?? "").trim(),
    commitReferencia: String(data.commit_referencia ?? "").trim(),
    desenvolvedor: String(data.desenvolvedor ?? data.id_desenvolvedor ?? "").trim(),
    dataEntregaTeste: String(data.data_entrega_teste ?? "").trim(),
  };
}

function parseTest(raw: string | undefined): TestDocumentacao | undefined {
  const parsed = safeJsonParse(raw);
  if (!parsed || typeof parsed !== "object") {
    if (!raw?.trim()) return undefined;
    return { casos: [] };
  }
  const data = parsed as Record<string, unknown>;
  const rawCases = Array.isArray(data.casos) ? data.casos : [];
  return {
    casos: rawCases.map((item) => {
      const value = item as Record<string, unknown>;
      return {
        resumo: String(value.resumo ?? "").trim(),
        passos: String(value.passos ?? value.passos_execucao ?? "").trim(),
        resultadoEsperado: String(value.resultado_esperado ?? "").trim(),
        resultadoObtido: String(value.resultado_obtido ?? "").trim(),
        status: ["APROVADO", "REPROVADO"].includes(String(value.status ?? "").trim())
          ? (String(value.status).trim() as "APROVADO" | "REPROVADO")
          : "PENDENTE",
        executor: String(value.executor ?? value.usuario_executor ?? "").trim(),
        dataExecucao: String(value.data_execucao ?? "").trim(),
        evidencia: String(value.evidencia ?? value.observacao ?? "").trim(),
      };
    }),
  };
}

function parseDeploy(raw: string | undefined): DeployDocumentacao | undefined {
  const parsed = safeJsonParse(raw);
  if (!parsed || typeof parsed !== "object") {
    if (!raw?.trim()) return undefined;
    return {
      ...getEmptyActivityDocumentation().deploy!,
      observacoes: raw.trim(),
    };
  }
  const data = parsed as Record<string, unknown>;
  return {
    versaoEntregue: String(data.versao_entregue ?? data.versao ?? "").trim(),
    ambiente: String(data.ambiente ?? "").trim(),
    dataDeploy: String(data.data_deploy ?? "").trim(),
    responsavelDeploy: String(
      data.responsavel_deploy ?? data.responsavel ?? data.id_responsavel_deploy ?? "",
    ).trim(),
    observacoes: String(data.observacoes ?? "").trim(),
  };
}

export function parseBackendDocumentation(
  docs: Record<string, string> | null | undefined,
): ActivityDocumentation {
  const data = docs ?? {};
  return {
    backlog: parseBacklog(data.doc_requisito),
    toDo: parseToDo(data.prontidao_dev),
    develop: parseDevelop(data.entrega_dev),
    test: parseTest(data.casos_teste),
    deploy: parseDeploy(data.deploy),
    encerramento: String(data.encerramento ?? "").trim(),
  };
}

export function serializeBacklogDocumentacao(backlog: BacklogDocumentacao) {
  return JSON.stringify({
    nome_funcionalidade: backlog.nomeFuncionalidade.trim(),
    descricao_detalhada: backlog.descricaoDetalhada.trim(),
    restricoes: backlog.restricoes.trim(),
    requisitos_funcionais: backlog.requisitosFuncionais.map((item) => item.trim()).filter(Boolean),
    requisitos_nao_funcionais: backlog.requisitosNaoFuncionais
      .map((item) => item.trim())
      .filter(Boolean),
    regras_negocio: backlog.regrasNegocio.map((item) => item.trim()).filter(Boolean),
    criterios_aceitacao: backlog.criteriosAceitacao.map((item) => item.trim()).filter(Boolean),
  });
}

export function serializeToDoDocumentacao(toDo: ToDoDocumentacao, requisitoId: number) {
  return JSON.stringify({
    id_requisito: requisitoId,
    responsavel_desenvolvimento: toDo.responsavelDesenvolvimento.trim(),
    registrado_por: toDo.registradoPor.trim(),
    data_prontidao: toDo.dataProntidao.trim(),
    observacoes_tecnicas: toDo.observacoesTecnicas.trim(),
    checklist: toDo.checklist,
  });
}

export function serializeDevelopDocumentacao(
  develop: DevelopDocumentacao,
  requisitoId: number,
) {
  return JSON.stringify({
    id_requisito: requisitoId,
    nome_entrega: develop.nomeEntrega.trim(),
    descricao_desenvolvido: develop.descricaoDesenvolvido.trim(),
    alteracoes: develop.alteracoes.trim(),
    validacao_qa: develop.validacaoQa.trim(),
    branch_referencia: develop.branchReferencia.trim(),
    commit_referencia: develop.commitReferencia.trim(),
    desenvolvedor: develop.desenvolvedor.trim(),
    data_entrega_teste: develop.dataEntregaTeste.trim(),
  });
}

export function serializeTestDocumentacao(test: TestDocumentacao, requisitoId: number) {
  return JSON.stringify({
    id_requisito: requisitoId,
    casos: test.casos.map((caso) => ({
      resumo: caso.resumo.trim(),
      passos: caso.passos.trim(),
      resultado_esperado: caso.resultadoEsperado.trim(),
      resultado_obtido: caso.resultadoObtido.trim(),
      status: caso.status,
      executor: caso.executor.trim(),
      data_execucao: caso.dataExecucao.trim(),
      evidencia: caso.evidencia.trim(),
    })),
  });
}

export function serializeDeployDocumentacao(
  deploy: DeployDocumentacao,
  requisitoId: number,
) {
  return JSON.stringify({
    id_requisito: requisitoId,
    versao_entregue: deploy.versaoEntregue.trim(),
    ambiente: deploy.ambiente.trim(),
    data_deploy: deploy.dataDeploy.trim(),
    responsavel_deploy: deploy.responsavelDeploy.trim(),
    observacoes: deploy.observacoes.trim(),
  });
}

export function isDeployDocumentacaoEmpty(deploy: DeployDocumentacao | undefined): boolean {
  if (!deploy) return true;
  return ![
    deploy.versaoEntregue,
    deploy.ambiente,
    deploy.dataDeploy,
    deploy.responsavelDeploy,
    deploy.observacoes,
  ].some((value) => value.trim().length > 0);
}

export function isTestDocumentacaoEmpty(test: TestDocumentacao | undefined): boolean {
  if (!test?.casos?.length) return true;
  return !test.casos.some(isCasoTestePreenchido);
}

export function isDevelopDocumentacaoEmpty(develop: DevelopDocumentacao | undefined): boolean {
  if (!develop) return true;
  return ![
    develop.nomeEntrega,
    develop.descricaoDesenvolvido,
    develop.alteracoes,
    develop.validacaoQa,
    develop.branchReferencia,
    develop.commitReferencia,
    develop.desenvolvedor,
    develop.dataEntregaTeste,
  ].some((value) => value.trim().length > 0);
}

export function isToDoDocumentacaoEmpty(toDo: ToDoDocumentacao | undefined): boolean {
  if (!toDo) return true;
  return ![
    toDo.responsavelDesenvolvimento,
    toDo.registradoPor,
    toDo.dataProntidao,
    toDo.observacoesTecnicas,
    ...toDo.checklist,
  ].some((value) => value.trim().length > 0);
}

export function isBacklogDocumentacaoEmpty(backlog: BacklogDocumentacao): boolean {
  return ![
    backlog.nomeFuncionalidade,
    backlog.descricaoDetalhada,
    backlog.restricoes,
    ...backlog.requisitosFuncionais,
    ...backlog.requisitosNaoFuncionais,
    ...backlog.regrasNegocio,
    ...backlog.criteriosAceitacao,
  ].some((value) => value.trim().length > 0);
}

/** Payload mínimo que satisfaz o gate de BACKLOG (doc_requisito). */
export function buildMarcarComoFeitoBacklog(tituloAtividade?: string): BacklogDocumentacao {
  const nome = (tituloAtividade || "").trim() || "Funcionalidade (confirmada na esteira)";
  return {
    nomeFuncionalidade: nome,
    descricaoDetalhada: "Documentação mínima gerada para avançar na esteira.",
    restricoes: "Nenhuma",
    requisitosFuncionais: ["Requisito funcional confirmado na esteira."],
    requisitosNaoFuncionais: ["Requisito não funcional confirmado na esteira."],
    regrasNegocio: ["Regra de negócio confirmada na esteira."],
    criteriosAceitacao: ["Critério de aceitação confirmado na esteira."],
  };
}

/** Payload mínimo que satisfaz o gate de TEST (casos_teste). */
export function buildMarcarComoFeitoTest(): TestDocumentacao {
  return {
    casos: [
      {
        resumo: "Validação mínima na esteira",
        passos: "1. Executar o cenário principal.",
        resultadoEsperado: "Comportamento esperado conforme requisito.",
        resultadoObtido: "Comportamento conforme esperado.",
        status: "APROVADO",
        executor: "Confirmado na esteira",
        dataExecucao: todayIsoDate(),
        evidencia: MARCAR_FEITO_OBS,
      },
    ],
  };
}

/** Payload mínimo que satisfaz o gate de prontidão (TO DO). */
export function buildMarcarComoFeitoToDo(): ToDoDocumentacao {
  return {
    responsavelDesenvolvimento: "Confirmado na esteira",
    registradoPor: "Confirmado na esteira",
    dataProntidao: todayIsoDate(),
    observacoesTecnicas: MARCAR_FEITO_OBS,
    checklist: TODO_CHECKLIST_OPTIONS.map((option) => option.value),
  };
}

/** Payload mínimo que satisfaz o gate de entrega (DEVELOP). */
export function buildMarcarComoFeitoDevelop(
  requisitoId: number,
  tituloAtividade?: string,
): DevelopDocumentacao {
  const nome = (tituloAtividade || "").trim() || `Atividade #${requisitoId}`;
  return {
    nomeEntrega: nome,
    descricaoDesenvolvido: "Desenvolvimento concluído (confirmação operacional).",
    alteracoes: "N/A",
    validacaoQa: "Validar na fase TEST.",
    branchReferencia: "N/A",
    commitReferencia: "N/A",
    desenvolvedor: "Confirmado na esteira",
    dataEntregaTeste: todayIsoDate(),
  };
}

/** Payload mínimo que satisfaz o gate de deploy (DEPLOY). */
export function buildMarcarComoFeitoDeploy(): DeployDocumentacao {
  return {
    versaoEntregue: "1.0.0",
    ambiente: "Produção",
    dataDeploy: todayIsoDate(),
    responsavelDeploy: "Confirmado na esteira",
    observacoes: MARCAR_FEITO_OBS,
  };
}

export function buildMarcarComoFeitoEncerramento(encerramentoAtual?: string): string {
  const atual = (encerramentoAtual || "").trim();
  if (atual) return atual;
  return "Atividade encerrada na esteira Kanban.";
}

export type DocumentationPhaseKey =
  | "backlog"
  | "to-do"
  | "develop"
  | "test"
  | "deploy"
  | "encerramento";

/** Conteúdo vazio para desmarcar uma fase e voltar ao estado pendente. */
export function serializeClearPhaseContent(
  phase: DocumentationPhaseKey,
  requisitoId: number,
): string {
  const empty = getEmptyActivityDocumentation();
  switch (phase) {
    case "backlog":
      return serializeBacklogDocumentacao(empty.backlog);
    case "to-do":
      return serializeToDoDocumentacao(empty.toDo!, requisitoId);
    case "develop":
      return serializeDevelopDocumentacao(empty.develop!, requisitoId);
    case "test":
      return serializeTestDocumentacao(empty.test!, requisitoId);
    case "deploy":
      return serializeDeployDocumentacao(empty.deploy!, requisitoId);
    case "encerramento":
      return "";
    default:
      return "";
  }
}

export function getActivityDocumentation(cardId: string): ActivityDocumentation {
  return DOCUMENTATION_BY_CARD_ID[cardId] ?? getEmptyActivityDocumentation();
}
