-- Schema inicial para salvar avaliações e respostas
-- Banco: Matriz
-- Nota: usuario_criacao e usuario_avaliador são textos livres (sem FK para tabela de usuário).
--       Quando o sistema de login existir, pode-se criar vínculo com a tabela de usuários.

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
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
