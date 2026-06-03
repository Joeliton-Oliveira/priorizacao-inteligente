# -*- coding: utf-8 -*-
"""
Estruturação da demanda com IA (Gemini): prompt, chamada ao modelo e normalização do JSON.
Sem dependência de FastAPI — erros são exceções de domínio.
"""
from __future__ import annotations

import json
import re

import google.generativeai as genai

from config import GEMINI_API_KEY
from domain.exceptions import AnaliseIaErro, EntradaInvalidaErro
from prompts import montar_prompt_analise

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


def extrair_json_ia(texto: str) -> dict | None:
    """Extrai JSON do texto retornado pela IA (pode vir com markdown)."""
    t = texto.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
    if match:
        t = match.group(1)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


def executar_analise_requisito(payload_para_prompt: dict) -> dict:
    """
    `payload_para_prompt` — mesmo formato esperado por `montar_prompt_analise`
    (texto_original, tipo_informado_usuario, módulos, etc.).

    Retorna dict compatível com `AnaliseRequisitoResponse.model_validate`.
    """
    texto = (payload_para_prompt.get("texto_original") or "").strip()
    if not texto:
        raise EntradaInvalidaErro("O texto da demanda não pode ser vazio.")

    try:
        prompt = montar_prompt_analise(payload_para_prompt)
        config = {"response_mime_type": "application/json"}
        response = model.generate_content(prompt, generation_config=config)
        data = extrair_json_ia(response.text or "")

        if not data:
            raise AnaliseIaErro(
                "A IA não retornou JSON válido. Resposta: " + (response.text or "")[:500]
            )

        titulo = data.get("titulo_requisito") or data.get("tituloRequisito", "")
        descricao = data.get("descricao_requisito") or data.get("descricaoRequisito", "")
        tipo = (data.get("tipo_requisito") or data.get("tipoRequisito", "INCREMENTO")).upper()
        objetivo = data.get("objetivo", "")
        finalidade = data.get("finalidade", "")
        raw_perguntas = data.get("perguntas_avaliacao") or data.get("perguntasAvaliacao", [])

        escala_likert_padrao = [
            {"rotulo": "Muito baixo", "valor": 1},
            {"rotulo": "Baixo", "valor": 2},
            {"rotulo": "Médio", "valor": 3},
            {"rotulo": "Alto", "valor": 4},
            {"rotulo": "Muito alto", "valor": 5},
        ]
        perguntas = []
        for p in raw_perguntas:
            raw_opcoes = p.get("opcoes_resposta") or p.get("opcoesResposta") or []
            if len(raw_opcoes) < 5:
                raw_opcoes = escala_likert_padrao
            opcoes = [
                {"rotulo": str(o.get("rotulo", "")), "valor": int(o.get("valor", 0))}
                for o in raw_opcoes[:5]
            ]
            perguntas.append(
                {
                    "id_pergunta": int(p.get("id_pergunta", 0)),
                    "texto": str(p.get("texto", "")),
                    "dimensao": str(p.get("dimensao", "")).upper(),
                    "opcoes_resposta": opcoes,
                }
            )

        return {
            "texto_original": texto,
            "titulo_requisito": titulo,
            "descricao_requisito": descricao,
            "tipo_requisito": tipo,
            "objetivo": objetivo,
            "finalidade": finalidade,
            "perguntas_avaliacao": perguntas,
        }
    except AnaliseIaErro:
        raise
    except Exception as e:
        raise AnaliseIaErro(f"Erro na IA: {str(e)}") from e


def montar_payload_de_requisicao_analise(req_like: dict) -> dict:
    """Converte corpo da API (dict / modelo .model_dump) para o payload do prompt."""
    texto = (req_like.get("texto_original") or req_like.get("texto") or "").strip()
    return {
        "texto_original": texto,
        "tipo_informado_usuario": req_like.get("tipo_informado_usuario") or "NAO_SEI",
        "modulo_afetado": req_like.get("modulo_afetado"),
        "contexto_negocio": req_like.get("contexto_negocio"),
        "objetivo_desejado": req_like.get("objetivo_desejado"),
        "impacto_percebido_usuario": req_like.get("impacto_percebido_usuario"),
        "frequencia_ocorrencia": req_like.get("frequencia_ocorrencia"),
        "urgencia_percebida": req_like.get("urgencia_percebida"),
        "ha_contorno": req_like.get("ha_contorno"),
        "sistema_ou_produto": req_like.get("sistema_ou_produto"),
        "perfil_solicitante": req_like.get("perfil_solicitante"),
    }
