# -*- coding: utf-8 -*-
"""Consultas consolidadas para detalhe, visão 360 e auditoria de demandas."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from db.connection import get_connection
from db.doc_fase_repo import obter_documentacao_fases
from domain.exceptions import RecursoNaoEncontradoError
from services.kanban_status_service import obter_gates_kanban


def _parse_json(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        texto = raw.strip()
        if not texto:
            return {}
        try:
            parsed = json.loads(texto)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _priority_label(score: float) -> str:
    if score >= 15:
        return "ALTA"
    if score >= 8:
        return "MEDIA"
    return "BAIXA"


def _metricas_avaliacao(tipo_requisito: str, respostas: list[dict[str, Any]]) -> dict[str, Any]:
    by_dim: dict[str, list[float]] = {}
    for resposta in respostas:
        dim = str(resposta.get("dimensao") or "").strip().upper()
        if not dim:
            continue
        try:
            valor = float(resposta.get("valor_resposta") or 0)
        except (TypeError, ValueError):
            valor = 0.0
        by_dim.setdefault(dim, []).append(valor)

    def media(dim: str) -> float:
        valores = by_dim.get(dim, [])
        if not valores:
            return 0.0
        return round(sum(valores) / len(valores), 2)

    tipo = (tipo_requisito or "INCREMENTO").strip().upper()
    if tipo == "BUG":
        coordenada_x = media("CRITICIDADE")
        coordenada_y = media("SEVERIDADE")
        eixos = "Criticidade x Severidade"
    else:
        coordenada_x = media("ESFORCO")
        coordenada_y = media("VALOR")
        eixos = "Esforço x Valor"

    score = round(coordenada_x * coordenada_y, 2)
    return {
        "coordenada_x": coordenada_x,
        "coordenada_y": coordenada_y,
        "score": score,
        "prioridade_categorica": _priority_label(score),
        "eixos": eixos,
    }


def _carregar_respostas(cur, id_avaliacao: int | None) -> list[dict[str, Any]]:
    if id_avaliacao is None:
        return []
    cur.execute(
        """
        SELECT id_pergunta, texto_pergunta, dimensao, valor_numerico
        FROM resposta_avaliacao
        WHERE id_avaliacao = %s
        ORDER BY id_pergunta, id_resposta
        """,
        (id_avaliacao,),
    )
    rows = cur.fetchall()
    return [
        {
            "id_pergunta": row[0],
            "texto": row[1] or "",
            "dimensao": row[2] or "",
            "valor_resposta": row[3],
        }
        for row in rows
    ]


def obter_visao_360(id_requisito: int) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id_requisito,
                    r.titulo,
                    r.descricao_refinada,
                    r.tipo_tarefa,
                    r.objetivo,
                    r.finalidade,
                    r.data_criacao,
                    eb.id_entrada_bruta,
                    eb.texto_original,
                    eb.usuario_criacao,
                    eb.perfil_solicitante,
                    eb.modulo_afetado,
                    eb.contexto_negocio,
                    eb.objetivo_desejado,
                    eb.dados_cadastro_json::text,
                    eb.data_criacao,
                    p.id_projeto,
                    p.nome_projeto,
                    p.versao_atual,
                    p.status_projeto,
                    ar.id_avaliacao,
                    ar.usuario_avaliador,
                    ar.perfil_avaliador,
                    ar.data_avaliacao,
                    sr.status_atual
                FROM requisito_estruturado r
                JOIN entrada_bruta eb ON eb.id_entrada_bruta = r.id_entrada_bruta
                LEFT JOIN projeto p ON p.id_projeto = eb.id_projeto
                LEFT JOIN LATERAL (
                    SELECT id_avaliacao, usuario_avaliador, perfil_avaliador, data_avaliacao
                    FROM avaliacao_requisito
                    WHERE id_requisito = r.id_requisito
                    ORDER BY data_avaliacao DESC, id_avaliacao DESC
                    LIMIT 1
                ) ar ON true
                LEFT JOIN status_requisito sr ON sr.id_requisito = r.id_requisito
                WHERE r.id_requisito = %s
                """,
                (id_requisito,),
            )
            row = cur.fetchone()
            if row is None:
                raise RecursoNaoEncontradoError("Demanda não encontrada")

            cadastro = _parse_json(row[14])
            respostas = _carregar_respostas(cur, row[20])
            metricas = _metricas_avaliacao(row[3] or "INCREMENTO", respostas)
            documentacao = obter_documentacao_fases(id_requisito)
            gates = obter_gates_kanban(id_requisito)

            return {
                "identificacao": {
                    "id_requisito": row[0],
                    "id_entrada_bruta": row[7],
                    "titulo": row[1],
                    "descricao_requisito": row[2],
                    "tipo_requisito": row[3],
                    "status_atual": row[24] or "BACKLOG",
                    "data_criacao_requisito": _iso(row[6]),
                    "projeto": {
                        "id_projeto": row[16],
                        "nome_projeto": row[17],
                        "versao_atual": row[18],
                        "status_projeto": row[19],
                    },
                },
                "origem_demanda": {
                    "texto_original": row[8],
                    "usuario_criacao": row[9],
                    "perfil_solicitante": cadastro.get("perfil_solicitante") or row[10],
                    "modulo_afetado": cadastro.get("modulo_afetado") or row[11],
                    "contexto_negocio": cadastro.get("contexto_negocio") or row[12],
                    "objetivo_desejado": cadastro.get("objetivo_desejado") or row[13],
                    "ha_contorno": cadastro.get("ha_contorno"),
                    "sistema_ou_produto": cadastro.get("sistema_ou_produto"),
                    "impacto_percebido_usuario": cadastro.get("impacto_percebido_usuario"),
                    "frequencia_ocorrencia": cadastro.get("frequencia_ocorrencia"),
                    "urgencia_percebida": cadastro.get("urgencia_percebida"),
                    "data_criacao_entrada": _iso(row[15]),
                },
                "estruturacao_ia": {
                    "titulo_requisito": row[1],
                    "descricao_requisito": row[2],
                    "tipo_requisito": row[3],
                    "objetivo": row[4],
                    "finalidade": row[5],
                },
                "avaliacao": {
                    "id_avaliacao": row[20],
                    "usuario_avaliador": row[21],
                    "perfil_avaliador": row[22],
                    "data_avaliacao": _iso(row[23]),
                    **metricas,
                },
                "respostas": respostas,
                "documentacao_fase": documentacao,
                "gates": gates,
            }
    finally:
        conn.close()


