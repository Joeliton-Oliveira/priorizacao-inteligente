-- Zera todas as tabelas do banco (dados apenas; estrutura permanece).
-- Ordem: filhas primeiro por causa das FKs.
-- RESTART IDENTITY: faz os SERIAL voltarem a começar em 1.

TRUNCATE TABLE projeto_versao_historico RESTART IDENTITY CASCADE;
TRUNCATE TABLE projeto RESTART IDENTITY CASCADE;
TRUNCATE TABLE resposta_avaliacao RESTART IDENTITY CASCADE;
TRUNCATE TABLE avaliacao_requisito RESTART IDENTITY CASCADE;
TRUNCATE TABLE requisito_estruturado RESTART IDENTITY CASCADE;
TRUNCATE TABLE entrada_bruta RESTART IDENTITY CASCADE;
