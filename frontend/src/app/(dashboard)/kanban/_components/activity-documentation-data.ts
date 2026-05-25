import { isCasoTestePreenchido, type CasoTeste } from "./test-case-types";

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
};

const BACKLOG_EXEMPLO: BacklogDocumentacao = {
  nomeFuncionalidade: "sdfg",
  descricaoDetalhada: "dfghj",
  restricoes: "fghj",
  requisitosFuncionais: ["dfgh"],
  requisitosNaoFuncionais: ["sdfgh"],
  regrasNegocio: ["dfgh"],
  criteriosAceitacao: ["dfgh"],
};

export const DOCUMENTATION_BY_CARD_ID: Record<string, ActivityDocumentation> = {
  "1": { backlog: BACKLOG_EXEMPLO },
  "2": { backlog: BACKLOG_EXEMPLO },
  "3": { backlog: BACKLOG_EXEMPLO },
};

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

export function getActivityDocumentation(cardId: string): ActivityDocumentation {
  return (
    DOCUMENTATION_BY_CARD_ID[cardId] ?? {
      backlog: {
        nomeFuncionalidade: "",
        descricaoDetalhada: "",
        restricoes: "",
        requisitosFuncionais: [],
        requisitosNaoFuncionais: [],
        regrasNegocio: [],
        criteriosAceitacao: [],
      },
      toDo: undefined,
      develop: undefined,
      test: undefined,
      deploy: undefined,
    }
  );
}
