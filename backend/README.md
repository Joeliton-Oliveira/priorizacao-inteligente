# Matriz de Severidade e Criticidade — Priorização inteligente de requisitos

Aplicação **FastAPI** (API REST) + **Dash** (front monolítico em `app.py`) + **PostgreSQL**. Versão do produto em `version.py` (`__version__`, `RELEASE_DATE`), exibida na barra lateral do Dash.

---

## Como rodar

### Pré-requisitos

- Python 3.x  
- PostgreSQL (ex.: banco `Matriz`)  
- `pip install -r requirements.txt`

### Banco (uma vez)

```bash
psql -h localhost -U postgres -d Matriz -f db/schema.sql
```

Opcional — limpar dados de teste (apaga conteúdo conforme `db/zerar_banco.sql`; confirme o script antes de executar):

```bash
psql -h localhost -U postgres -d Matriz -f db/zerar_banco.sql
```

Para testar Kanban e atividades, use o fluxo normal da aplicação (cadastro, estruturação com IA, Likert, salvar avaliação) ou insira dados via SQL próprio.

Exemplo — **projeto na versão 2.3.11** e **um bug** associado (requer Postgres configurado em `config.py`):

```bash
python3 db/seed_projeto_2311_bug.py
```

### Subir os serviços

Terminal 1 — API (`http://127.0.0.1:8000`, documentação interativa em **`/docs`**):

```bash
python3 api.py
```

Terminal 2 — Dash (`http://127.0.0.1:8051`):

```bash
python3 app.py
```

Se aparecer **«Address already in use»** na porta 8051, pare o processo antigo (`lsof -nP -iTCP:8051 -sTCP:LISTEN` e depois `kill <PID>`) ou use outra porta: `PORT=8052 python3 app.py`.

Use **`app.py` na raiz do projeto** como front principal. Se a sidebar mostrar só quatro itens (sem Projetos, Fila nem «Lista da esteira»), o processo em execução não é este ficheiro — pare o servidor (Ctrl+C) e suba de novo com `python3 app.py` a partir da pasta correta.

Cliente HTTP padrão do front: `http://127.0.0.1:8000` (`services/api_client.py`).

---

## Front-end (Dash): rotas

| Rota | Função |
|------|--------|
| `/` | Cadastro da demanda, **Analisar e estruturar com IA**, Likert, salvamento; **projeto opcional** (`cadastro-id-projeto`). |
| `/atividades` | Matrizes, resumo, **filtros** (tipo, status, busca), tabela com **Projeto** e **Versão**. |
| `/kanban` | Esteira 6 colunas, movimentação com persistência na API; **mensagens** em `kanban-msg` (sucesso, erro, WIP). |
| `/kanban-lista` | **Lista em tabela** das mesmas atividades da esteira (ordenadas por fase); link na sidebar logo abaixo de «Esteira Kanban». |
| `/atividade/<id>` | Hub operacional da atividade (leitura + placeholders para governança). |
| `/projetos` | Projetos: cadastro, evolução de versão, status, histórico, filtros. |
| `/fila` | Duas tabelas (bugs e incrementos/features) via `GET /api/v1/fila/bugs` e `GET /api/v1/fila/incrementos`. |
| `/calibragem` | Ajustes locais de WIP/visualização no Dash; não há configuração manual da fila na API. |

Navegação por `dcc.Link` na sidebar; roteamento em `_router` (`dcc.Location`).

**Stores principais:** `store-atividades`, `store-calibragem`, `store-kanban`, `store-fila`, `store-sidebar-open`, `store-analise`, `store-proj-reload`, `store-kanban-lista`, `store-atividade-detalhe`.

---

## Fluxo ponta a ponta (usuário)

1. **Cadastro** — Preencher demanda, opcionalmente vincular projeto, **Analisar e estruturar com IA**.  
2. Responder **Likert**, informar responsável, **Salvar avaliação**; confirmar diálogo (formulário e vínculo de projeto zerados).  
3. **Atividades** — Ver gráficos e tabela (recarrega lista ao abrir a rota).  
4. **Kanban** — Mover cartões; mensagens de feedback; WIP respeitado.  
5. **Fila** — Ver ordenação sugerida pela API.  
6. **Calibragem** — Ajustes locais de interface/limites do Kanban no próprio Dash.  
7. **Projetos** — Governança de versões em paralelo ao fluxo da demanda.

**Nota:** a **fila da API** é organizada automaticamente pela lógica da matriz/quadrantes; não existe endpoint de calibragem manual da fila no backend.

