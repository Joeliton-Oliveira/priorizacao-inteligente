-- Preenche status inicial BACKLOG para requisitos avaliados sem linha em status_requisito.
-- Seguro para reexecução: só insere quando não existe registro para o requisito.
INSERT INTO status_requisito (id_requisito, status_atual)
SELECT r.id_requisito, 'BACKLOG'
FROM requisito_estruturado r
JOIN avaliacao_requisito ra ON ra.id_requisito = r.id_requisito
LEFT JOIN status_requisito sr ON sr.id_requisito = r.id_requisito
WHERE sr.id_requisito IS NULL;
