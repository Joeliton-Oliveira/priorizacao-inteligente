"""
Repositório para persistir avaliações e respostas no banco.
"""
import json
from db.connection import get_connection


def salvar_avaliacao_completa(
    texto_original: str,
    titulo_requisito: str,
    descricao_requisito: str,
    tipo_requisito: str,
    objetivo: str,
    finalidade: str,
    usuario_avaliador: str,
    perfil_avaliador: str | None,
    respostas: list[dict],
    cadastro: dict | None = None,
) -> dict:
    """
    Salva entrada bruta, requisito estruturado, avaliação e respostas.
    Retorna dict com ids criados ou erro.
    """
    cadastro = cadastro or {}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Entrada bruta
            cur.execute(
                """
                INSERT INTO entrada_bruta (
                    texto_original, usuario_criacao, perfil_solicitante,
                    modulo_afetado, contexto_negocio, objetivo_desejado, dados_cadastro_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_entrada_bruta
                """,
                (
                    texto_original,
                    usuario_avaliador,
                    perfil_avaliador or cadastro.get("perfil_solicitante"),
                    cadastro.get("modulo_afetado"),
                    cadastro.get("contexto_negocio"),
                    cadastro.get("objetivo_desejado"),
                    json.dumps(cadastro) if cadastro else None,
                ),
            )
            id_entrada = cur.fetchone()[0]

            # 2. Requisito estruturado
            cur.execute(
                """
                INSERT INTO requisito_estruturado (
                    id_entrada_bruta, titulo, descricao_refinada, tipo_tarefa, objetivo, finalidade
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_requisito
                """,
                (
                    id_entrada,
                    titulo_requisito,
                    descricao_requisito,
                    tipo_requisito,
                    objetivo,
                    finalidade,
                ),
            )
            id_requisito = cur.fetchone()[0]

            # 3. Avaliação
            cur.execute(
                """
                INSERT INTO avaliacao_requisito (id_requisito, usuario_avaliador, perfil_avaliador)
                VALUES (%s, %s, %s)
                RETURNING id_avaliacao
                """,
                (id_requisito, usuario_avaliador, perfil_avaliador or cadastro.get("perfil_solicitante")),
            )
            id_avaliacao = cur.fetchone()[0]

            # 4. Respostas
            for r in respostas:
                cur.execute(
                    """
                    INSERT INTO resposta_avaliacao (id_avaliacao, id_pergunta, texto_pergunta, dimensao, valor_numerico)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        id_avaliacao,
                        r.get("id_pergunta", 0),
                        r.get("texto", "")[:1000],
                        r.get("dimensao", ""),
                        r.get("valor_resposta", 0),
                    ),
                )

            conn.commit()
            return {
                "sucesso": True,
                "id_entrada_bruta": id_entrada,
                "id_requisito": id_requisito,
                "id_avaliacao": id_avaliacao,
            }
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_atividades_priorizadas():
    """
    Lista todas as atividades já avaliadas com coordenadas para os gráficos.
    Para BUG: coordenada_x = Criticidade, coordenada_y = Severidade.
    Para INCREMENTO: coordenada_x = Esforço, coordenada_y = Valor.
    score = coordenada_x * coordenada_y. prioridade_categorica e status_atual derivados.
    Retorna lista de dict com id, titulo, tipo_requisito, coordenada_x, coordenada_y, score, prioridade_categorica, status_atual.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id_requisito,
                    r.titulo,
                    r.tipo_tarefa,
                    ra.id_avaliacao,
                    res.dimensao,
                    res.valor_numerico
                FROM requisito_estruturado r
                JOIN avaliacao_requisito ra ON ra.id_requisito = r.id_requisito
                JOIN resposta_avaliacao res ON res.id_avaliacao = ra.id_avaliacao
                ORDER BY r.id_requisito, res.dimensao
                """
            )
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        conn.close()
        raise

    # Agrupar por requisito e por dimensão (média se houver mais de uma resposta por dimensão)
    from collections import defaultdict
    by_req = defaultdict(lambda: defaultdict(list))
    for id_requisito, titulo, tipo_tarefa, id_avaliacao, dimensao, valor in rows:
        key = (id_requisito, titulo, (tipo_tarefa or "INCREMENTO").upper())
        if dimensao:
            by_req[key][dimensao.upper().strip()].append(valor)

    out = []
    for (id_requisito, titulo, tipo_tarefa), dims in by_req.items():
        def media(dimensao):
            v = dims.get(dimensao, [])
            return sum(v) / len(v) if v else 0.0

        if tipo_tarefa == "BUG":
            coordenada_x = media("CRITICIDADE")
            coordenada_y = media("SEVERIDADE")
        else:
            coordenada_x = media("ESFORCO")
            coordenada_y = media("VALOR")

        score = round(coordenada_x * coordenada_y, 2)
        coordenada_x = round(coordenada_x, 2)
        coordenada_y = round(coordenada_y, 2)

        if score >= 15:
            prioridade_categorica = "ALTA"
        elif score >= 8:
            prioridade_categorica = "MEDIA"
        else:
            prioridade_categorica = "BAIXA"

        out.append({
            "id": id_requisito,
            "titulo": titulo or "",
            "tipo_requisito": tipo_tarefa,
            "coordenada_x": coordenada_x,
            "coordenada_y": coordenada_y,
            "score": score,
            "prioridade_categorica": prioridade_categorica,
            "status_atual": "AVALIADO",
        })
    return out
