-- Demandas sem projeto violam a regra de negócio: remove cascata e torna id_projeto obrigatório.
-- Ordem: respostas → avaliações → status → requisito → entrada bruta.
-- psql -h localhost -U postgres -d Matriz -f db/migrate_entrada_bruta_id_projeto_obrigatorio.sql

DELETE FROM resposta_avaliacao
WHERE id_avaliacao IN (
  SELECT ra.id_avaliacao FROM avaliacao_requisito ra
  JOIN requisito_estruturado r ON ra.id_requisito = r.id_requisito
  JOIN entrada_bruta eb ON r.id_entrada_bruta = eb.id_entrada_bruta
  WHERE eb.id_projeto IS NULL
);

DELETE FROM avaliacao_requisito
WHERE id_requisito IN (
  SELECT r.id_requisito FROM requisito_estruturado r
  JOIN entrada_bruta eb ON r.id_entrada_bruta = eb.id_entrada_bruta
  WHERE eb.id_projeto IS NULL
);

DELETE FROM status_requisito
WHERE id_requisito IN (
  SELECT r.id_requisito FROM requisito_estruturado r
  JOIN entrada_bruta eb ON r.id_entrada_bruta = eb.id_entrada_bruta
  WHERE eb.id_projeto IS NULL
);

DELETE FROM requisito_estruturado
WHERE id_entrada_bruta IN (SELECT id_entrada_bruta FROM entrada_bruta WHERE id_projeto IS NULL);

DELETE FROM entrada_bruta WHERE id_projeto IS NULL;

ALTER TABLE entrada_bruta ALTER COLUMN id_projeto SET NOT NULL;

ALTER TABLE entrada_bruta DROP CONSTRAINT IF EXISTS entrada_bruta_id_projeto_fkey;
ALTER TABLE entrada_bruta ADD CONSTRAINT entrada_bruta_id_projeto_fkey
  FOREIGN KEY (id_projeto) REFERENCES projeto(id_projeto) ON DELETE RESTRICT;
