export const DEMAND_TYPE_OPTIONS = [
  { value: "nao_sei", label: "Não sei informar" },
  { value: "bug", label: "Bug" },
  { value: "feature", label: "Feature" },
  { value: "melhoria", label: "Melhoria" },
  { value: "outro", label: "Outro" },
];

export const FREQUENCY_OPTIONS = [
  { value: "sempre", label: "Sempre" },
  { value: "frequentemente", label: "Frequentemente" },
  { value: "as_vezes", label: "Às vezes" },
  { value: "raramente", label: "Raramente" },
  { value: "nunca", label: "Nunca observado" },
];

export const URGENCY_OPTIONS = [
  { value: "critica", label: "Crítica" },
  { value: "alta", label: "Alta" },
  { value: "media", label: "Média" },
  { value: "baixa", label: "Baixa" },
];

export const TEMPORARY_WORKAROUND_OPTIONS = [
  { value: "sim", label: "Sim" },
  { value: "nao", label: "Não" },
  { value: "nao_sei", label: "Não sei" },
];

export const FORM_STEPS = [
  { id: 1, title: "Identificação da Demanda" },
  { id: 2, title: "Impacto e Priorização" },
  { id: 3, title: "Contexto" },
];
