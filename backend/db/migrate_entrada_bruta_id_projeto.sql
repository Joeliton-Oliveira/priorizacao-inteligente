-- Vincular demanda (entrada bruta) a projeto (coluna opcional até migrar para obrigatória).
-- Depois: db/migrate_entrada_bruta_id_projeto_obrigatorio.sql
-- psql -h localhost -U postgres -d Matriz -f db/migrate_entrada_bruta_id_projeto.sql

ALTER TABLE entrada_bruta
    ADD COLUMN IF NOT EXISTS id_projeto INTEGER REFERENCES projeto(id_projeto) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_entrada_bruta_id_projeto ON entrada_bruta(id_projeto);
