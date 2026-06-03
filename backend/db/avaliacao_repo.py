"""
Repositório para persistir avaliações e respostas no banco.
"""
import json
from db.connection import get_connection

_SQL_CREATE_STATUS_REQUISITO = """
CREATE TABLE IF NOT EXISTS status_requisito (
    id_requisito INTEGER PRIMARY KEY REFERENCES requisito_estruturado(id_requisito),
    status_atual VARCHAR(50) NOT NULL
)
"""


def _ensure_status_requisito(cur) -> None:
    cur.execute(_SQL_CREATE_STATUS_REQUISITO)


def _extrair_id_projeto_do_cadastro(cadastro: dict | None) -> int | None:
    if not cadastro:
        return None
    raw = cadastro.get("id_projeto")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def _validar_projeto_obrigatorio(cadastro: dict | None, cur) -> int:
    """Exige cadastro.id_projeto e projeto existente com versao_atual preenchida."""
    id_projeto = _extrair_id_projeto_do_cadastro(cadastro)
    if id_projeto is None:
        raise ValueError(
            "Toda demanda deve estar vinculada a um projeto. Informe cadastro.id_projeto ao salvar."
        )
    cur.execute(
        "SELECT versao_atual FROM projeto WHERE id_projeto = %s",
        (id_projeto,),
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError("Projeto não encontrado.")
    va = (row[0] or "").strip() if row[0] is not None else ""
    if not va:
        raise ValueError("O projeto indicado não possui versão cadastrada (versao_atual).")
    return id_projeto


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
            id_projeto = _validar_projeto_obrigatorio(cadastro, cur)
            # 1. Entrada bruta
            cur.execute(
                """
                INSERT INTO entrada_bruta (
                    texto_original, usuario_criacao, perfil_solicitante,
                    modulo_afetado, contexto_negocio, objetivo_desejado, dados_cadastro_json, id_projeto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
                    id_projeto,
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

            # Novo requisito sempre nasce na coluna BACKLOG da esteira.
            _ensure_status_requisito(cur)
            cur.execute(
                """
                INSERT INTO status_requisito (id_requisito, status_atual)
                VALUES (%s, 'BACKLOG')
                ON CONFLICT (id_requisito) DO UPDATE SET status_atual = EXCLUDED.status_atual
                """,
                (id_requisito,),
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
    itens = listar_atividades_para_fila()
    for item in itens:
        item.pop("data_avaliacao", None)
    return itens


def listar_atividades_para_fila():
    """
    Lista atividades com coordenadas e data_avaliacao para a fila (envelhecimento).
    Mesma estrutura que listar_atividades_priorizadas + data_avaliacao.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_status_requisito(cur)
            conn.commit()
            cur.execute(
                """
                SELECT
                    r.id_requisito,
                    r.titulo,
                    r.tipo_tarefa,
                    ra.data_avaliacao,
                    res.dimensao,
                    res.valor_numerico,
                    sr.status_atual,
                    eb.id_projeto,
                    p.nome_projeto,
                    p.versao_atual
                FROM requisito_estruturado r
                JOIN entrada_bruta eb ON r.id_entrada_bruta = eb.id_entrada_bruta
                JOIN avaliacao_requisito ra ON ra.id_requisito = r.id_requisito
                JOIN resposta_avaliacao res ON res.id_avaliacao = ra.id_avaliacao
                LEFT JOIN status_requisito sr ON sr.id_requisito = r.id_requisito
                LEFT JOIN projeto p ON eb.id_projeto = p.id_projeto
                ORDER BY r.id_requisito, res.dimensao
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    from collections import defaultdict
    by_req = defaultdict(lambda: {"dims": defaultdict(list), "data_avaliacao": None})
    for (
        id_requisito,
        titulo,
        tipo_tarefa,
        data_avaliacao,
        dimensao,
        valor,
        status_atual,
        id_projeto,
        nome_projeto,
        versao_atual_proj,
    ) in rows:
        key = (id_requisito, titulo, (tipo_tarefa or "INCREMENTO").upper())
        if dimensao:
            by_req[key]["dims"][dimensao.upper().strip()].append(valor)
        if by_req[key]["data_avaliacao"] is None and data_avaliacao:
            by_req[key]["data_avaliacao"] = data_avaliacao
        if "status_atual" not in by_req[key] and status_atual:
            by_req[key]["status_atual"] = status_atual
        if "id_projeto" not in by_req[key]:
            by_req[key]["id_projeto"] = id_projeto
            by_req[key]["nome_projeto"] = nome_projeto
            by_req[key]["versao_projeto"] = versao_atual_proj

    out = []
    for (id_requisito, titulo, tipo_tarefa), data in by_req.items():
        dims = data["dims"]
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

        status_atual = (data.get("status_atual") or "BACKLOG").upper()
        row = {
            "id": id_requisito,
            "titulo": titulo or "",
            "tipo_requisito": tipo_tarefa,
            "coordenada_x": coordenada_x,
            "coordenada_y": coordenada_y,
            "score": score,
            "prioridade_categorica": prioridade_categorica,
            "status_atual": status_atual,
            "data_avaliacao": data.get("data_avaliacao"),
        }
        if data.get("id_projeto") is not None:
            row["id_projeto"] = data["id_projeto"]
        if data.get("nome_projeto"):
            row["nome_projeto"] = data["nome_projeto"]
        if data.get("versao_projeto"):
            row["versao_projeto"] = data["versao_projeto"]
        out.append(row)
    return out


def obter_status_atual_requisito(id_requisito: int) -> str | None:
    """Devolve status_atual em status_requisito ou None se não existir linha."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_status_requisito(cur)
            conn.commit()
            cur.execute(
                "SELECT status_atual FROM status_requisito WHERE id_requisito = %s",
                (id_requisito,),
            )
            row = cur.fetchone()
        return row[0] if row and row[0] is not None else None
    finally:
        conn.close()


def obter_tipo_requisito(id_requisito: int) -> str | None:
    """Devolve tipo_tarefa em requisito_estruturado ou None se não existir linha."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tipo_tarefa FROM requisito_estruturado WHERE id_requisito = %s",
                (id_requisito,),
            )
            row = cur.fetchone()
        if not row or row[0] is None:
            return None
        return str(row[0]).strip().upper() or None
    finally:
        conn.close()


def listar_status_requisito_por_coluna(coluna_kanban: str, excluir_id_requisito: int | None = None) -> int:
    """Conta requisitos na coluna Kanban indicada (mapeamento alinhado a kanban_gates)."""
    from services.kanban_gates import status_api_para_coluna_kanban

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_status_requisito(cur)
            cur.execute("SELECT id_requisito, status_atual FROM status_requisito")
            rows = cur.fetchall()
    finally:
        conn.close()

    count = 0
    for rid, st in rows:
        if excluir_id_requisito is not None and rid == excluir_id_requisito:
            continue
        if status_api_para_coluna_kanban(st) == coluna_kanban:
            count += 1
    return count


def atualizar_status_requisito(id_requisito: int, status: str) -> None:
    """Atualiza o status_atual do requisito na tabela status_requisito."""
    from services.kanban_gates import normalizar_status_api

    status_normalizado = normalizar_status_api(status)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_status_requisito(cur)
            cur.execute(
                """
                INSERT INTO status_requisito (id_requisito, status_atual)
                VALUES (%s, %s)
                ON CONFLICT (id_requisito) DO UPDATE SET status_atual = EXCLUDED.status_atual
                """,
                (id_requisito, status_normalizado),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
