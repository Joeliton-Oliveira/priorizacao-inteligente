# -*- coding: utf-8 -*-
"""
Cliente para integração com a API de priorização.
Execute a API com: python3 api.py (porta 8000)

Variáveis de ambiente opcionais:
- API_BASE_URL — URL base (default http://127.0.0.1:8000)
- DOCUMENTACAO_FASE_NO_LOCAL_FALLBACK=1 — desativa gravação/leitura direta no PostgreSQL
  quando a API falha (útil se a API estiver noutra máquina). Com fallback ativo (default),
  após PUT/POST bem-sucedido na API replica também para o Postgres do config.py; no GET,
  funde fases vazias da API com o que existir na base local (evita «gravou mas sumiu»).
"""
import os
import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _documentacao_local_fallback_desligado() -> bool:
    return os.environ.get("DOCUMENTACAO_FASE_NO_LOCAL_FALLBACK", "").strip().lower() in ("1", "true", "yes")


def _detail_http(resp) -> str:
    try:
        d = resp.json().get("detail", "")
        if isinstance(d, list):
            return str(d)
        return str(d) if d else str(resp.reason or resp.status_code)
    except Exception:
        return str(resp.reason or resp.status_code)


def _salvar_documentacao_via_db(id_requisito: int, fase_codigo: str, conteudo: str) -> tuple[dict | None, str | None]:
    try:
        from db.doc_fase_repo import salvar_documentacao_fase as _salvar

        return _salvar(int(id_requisito), str(fase_codigo), conteudo or ""), None
    except ValueError as e:
        return None, f"Erro ao gravar: {e}"
    except Exception as e:
        return None, f"Erro ao gravar na base PostgreSQL: {e}"


def _obter_documentacao_via_db(id_requisito: int) -> tuple[dict | None, str | None]:
    try:
        from db.doc_fase_repo import obter_documentacao_fases as _obter

        return _obter(int(id_requisito)), None
    except Exception as e:
        return None, f"Erro ao ler documentação na base PostgreSQL: {e}"


def _merge_doc_fases_api_com_db_local(api_data: dict | None, id_requisito: int) -> dict:
    """
    Se a API devolver 200 com textos vazios mas o requisito_doc_fase local tiver conteúdo
    (ex.: gravação anterior só via fallback), usa o local para essas chaves.
    """
    from db.doc_fase_repo import FASES_DOC_VALIDAS

    base: dict = {k: "" for k in FASES_DOC_VALIDAS}
    if isinstance(api_data, dict):
        for k in FASES_DOC_VALIDAS:
            v = api_data.get(k)
            if v is None:
                base[k] = ""
            elif isinstance(v, str):
                base[k] = v
            else:
                base[k] = str(v)
    if _documentacao_local_fallback_desligado():
        return base
    dbd, err = _obter_documentacao_via_db(id_requisito)
    if err is not None or not isinstance(dbd, dict):
        return base
    for k in FASES_DOC_VALIDAS:
        api_v = str(base.get(k) or "").strip()
        db_v = str(dbd.get(k) or "").strip()
        if db_v and not api_v:
            base[k] = dbd[k]
    return base


