import type {
  BacklogDocumentacao,
  DeployDocumentacao,
  TestDocumentacao,
} from "./activity-documentation-data";
import type { CasoTeste } from "./test-case-types";

function listaTemItem(vals: string[] | undefined): boolean {
  return (vals ?? []).some((v) => String(v).trim().length > 0);
}

type BacklogGateOptions = {
  exigirRegrasECriterios?: boolean;
  /** BUG: documento de requisito no BACKLOG não é obrigatório (espelha backend). */
  dispensarDocRequisito?: boolean;
};

/** Espelha eval_fase_docs_doc_requisito_gate (backend). */
export function evalBacklogGate(
  backlog: BacklogDocumentacao,
  options?: BacklogGateOptions,
): { ok: boolean; falta: string[] } {
  if (options?.dispensarDocRequisito) {
    return { ok: true, falta: [] };
  }
  const falta: string[] = [];
  const exigirRegrasECriterios = options?.exigirRegrasECriterios ?? true;
  if (!backlog.nomeFuncionalidade.trim()) falta.push("Nome da funcionalidade");
  if (!backlog.descricaoDetalhada.trim()) falta.push("Descrição detalhada");
  if (!listaTemItem(backlog.requisitosFuncionais)) falta.push("Pelo menos um requisito funcional (RF)");
  if (!listaTemItem(backlog.requisitosNaoFuncionais)) {
    falta.push("Pelo menos um requisito não funcional (RNF)");
  }
  if (exigirRegrasECriterios) {
    if (!listaTemItem(backlog.regrasNegocio)) falta.push("Pelo menos uma regra de negócio");
    if (!listaTemItem(backlog.criteriosAceitacao)) falta.push("Pelo menos um critério de aceitação");
  }
  return { ok: falta.length === 0, falta };
}

function casoAprovadoCompleto(caso: CasoTeste): boolean {
  if (caso.status !== "APROVADO") return false;
  for (const v of [
    caso.resumo,
    caso.passos,
    caso.resultadoEsperado,
    caso.resultadoObtido,
    caso.executor,
    caso.dataExecucao,
    caso.evidencia,
  ]) {
    if (!String(v || "").trim()) return false;
  }
  return true;
}

/** Espelha eval_fase_docs_casos_teste_gate (backend). */
export function evalTestGate(test: TestDocumentacao | undefined): { ok: boolean; falta: string[] } {
  const casos = test?.casos ?? [];
  if (casos.length === 0) {
    return {
      ok: false,
      falta: ["Adicione pelo menos um caso de teste e preencha os campos."],
    };
  }
  if (casos.some(casoAprovadoCompleto)) {
    return { ok: true, falta: [] };
  }
  return {
    ok: false,
    falta: [
      "Pelo menos um caso com status APROVADO",
      "Todos os campos obrigatórios preenchidos (resumo, passos, esperado, obtido, executor, data)",
      "Evidência ou observação do teste (campo Evidência)",
    ],
  };
}

export function backlogPassesGate(backlog: BacklogDocumentacao, options?: BacklogGateOptions): boolean {
  return evalBacklogGate(backlog, options).ok;
}

export function testPassesGate(test: TestDocumentacao | undefined): boolean {
  return evalTestGate(test).ok;
}

/** Espelha eval_fase_docs_deploy_gate (backend). */
export function evalDeployGate(deploy: DeployDocumentacao | undefined): { ok: boolean; falta: string[] } {
  if (!deploy) {
    return {
      ok: false,
      falta: ["Versão entregue", "Ambiente (ex.: produção, homologação, staging)", "Data do deploy", "Responsável pelo deploy"],
    };
  }
  const falta: string[] = [];
  if (!deploy.versaoEntregue.trim()) falta.push("Versão entregue");
  if (!deploy.ambiente.trim()) falta.push("Ambiente (ex.: produção, homologação, staging)");
  if (!deploy.dataDeploy.trim()) falta.push("Data do deploy");
  if (!deploy.responsavelDeploy.trim()) falta.push("Responsável pelo deploy");
  return { ok: falta.length === 0, falta };
}

export function deployPassesGate(deploy: DeployDocumentacao | undefined): boolean {
  return evalDeployGate(deploy).ok;
}
