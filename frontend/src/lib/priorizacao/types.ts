export type LikertOption = {
  rotulo: string;
  valor: number;
};

export type PerguntaAvaliacao = {
  id_pergunta: number;
  texto: string;
  dimensao: string;
  opcoes_resposta: LikertOption[];
};

export type AnaliseRequisitoResponse = {
  texto_original: string;
  titulo_requisito: string;
  descricao_requisito: string;
  tipo_requisito: "BUG" | "INCREMENTO" | string;
  objetivo: string;
  finalidade: string;
  perguntas_avaliacao: PerguntaAvaliacao[];
};

export type RespostaAvaliacaoPayload = {
  id_pergunta: number;
  texto: string;
  dimensao: string;
  valor_resposta: number;
};
