-- Documentação por fase Kanban (evidências para avançar colunas).
-- psql -h localhost -U postgres -d Matriz -f db/migrate_requisito_doc_fase.sql

CREATE TABLE IF NOT EXISTS requisito_doc_fase (
    id_requisito INTEGER NOT NULL REFERENCES requisito_estruturado(id_requisito) ON DELETE CASCADE,
    fase_codigo VARCHAR(40) NOT NULL,
    conteudo TEXT NOT NULL DEFAULT '',
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_requisito, fase_codigo),
    CONSTRAINT requisito_doc_fase_codigo_check CHECK (fase_codigo IN (
        'doc_requisito', 'prontidao_dev', 'entrega_dev', 'casos_teste', 'deploy', 'encerramento'
    ))
);

CREATE INDEX IF NOT EXISTS idx_requisito_doc_fase_requisito ON requisito_doc_fase(id_requisito);
