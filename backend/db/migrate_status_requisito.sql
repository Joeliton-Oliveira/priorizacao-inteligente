-- Tabela de status Kanban por requisito (faltava no schema inicial).
CREATE TABLE IF NOT EXISTS status_requisito (
    id_requisito INTEGER PRIMARY KEY REFERENCES requisito_estruturado(id_requisito) ON DELETE CASCADE,
    status_atual VARCHAR(50) NOT NULL
);
