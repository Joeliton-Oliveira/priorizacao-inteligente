-- Schema inicial para salvar avaliações e respostas
-- Banco: Matriz
-- Nota: usuario_criacao e usuario_avaliador são textos livres (sem FK para tabela de usuário).
--       Quando o sistema de login existir, pode-se criar vínculo com a tabela de usuários.
-- Ordem: projeto antes de entrada_bruta (FK id_projeto).

-- Projetos acompanhados pelo sistema (novo no cadastro ou legado com versão informada)
CREATE TABLE IF NOT EXISTS projeto (
    id_projeto SERIAL PRIMARY KEY,
    nome_projeto VARCHAR(255) NOT NULL,
    descricao TEXT,
    responsavel VARCHAR(255),
    tipo_origem VARCHAR(20) NOT NULL CHECK (tipo_origem IN ('novo', 'existente')),
    versao_inicial VARCHAR(32) NOT NULL,
    versao_atual VARCHAR(32) NOT NULL,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_ultima_atualizacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_projeto VARCHAR(20) NOT NULL DEFAULT 'ativo'
        CHECK (status_projeto IN ('ativo', 'arquivado', 'descontinuado'))
);

-- Histórico de evoluções de versão por projeto (auditoria / governança)
CREATE TABLE IF NOT EXISTS projeto_versao_historico (
    id_historico SERIAL PRIMARY KEY,
    id_projeto INTEGER NOT NULL REFERENCES projeto(id_projeto) ON DELETE CASCADE,
    versao_anterior VARCHAR(32) NOT NULL,
    versao_nova VARCHAR(32) NOT NULL,
    nivel_evolucao VARCHAR(16) NOT NULL CHECK (nivel_evolucao IN ('patch', 'minor', 'major')),
    motivo TEXT,
    usuario_responsavel VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projeto_versao_hist_projeto ON projeto_versao_historico(id_projeto, criado_em DESC);

-- Entrada bruta (texto original + dados do cadastro)
CREATE TABLE IF NOT EXISTS entrada_bruta (
    id_entrada_bruta SERIAL PRIMARY KEY,
    texto_original TEXT NOT NULL,
    usuario_criacao VARCHAR(255),  -- texto livre, sem FK
    perfil_solicitante VARCHAR(50),
    modulo_afetado VARCHAR(255),
    contexto_negocio TEXT,
    objetivo_desejado TEXT,
    dados_cadastro_json JSONB,
    id_projeto INTEGER NOT NULL REFERENCES projeto(id_projeto) ON DELETE RESTRICT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entrada_bruta_id_projeto ON entrada_bruta(id_projeto);

-- Requisito estruturado (saída da IA)
CREATE TABLE IF NOT EXISTS requisito_estruturado (
    id_requisito SERIAL PRIMARY KEY,
    id_entrada_bruta INTEGER REFERENCES entrada_bruta(id_entrada_bruta),
    titulo VARCHAR(500) NOT NULL,
    descricao_refinada TEXT,
    tipo_tarefa VARCHAR(20) NOT NULL,
    objetivo TEXT,
    finalidade TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Avaliação (quem respondeu, quando)
CREATE TABLE IF NOT EXISTS avaliacao_requisito (
    id_avaliacao SERIAL PRIMARY KEY,
    id_requisito INTEGER NOT NULL REFERENCES requisito_estruturado(id_requisito),
    usuario_avaliador VARCHAR(255) NOT NULL,  -- texto livre, sem FK
    perfil_avaliador VARCHAR(50),
    data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Respostas às perguntas
CREATE TABLE IF NOT EXISTS resposta_avaliacao (
    id_resposta SERIAL PRIMARY KEY,
    id_avaliacao INTEGER NOT NULL REFERENCES avaliacao_requisito(id_avaliacao),
    id_pergunta INTEGER NOT NULL,
    texto_pergunta TEXT,
    dimensao VARCHAR(50),
    valor_numerico INTEGER NOT NULL,
    data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status atual de cada requisito na esteira Kanban (BACKLOG, TO_DO, DEVELOP, TEST, DEPLOY, DONE)
CREATE TABLE IF NOT EXISTS status_requisito (
    id_requisito INTEGER PRIMARY KEY REFERENCES requisito_estruturado(id_requisito) ON DELETE CASCADE,
    status_atual VARCHAR(50) NOT NULL
);
