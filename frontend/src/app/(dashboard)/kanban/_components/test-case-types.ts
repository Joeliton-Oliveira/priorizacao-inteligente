export type CasoTesteStatus = "PENDENTE" | "APROVADO" | "REPROVADO";

export type CasoTeste = {
  resumo: string;
  passos: string;
  resultadoEsperado: string;
  resultadoObtido: string;
  status: CasoTesteStatus;
  executor: string;
  dataExecucao: string;
  evidencia: string;
};

export const CASO_TESTE_STATUS_OPTIONS: { value: CasoTesteStatus; label: string }[] = [
  { value: "PENDENTE", label: "Pendente" },
  { value: "APROVADO", label: "Aprovado" },
  { value: "REPROVADO", label: "Reprovado" },
];

export function casoTesteVazio(): CasoTeste {
  return {
    resumo: "",
    passos: "",
    resultadoEsperado: "",
    resultadoObtido: "",
    status: "PENDENTE",
    executor: "",
    dataExecucao: "",
    evidencia: "",
  };
}

export function normalizeCasoTesteStatus(status: string): CasoTesteStatus {
  const upper = status.trim().toUpperCase();
  if (upper === "APROVADO" || upper === "REPROVADO") return upper;
  return "PENDENTE";
}

export function isCasoTestePreenchido(caso: CasoTeste): boolean {
  return [
    caso.resumo,
    caso.passos,
    caso.resultadoEsperado,
    caso.resultadoObtido,
    caso.executor,
    caso.dataExecucao,
    caso.evidencia,
  ].some((value) => value.trim().length > 0) || caso.status !== "PENDENTE";
}
