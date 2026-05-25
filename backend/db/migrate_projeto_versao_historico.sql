-- Bancos que já têm a tabela projeto (rodar após migrate_projetos.sql):
-- psql -h localhost -U postgres -d Matriz -f db/migrate_projeto_versao_historico.sql

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