def salvar_avaliacao(payload: dict) -> tuple[dict | None, str | None]:
    """
    Envia a avaliação para ser salva no banco.
    Retorna (resultado, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    url = f"{API_BASE_URL}/api/v1/requisitos/salvar-avaliacao"
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao salvar: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def analisar_requisito(payload: dict) -> tuple[dict | None, str | None]:
    """
    Envia a demanda para estruturação com IA (POST /api/v1/requisitos/analise).
    Retorna (dados, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    url = f"{API_BASE_URL}/api/v1/requisitos/analise"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.Timeout:
        return None, "Tempo limite excedido. A estruturação com IA está demorando muito."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        detail_str = str(detail).lower()
        if resp.status_code == 429 or "quota" in detail_str or "exceeded" in detail_str:
            return None, (
                "Cota da API Gemini (free tier) excedida. "
                "Tente novamente amanhã ou verifique seu plano em Google AI Studio."
            )
        return None, f"Erro da API: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def listar_atividades() -> tuple[list | None, str | None]:
    """
    Obtém a lista de atividades priorizadas.
    Retorna (lista, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    url = f"{API_BASE_URL}/api/v1/requisitos/atividades"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao listar atividades: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def obter_fila_duas() -> tuple[dict | None, str | None]:
    """
    Obtém duas filas por rotas separadas: bugs e incrementos/features.
    Retorna ({"bugs": [...], "features": [...]}, None) em sucesso.
    """
    try:
        r_bugs = requests.get(f"{API_BASE_URL}/api/v1/fila/bugs", timeout=15)
        r_bugs.raise_for_status()
        bugs = r_bugs.json()
        if not isinstance(bugs, list):
            return None, "Resposta inválida da API (/fila/bugs)."

        r_incs = requests.get(f"{API_BASE_URL}/api/v1/fila/incrementos", timeout=15)
        r_incs.raise_for_status()
        incrementos = r_incs.json()
        if not isinstance(incrementos, list):
            return None, "Resposta inválida da API (/fila/incrementos)."

        return {"bugs": bugs, "features": incrementos, "incrementos": incrementos}, None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = (
                (r_incs.json().get("detail") if "r_incs" in locals() else None)
                or (r_bugs.json().get("detail") if "r_bugs" in locals() else None)
                or str(e)
            )
        except Exception:
            detail = str(e)
        return None, f"Erro ao obter filas: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def get_config_fila() -> tuple[dict | None, str | None]:
    """
    Obtém a configuração da fila (calibragem).
    Retorna (config, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    url = f"{API_BASE_URL}/api/v1/config-fila"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao obter config: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def save_config_fila(config: dict) -> tuple[dict | None, str | None]:
    """
    Salva a configuração da fila (calibragem) no servidor.
    Retorna (resultado, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    url = f"{API_BASE_URL}/api/v1/config-fila"
    try:
        resp = requests.post(url, json=config, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao salvar config: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def criar_projeto_cadastro(payload: dict) -> tuple[dict | None, str | None]:
    """POST /api/v1/projetos — projeto novo (1.0.0) ou existente (versão informada)."""
    url = f"{API_BASE_URL}/api/v1/projetos"
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao cadastrar projeto: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def listar_projetos_cadastro(
    tipo_origem: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> tuple[list | None, str | None]:
    """GET /api/v1/projetos. Filtros opcionais: origem, status (ativo/arquivado/descontinuado), busca por nome (q)."""
    url = f"{API_BASE_URL}/api/v1/projetos"
    params = {}
    if tipo_origem:
        params["tipo_origem"] = tipo_origem
    if status:
        params["status"] = status
    if q:
        params["q"] = q
    try:
        resp = requests.get(url, params=params or None, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao listar projetos: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def atualizar_status_projeto_cadastro(id_projeto: int, status: str) -> tuple[dict | None, str | None]:
    """PATCH /api/v1/projetos/{id}/status — ativo, arquivado ou descontinuado."""
    url = f"{API_BASE_URL}/api/v1/projetos/{id_projeto}/status"
    try:
        resp = requests.patch(url, json={"status": status}, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao atualizar status do projeto: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def evoluir_versao_projeto_cadastro(
    id_projeto: int,
    nivel: str,
    motivo: str | None = None,
    usuario_responsavel: str | None = None,
) -> tuple[dict | None, str | None]:
    """POST evolução semântica da versão do projeto (opcional: motivo, usuário)."""
    url = f"{API_BASE_URL}/api/v1/projetos/{id_projeto}/evoluir-versao"
    body: dict = {"nivel": nivel}
    if motivo and str(motivo).strip():
        body["motivo"] = str(motivo).strip()
    if usuario_responsavel and str(usuario_responsavel).strip():
        body["usuario_responsavel"] = str(usuario_responsavel).strip()
    try:
        resp = requests.post(url, json=body, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao evoluir versão: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def listar_historico_versao_projeto_cadastro(
    id_projeto: int,
    limite: int = 100,
) -> tuple[list | None, str | None]:
    """GET histórico de versões de um projeto."""
    url = f"{API_BASE_URL}/api/v1/projetos/{id_projeto}/historico-versao"
    try:
        resp = requests.get(url, params={"limite": limite}, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro ao carregar histórico: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


# Resposta meta para GETs opcionais (visão 360, auditoria, gates): None = sucesso com corpo JSON;
# "HTTP_404" = rota não encontrada neste workspace; outras strings = erro de rede/HTTP.
EP_NOT_FOUND = "HTTP_404"


def _get_json_optional(path: str) -> tuple[object | None, str | None]:
    """
    GET que espera JSON. Não inventa contrato: só tenta o path indicado.
    404 → (None, EP_NOT_FOUND). Outros erros → (None, mensagem).
    """
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 404:
            return None, EP_NOT_FOUND
        resp.raise_for_status()
        try:
            return resp.json(), None
        except ValueError:
            return None, "Resposta não é JSON válido."
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erro HTTP: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def get_visao_360_demanda(demanda_id: int) -> tuple[object | None, str | None]:
    """GET /api/v1/demandas/{id}/visao-360 — quando existir no backend consolidado."""
    return _get_json_optional(f"/api/v1/demandas/{int(demanda_id)}/visao-360")


def get_auditoria_demanda(demanda_id: int) -> tuple[object | None, str | None]:
    """GET /api/v1/demandas/{id}/auditoria — quando existir no backend consolidado."""
    return _get_json_optional(f"/api/v1/demandas/{int(demanda_id)}/auditoria")


def get_kanban_gates_demanda(demanda_id: int) -> tuple[object | None, str | None]:
    """GET /api/v1/kanban/{id}/gates — quando existir no backend consolidado."""
    return _get_json_optional(f"/api/v1/kanban/{int(demanda_id)}/gates")


def obter_documentacao_fase_requisito(id_requisito: int) -> tuple[dict | None, str | None]:
    """GET documentação por fase Kanban (seis chaves)."""
    url = f"{API_BASE_URL}/api/v1/requisitos/{int(id_requisito)}/documentacao-fase"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return _merge_doc_fases_api_com_db_local(resp.json(), id_requisito), None
    except requests.exceptions.ConnectionError:
        if not _documentacao_local_fallback_desligado():
            data, err = _obter_documentacao_via_db(id_requisito)
            if err is None:
                return data, None
            return None, (
                f"Erro de conexão com a API ({API_BASE_URL}). Inicie com: python3 api.py. "
                f"Tentativa direta no PostgreSQL também falhou: {err}"
            )
        return None, f"Erro de conexão com a API ({API_BASE_URL}). Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError:
        detail = _detail_http(resp)
        # Qualquer 404: tenta PostgreSQL local (API antiga, proxy errado, ou rota não registada).
        if not _documentacao_local_fallback_desligado() and resp.status_code == 404:
            data, err = _obter_documentacao_via_db(id_requisito)
            if err is None:
                return data, None
            return None, (
                f"A API devolveu 404 ({detail}) em {url}. "
                f"Leitura direta na base falhou: {err}"
            )
        return None, f"Erro ao ler documentação ({resp.status_code}): {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def salvar_documentacao_fase_requisito(id_requisito: int, fase_codigo: str, conteudo: str) -> tuple[dict | None, str | None]:
    """Grava texto de uma fase (doc_requisito, prontidao_dev, …) via PUT ou POST."""
    url = f"{API_BASE_URL}/api/v1/requisitos/{int(id_requisito)}/documentacao-fase/{fase_codigo}"
    payload = {"conteudo": conteudo or ""}
    try:
        resp = requests.put(url, json=payload, timeout=15)
        if resp.status_code in (404, 405):
            resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        out = resp.json()
        # Replica no Postgres do config.py para o Dash e GETs subsequentes verem o mesmo estado
        # mesmo que a API aponte para outra instância ou devolva OK sem persistir como esperado.
        if not _documentacao_local_fallback_desligado():
            _salvar_documentacao_via_db(id_requisito, fase_codigo, conteudo)
        return out, None
    except requests.exceptions.ConnectionError:
        if not _documentacao_local_fallback_desligado():
            data, err = _salvar_documentacao_via_db(id_requisito, fase_codigo, conteudo)
            if err is None:
                return data, None
            return None, (
                f"Erro de conexão com a API ({API_BASE_URL}). Inicie com: python3 api.py. "
                f"Tentativa direta no PostgreSQL também falhou: {err}"
            )
        return None, f"Erro de conexão com a API ({API_BASE_URL}). Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError:
        detail = _detail_http(resp)
        # Qualquer 404: grava direto no PostgreSQL (mesma máquina / mesmo config.py que a API).
        if not _documentacao_local_fallback_desligado() and resp.status_code == 404:
            data, err = _salvar_documentacao_via_db(id_requisito, fase_codigo, conteudo)
            if err is None:
                return data, None
            return None, (
                f"A API devolveu 404 ({detail}) em {url}. "
                f"Gravação direta no PostgreSQL falhou: {err}"
            )
        if resp.status_code == 422 and "requisito" in detail.lower():
            return None, f"Erro ao gravar: {detail} (confirme o ID na lista de atividades e a base PostgreSQL.)"
        return None, f"Erro ao gravar ({resp.status_code}): {detail} — URL: {url}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def atualizar_status_requisito(id_requisito: int, status: str) -> tuple[dict | None, str | None]:
    """
    Atualiza o status_atual de uma atividade (BACKLOG, TO_DO, DEVELOP, TEST, DEPLOY, DONE).
    """
    url = f"{API_BASE_URL}/api/v1/requisitos/{id_requisito}/status"
    try:
        resp = requests.post(url, json={"status": status}, timeout=10)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão ao atualizar status. Verifique se a API está rodando (python3 api.py)."
    except requests.exceptions.HTTPError:
        detail = _detail_http(resp)
        return None, f"Erro ao atualizar status: {detail}"
    except Exception as e:
        return None, f"Erro inesperado ao atualizar status: {str(e)}"
