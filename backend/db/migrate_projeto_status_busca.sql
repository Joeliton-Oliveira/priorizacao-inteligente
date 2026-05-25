-- Bancos que já têm a tabela projeto (sem status):
-- psql -h localhost -U postgres -d Matriz -f db/migrate_projeto_status_busca.sql

ALTER TABLE projeto
    ADD COLUMN IF NOT EXISTS status_projeto VARCHAR(20) NOT NULL DEFAULT 'ativo';

ALTER TABLE projeto DROP CONSTRAINT IF EXISTS projeto_status_projeto_check;
ALTER TABLE projeto ADD CONSTRAINT projeto_status_projeto_check
    CHECK (status_projeto IN ('ativo', 'arquivado', 'descontinuado'));

UPDATE projeto SET status_projeto = 'ativo' WHERE status_projeto IS NULL;
