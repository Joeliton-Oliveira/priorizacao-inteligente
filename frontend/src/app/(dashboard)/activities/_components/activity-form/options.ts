export const DEMAND_TYPE_OPTIONS = [
  { value: "bug", label: "Bug" },
  { value: "feature", label: "Feature" },
];

export const IMPACT_OPTIONS = [
  { value: "nao_impacta", label: "Não impacta operação" },
  { value: "baixo", label: "Impacto baixo" },
  { value: "moderado", label: "Impacto moderado" },
  { value: "alto", label: "Impacto alto" },
  { value: "operacao_parada", label: "Operação parada" },
];

export const FREQUENCY_OPTIONS = [
  { value: "uma_vez", label: "Aconteceu uma vez" },
  { value: "as_vezes", label: "Às vezes" },
  { value: "frequente", label: "Frequente" },
  { value: "sempre", label: "Sempre acontece" },
  { value: "nao_sei", label: "Não sei informar" },
];

export const URGENCY_OPTIONS = [
  { value: "baixa", label: "Baixa" },
  { value: "media", label: "Média" },
  { value: "alta", label: "Alta" },
  { value: "critica", label: "Crítica" },
];

export const FORM_STEPS = [
  {
    id: 1,
    progressLabel: "Demanda e impacto",
    title: "1. Descreva a demanda e o impacto",
    description:
      "Explique a demanda e informe impacto percebido, frequência de ocorrência e urgência.",
  },
  {
    id: 2,
    progressLabel: "Resultado e envio",
    title: "2. Resultado esperado e projeto",
    description:
      "Descreva o resultado esperado, vincule o projeto e envie para estruturação automática com IA.",
  },
];
