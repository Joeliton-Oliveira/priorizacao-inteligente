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

Na primeira subida com banco vazio, o backend executa o **seed inicial** (`backend/db/seed_inicial.py`): 3 projetos, cada um com 2 bugs e 2 features (incrementos), já avaliados na matriz e com alguns cards em colunas diferentes do Kanban. Controle pela variável `SEED_INICIAL_ON_STARTUP` (padrão `true` no `.env.example`).

Recarregar só os dados de demonstração (sem apagar o volume):

```bash
docker compose exec backend python db/seed_inicial.py --force
```

Se precisar recriar o banco do zero e reaplicar o schema + seed:

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