---

## API REST

- **OpenAPI / Swagger:** `http://127.0.0.1:8000/docs` após subir `api.py` — endpoints agrupados por domínio (Meta, Projetos, Requisitos com estruturação IA + avaliação, Kanban, Fila).  
- **Ping / meta:** `GET /`, `GET /api/v1/status`, `GET /api/v1/ping`.  
- **Projetos:** `POST/GET /api/v1/projetos`, `PATCH /api/v1/projetos/{id}/status`, `POST .../evoluir-versao`, `GET .../historico-versao`.  
- **Requisitos:** `POST /api/v1/requisitos/analise` (estruturação com IA), `GET .../atividades`, `POST .../salvar-avaliacao`, `GET|PUT|POST .../documentacao-fase/...`, `POST .../status`.  
- **Kanban / fila:** `GET /api/v1/kanban/{id}/gates`, `GET /api/v1/fila/bugs`, `GET /api/v1/fila/incrementos`.  

Erros de regra de negócio vêm de `domain/exceptions.py` (404/422/400/502) via handler no FastAPI; o front continua a usar os mesmos paths em `services/api_client.py`.

---

## Arquitetura do back-end

- **Controller:** `api.py` — rotas FastAPI, modelos Pydantic de entrada/saída; não importa `db.*`.  
- **Service:** `services/*` — casos de uso (projetos, avaliação, IA, documentação, Kanban, fila).  
- **Repository:** `db/*_repo.py` — SQL PostgreSQL, linhas → `dict`.  
- **Domain:** `domain/` — exceções tipadas mapeadas para HTTP.  
- **Regras partilhadas:** `fila_priorizacao.py` (fila), `services/kanban_gates.py` (gates documentais), `prompts.py` (IA).

Isto é **Controller → Service → Repository/DB**, com Domain e Pydantic na borda — não um *Model* ORM clássico.

---

## Matriz, fila e Kanban (onde está cada regra)

| Tema | Ficheiros principais |
|------|----------------------|
| **Matriz BUG** | Eixos Criticidade × Severidade; médias Likert em `db/avaliacao_repo.py` (`listar_atividades_*`). |
| **Matriz INCREMENTO** | Esforço × Valor; mesma agregação. |
| **Score e prioridade** | `score = x * y`; faixas ALTA / MEDIA / BAIXA no repo; `score_final` da fila em `fila_priorizacao.py` (quadrante, score, fase e tempo parado). |
| **Fila** | Ordenação automática por quadrante da matriz e score; suporte às visões separadas de bugs e features. |
| **Kanban** | Colunas BACKLOG → … → DONE; avanço **uma** coluna de cada vez; **retrocesso** livre; bloqueio se faltar documentação da fase (`services/kanban_gates.py`, `db/doc_fase_repo.py`). |

---

## Lacunas conhecidas (front)

- Sem export da tabela de atividades, página de detalhe de requisito, paginação em projetos ou edição de nome/descrição de projeto após criar.  
- Nomenclatura de `status_atual` na API vs. colunas do Kanban pode exigir alinhamento no backend.  
- UX mobile / acessibilidade não são foco desta versão.

---

## Testes

```bash
python3 -m pytest tests/ -q
```

Inclui *smoke* do layout Dash, `tests/test_fluxo_feature_kanban.py` (feature INCREMENTO + gates por baia, com mocks de DB) e verificação de que a versão em `version.py` aparece no **Changelog** deste README (ver secção abaixo).

---

## Changelog

Histórico alinhado a `version.py` (`changelog_alinhado_com_version_py` lê este arquivo).

## [1.0.0] — 2026-04-02

- Estrutura da aplicação: cadastro, IA, Likert, matriz, fila automática, Kanban, projetos, rota `/fila`, filtros em atividades, mensagens no Kanban, vínculo projeto ↔ demanda.  
- Versão única em `version.py` consumida pela API (OpenAPI) e pelo Dash.  
- Exibição da versão e data de release na sidebar do Dash.  
- Teste automático do formato semântico da versão.  
- **Documentação:** apenas este `README.md` como documentação do projeto (arquitetura, API, matriz/fila/Kanban); comentários no código apontam para aqui quando relevante. O pytest pode criar `.pytest_cache/README.md` localmente — a pasta está no `.gitignore` e não faz parte da documentação.

<!-- Próximo release: adicionar ## [1.0.1] — AAAA-MM-DD com bullets (dois # antes do colchete). -->
