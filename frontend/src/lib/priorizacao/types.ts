export type LikertOption = {
  rotulo: string;
  valor: number;
};

export type MatrixPoint = {
  x: number;
  y: number;
  titulo: string;
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

export type ProjetoListItem = {
  id_projeto: number;
  nome_projeto: string;
  versao_atual?: string | null;
  status_projeto?: string | null;
};

export type SalvarAvaliacaoResponse = {
  sucesso: boolean;
  id_entrada_bruta: number;
  id_requisito: number;
  id_avaliacao: number;
  versao_projeto_atualizada?: string;
  warning?: string;
};

export type AtividadePriorizada = {
  id: number;
  titulo: string;
  tipo_requisito: string;
  coordenada_x: number;
  coordenada_y: number;
  score: number;
  prioridade_categorica: string;
  status_atual: string;
  id_projeto?: number | null;
  nome_projeto?: string | null;
  versao_projeto?: string | null;
  data_avaliacao?: string | null;
};

export type FilaItem = AtividadePriorizada & {
  dias_parado?: number;
  score_base?: number;
  bonus_tempo?: number;
  bonus_quadrante?: number;
  bonus_fase?: number;
  bonus_manual?: number;
  score_final?: number;
  faixa?: string;
  fila_ordem_quadrante?: number;
  fila_quadrante_nome?: string;
  fila_distancia_ideal?: number;
  /** Referência do quadrante atual (não é um canto global da matriz). */
  fila_canto_ideal_x?: number;
  fila_canto_ideal_y?: number;
};

export type ProjetoStatus = "ativo" | "arquivado" | "descontinuado";
export type ProjetoTipoOrigem = "novo" | "existente";

export type ProjetoDetalhado = ProjetoListItem & {
  descricao?: string | null;
  responsavel?: string | null;
  tipo_origem?: ProjetoTipoOrigem | null;
  versao_inicial?: string | null;
  data_cadastro?: string | null;
  data_ultima_atualizacao?: string | null;
  ultima_evolucao_em?: string | null;
  ultima_evolucao_por?: string | null;
  ultima_evolucao_nivel?: string | null;
  ultima_evolucao_versao?: string | null;
};

export type ProjetoHistoricoVersao = {
  id_historico: number;
  id_projeto: number;
  versao_anterior: string;
  versao_nova: string;
  nivel_evolucao: string;
  motivo?: string | null;
  usuario_responsavel?: string | null;
  criado_em: string;
};

export type ConfigFila = {
  vazao: {
    bugs: number;
    incrementos: number;
  };
  envelhecimento: {
    intervalo_dias: number;
    incremento_base: number;
    limite_maximo: number | null;
  };
  quadrantes_incremento: Record<string, number>;
  quadrantes_bug: Record<string, number>;
  fases: Record<string, number>;
  incremento_por_faixa_bug: Record<string, number>;
  incremento_por_faixa_incremento: Record<string, number>;
  wip: {
    TO_DO: number;
    DEVELOP: number;
    TEST: number;
    DEPLOY: number;
  };
};

export type KanbanWipDestino = {
  coluna: string;
  ocupacao: number;
  limite: number;
};

export type KanbanGatesResponse = {
  id_requisito: number;
  status_atual: string;
  coluna_kanban: string;
  proxima_coluna: string | null;
  pode_avancar_documentacao: boolean;
  pode_avancar_wip?: boolean;
  wip_destino?: KanbanWipDestino | null;
  falta_documentacao: string[];
};

export type Visao360DemandaResponse = {
  identificacao: {
    id_requisito: number;
    id_entrada_bruta: number;
    titulo: string;
    descricao_requisito: string;
    tipo_requisito: string;
    status_atual: string;
    data_criacao_requisito?: string | null;
    projeto?: {
      id_projeto?: number | null;
      nome_projeto?: string | null;
      versao_atual?: string | null;
      status_projeto?: string | null;
    };
  };
  origem_demanda: {
    texto_original: string;
    usuario_criacao?: string | null;
    perfil_solicitante?: string | null;
    modulo_afetado?: string | null;
    contexto_negocio?: string | null;
    objetivo_desejado?: string | null;
    ha_contorno?: string | null;
    sistema_ou_produto?: string | null;
    impacto_percebido_usuario?: string | null;
    frequencia_ocorrencia?: string | null;
    urgencia_percebida?: string | null;
    data_criacao_entrada?: string | null;
  };
  estruturacao_ia: {
    titulo_requisito: string;
    descricao_requisito: string;
    tipo_requisito: string;
    objetivo: string;
    finalidade: string;
  };
  avaliacao: {
    id_avaliacao?: number | null;
    usuario_avaliador?: string | null;
    perfil_avaliador?: string | null;
    data_avaliacao?: string | null;
    coordenada_x: number;
    coordenada_y: number;
    score: number;
    prioridade_categorica: string;
    eixos: string;
  };
  respostas: RespostaAvaliacaoPayload[];
  documentacao_fase: Record<string, string>;
  gates: KanbanGatesResponse;
};

export type EventoAuditoria = {
  tipo: string;
  titulo: string;
  descricao: string;
  quando?: string | null;
  responsavel?: string | null;
};

export type AuditoriaDemandaResponse = {
  id_requisito: number;
  titulo: string;
  tipo_requisito: string;
  eventos: EventoAuditoria[];
};
