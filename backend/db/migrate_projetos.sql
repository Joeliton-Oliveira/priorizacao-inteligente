-- Executar em bancos já existentes (uma vez):
-- psql -h localhost -U postgres -d Matriz -f db/migrate_projetos.sql

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

-- Histórico de versões (pode rodar também migrate_projeto_versao_historico.sql isolado)
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