def obter_auditoria(id_requisito: int) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id_requisito,
                    r.titulo,
                    r.tipo_tarefa,
                    r.data_criacao,
                    eb.data_criacao,
                    eb.usuario_criacao,
                    ar.id_avaliacao,
                    ar.data_avaliacao,
                    ar.usuario_avaliador,
                    eb.id_projeto
                FROM requisito_estruturado r
                JOIN entrada_bruta eb ON eb.id_entrada_bruta = r.id_entrada_bruta
                LEFT JOIN LATERAL (
                    SELECT id_avaliacao, data_avaliacao, usuario_avaliador
                    FROM avaliacao_requisito
                    WHERE id_requisito = r.id_requisito
                    ORDER BY data_avaliacao DESC, id_avaliacao DESC
                    LIMIT 1
                ) ar ON true
                WHERE r.id_requisito = %s
                """,
                (id_requisito,),
            )
            row = cur.fetchone()
            if row is None:
                raise RecursoNaoEncontradoError("Demanda não encontrada")

            eventos: list[dict[str, Any]] = [
                {
                    "tipo": "entrada_bruta",
                    "titulo": "Demanda cadastrada",
                    "descricao": "Texto original e metadados da demanda foram gravados.",
                    "quando": _iso(row[4]),
                    "responsavel": row[5],
                },
                {
                    "tipo": "requisito_estruturado",
                    "titulo": "Requisito estruturado",
                    "descricao": "A demanda foi consolidada como requisito estruturado.",
                    "quando": _iso(row[3]),
                    "responsavel": None,
                },
            ]

            if row[6] is not None:
                eventos.append(
                    {
                        "tipo": "avaliacao",
                        "titulo": "Avaliação registrada",
                        "descricao": "As respostas Likert foram persistidas no banco.",
                        "quando": _iso(row[7]),
                        "responsavel": row[8],
                    }
                )

            cur.execute(
                """
                SELECT fase_codigo, atualizado_em
                FROM requisito_doc_fase
                WHERE id_requisito = %s
                ORDER BY atualizado_em DESC, fase_codigo
                """,
                (id_requisito,),
            )
            for fase_codigo, atualizado_em in cur.fetchall():
                eventos.append(
                    {
                        "tipo": "documentacao_fase",
                        "titulo": f"Documentação atualizada ({fase_codigo})",
                        "descricao": "Uma fase documental da atividade foi atualizada.",
                        "quando": _iso(atualizado_em),
                        "responsavel": None,
                    }
                )

            if row[9] is not None:
                cur.execute(
                    """
                    SELECT versao_anterior, versao_nova, nivel_evolucao, motivo, usuario_responsavel, criado_em
                    FROM projeto_versao_historico
                    WHERE id_projeto = %s
                    ORDER BY criado_em DESC, id_historico DESC
                    LIMIT 50
                    """,
                    (row[9],),
                )
                for versao_anterior, versao_nova, nivel, motivo, usuario_responsavel, criado_em in cur.fetchall():
                    eventos.append(
                        {
                            "tipo": "versao_projeto",
                            "titulo": f"Projeto evoluído ({nivel})",
                            "descricao": f"{versao_anterior} → {versao_nova}" + (f" · {motivo}" if motivo else ""),
                            "quando": _iso(criado_em),
                            "responsavel": usuario_responsavel,
                        }
                    )

            def _ordem(evento: dict[str, Any]) -> tuple[int, str]:
                when = evento.get("quando") or ""
                return (0 if when else 1, str(when))

            eventos.sort(key=_ordem, reverse=True)

            return {
                "id_requisito": row[0],
                "titulo": row[1],
                "tipo_requisito": row[2],
                "eventos": eventos,
            }
    finally:
        conn.close()
