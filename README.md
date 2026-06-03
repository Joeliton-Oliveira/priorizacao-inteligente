# Projeto Mauricio

Configuração inicial para desenvolvimento local com `Docker Compose`, subindo:

- `frontend`: Next.js em `http://localhost:3000`
- `backend`: FastAPI em `http://localhost:8000`
- `postgres`: PostgreSQL 18 em `localhost:5432`

## Pré-requisitos

- Docker
- Docker Compose

## Subindo o ambiente

Antes de subir o ambiente, ajuste o arquivo `.env` da raiz. Há um modelo pronto em `.env.example`.

```bash
docker compose up --build
```

O frontend roda em modo de desenvolvimento com `next dev --webpack`, mantendo recarga durante o desenvolvimento e evitando um erro `500` observado com o Turbopack dentro do container.

## Serviços

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Postgres:
  - database: `Matriz`
  - user: `postgres`
  - password: `postgres`

## Bootstrap do banco

O schema inicial é carregado automaticamente a partir de `backend/db/schema.sql` no primeiro start do volume do Postgres.

Se precisar recriar o banco do zero e reaplicar o schema:

```bash
docker compose down -v
docker compose up --build
```

## Variáveis de ambiente

- Arquivo principal do Compose: `.env` na raiz
- Modelo compartilhado: `.env.example`
- Referências por projeto:
  - `backend/.env.example`
  - `frontend/.env.example`

O `docker-compose.yml` lê as variáveis da raiz e injeta em cada serviço apenas o conjunto necessário ao `backend` e ao `frontend`, sem deixar os valores espalhados no YAML.

Para a migração do cadastro no Next, o fallback mock de análise ficou desativado por padrão. Se precisar simular a análise sem backend em um ambiente de desenvolvimento, defina `PRIORIZACAO_ANALISE_ALLOW_MOCK_FALLBACK=true`.
