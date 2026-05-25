"""
Cliente para integração com a API de priorização.
"""
import requests

API_BASE_URL = "http://127.0.0.1:8000"


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
    Envia o requisito para análise pela IA.
    Retorna (dados, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    url = f"{API_BASE_URL}/api/v1/requisitos/analise"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Erro de conexão. Verifique se a API está rodando (python api.py)."
    except requests.exceptions.Timeout:
        return None, "Tempo limite excedido. A análise está demorando muito."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        detail_str = str(detail).lower()
        if resp.status_code == 429 or "quota" in detail_str or "exceeded" in detail_str:
            return None, (
                "Cota da API Gemini (free tier) excedida. "
                "O limite diário de análises foi atingido. Tente novamente amanhã ou verifique seu plano em Google AI Studio."
            )
        return None, f"Erro da API: {detail}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"


def listar_atividades() -> tuple[list | None, str | None]:
    """
    Obtém a lista de atividades priorizadas para os gráficos.
    Retorna (lista, None) em sucesso ou (None, mensagem_erro) em falha.
    Cada item tem: id, titulo, tipo_requisito, coordenada_x, coordenada_y, score, prioridade_categorica, status_atual.
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
