import type { ActivityFormData } from "@/lib/activity-form-draft";
import type { AnaliseRequisitoResponse, LikertOption, PerguntaAvaliacao } from "./types";
import { buildAnaliseRequestBody } from "./map-form-to-analise";

const LIKERT: LikertOption[] = [
  { rotulo: "Muito baixo", valor: 1 },
  { rotulo: "Baixo", valor: 2 },
  { rotulo: "Moderado", valor: 3 },
  { rotulo: "Alto", valor: 4 },
  { rotulo: "Muito alto", valor: 5 },
];

function bugQuestions(ctx: string): PerguntaAvaliacao[] {
  return [
    {
      id_pergunta: 1,
      texto: `Qual o grau de impacto deste problema nos objetivos de negócio e na experiência do usuário, considerando o contexto "${ctx}"?`,
      dimensao: "CRITICIDADE",
      opcoes_resposta: LIKERT,
    },
    {
      id_pergunta: 2,
      texto:
        "Quantos usuários ou processos de negócio são potencialmente afetados por este problema?",
      dimensao: "CRITICIDADE",
      opcoes_resposta: LIKERT,
    },
    {
      id_pergunta: 3,
      texto:
        "Em que medida a falha prejudica a funcionalidade principal do sistema, considerando o contorno informado?",
      dimensao: "SEVERIDADE",
      opcoes_resposta: LIKERT,
    },
    {
      id_pergunta: 4,
      texto:
        "Qual o risco de o problema causar perda de dados ou comportamento imprevisível no sistema?",
      dimensao: "SEVERIDADE",
      opcoes_resposta: LIKERT,
    },
  ];
}

function incrementQuestions(ctx: string): PerguntaAvaliacao[] {
  return [
    {
      id_pergunta: 1,
      texto: `Quanto esforço de desenvolvimento esta melhoria exige, no contexto "${ctx}"?`,
      dimensao: "ESFORCO",
      opcoes_resposta: LIKERT,
    },
    {
      id_pergunta: 2,
      texto: "Há dependências externas que aumentam o esforço de entrega?",
      dimensao: "ESFORCO",
      opcoes_resposta: LIKERT,
    },
    {
      id_pergunta: 3,
      texto: "Quanto valor de negócio esta melhoria entrega ao time ou ao produto?",
      dimensao: "VALOR",
      opcoes_resposta: LIKERT,
    },
    {
      id_pergunta: 4,
      texto: "O benefício justifica priorizar esta melhoria em relação a outras demandas?",
      dimensao: "VALOR",
      opcoes_resposta: LIKERT,
    },
  ];
}

export function mockAnaliseFromForm(form: ActivityFormData): AnaliseRequisitoResponse {
  const body = buildAnaliseRequestBody(form);
  const isBug =
    body.tipo_informado_usuario === "BUG" ||
    (body.tipo_informado_usuario === "NAO_SEI" &&
      /bug|erro|falha|quebr/i.test(form.description));

  const tipo = isBug ? "BUG" : "INCREMENTO";
  const ctx = form.businessImportance.trim() || form.systemArea.trim() || "geral";
  const titulo =
    form.description.trim().slice(0, 80) ||
    (tipo === "BUG" ? "Problema reportado" : "Melhoria solicitada");

  return {
    texto_original: form.description.trim(),
    titulo_requisito: titulo,
    descricao_requisito: form.description.trim(),
    tipo_requisito: tipo,
    objetivo: form.expectedResult.trim() || "Corrigir ou entregar o comportamento esperado.",
    finalidade:
      form.businessImportance.trim() ||
      "Garantir estabilidade e valor ao usuário do sistema.",
    perguntas_avaliacao:
      tipo === "BUG" ? bugQuestions(ctx) : incrementQuestions(ctx),
  };
}
