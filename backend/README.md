# Backend — API de Priorização

Backend em `FastAPI` com persistência em `PostgreSQL`, responsável por projetos, estruturação com IA, avaliação Likert, matriz, fila, Kanban e documentação por fase.

O frontend atual do produto está em `frontend/` e consome esta API. A referência operacional do workspace é o `docker-compose.yml` da raiz.

## Como rodar

O fluxo principal do projeto está documentado no `README.md` da raiz. Para subir apenas a API localmente dentro da pasta `backend/`:

```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Com Docker Compose, a API sobe em `http://localhost:8000` e a documentação interativa fica em `http://localhost:8000/docs`.

## Responsabilidades

- `api.py`: rotas FastAPI e contratos HTTP
- `services/`: regras de negócio
- `db/`: acesso PostgreSQL e scripts auxiliares
- `domain/`: exceções de domínio
- `prompts.py`: prompt de estruturação com IA
- `fila_priorizacao.py`: cálculo e ordenação da fila

## Endpoints principais

- `GET /api/v1/status`
- `POST /api/v1/projetos`
- `GET /api/v1/projetos`
- `POST /api/v1/requisitos/analise`
- `POST /api/v1/requisitos/salvar-avaliacao`
- `GET /api/v1/requisitos/atividades`
- `POST /api/v1/requisitos/{id}/status`
- `GET /api/v1/fila/bugs`
- `GET /api/v1/fila/incrementos`
- `GET /api/v1/kanban/{id}/gates`
- `GET /api/v1/demandas/{id}/visao-360`
- `GET /api/v1/demandas/{id}/auditoria`

## Seed inicial

Com o Postgres no ar:

```bash
python db/seed_inicial.py          # só se não houver projetos (ou falha se já existir)
python db/seed_inicial.py --force  # remove projetos deste seed e recria
```

Na subida via Docker, o seed roda automaticamente quando a tabela `projeto` está vazia (`SEED_INICIAL_ON_STARTUP=true`).

## Testes

```bash
python3 -m pytest tests/ -q
```

A suíte cobre API, fila, calibragem, regras de negócio, projetos e o fluxo principal de feature + Kanban.

## Changelog

Histórico alinhado a `version.py` (`changelog_alinhado_com_version_py` lê este arquivo).

## [1.1.0] — 2026-06-11

- Seed inicial: dois bugs com mesma criticidade/severidade para demonstrar sobreposição na matriz.
- Seed inicial: responsáveis e avaliadores com nomes fictícios; `--force` recria dados sem violar FKs.
- Matriz de atividades: tooltip com títulos destacados, ícones de bug/incremento e efeito glass.

## [1.0.0] — 2026-04-02

- Estrutura da aplicação: cadastro, IA, Likert, matriz, fila automática, Kanban, projetos, rota `/fila`, filtros em atividades, mensagens no Kanban, vínculo projeto ↔ demanda.
- Versão única em `version.py` consumida pela API.
- Teste automático do formato semântico da versão.
- Documentação operacional centralizada no `README.md` da raiz e neste `README.md` do backend.

<!-- Próximo release: adicionar ## [x.y.z] — AAAA-MM-DD com bullets (dois # antes do colchete). -->
