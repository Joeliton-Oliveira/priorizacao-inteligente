"""
Persistência de projetos (cadastro novo vs existente, evolução de versão e histórico).
"""
from datetime import datetime
from typing import Any

from db.connection import get_connection
from version import parse_semver, proxima_versao_semver

VERSAO_INICIAL_NOVO = "1.0.0"
STATUS_PROJETO_VALIDOS = frozenset({"ativo", "arquivado", "descontinuado"})


def _nome_projeto_duplicado(cur, nome: str) -> bool:
    cur.execute(
        "SELECT 1 FROM projeto WHERE lower(trim(nome_projeto)) = lower(trim(%s)) LIMIT 1",
        (nome,),
    )
    return cur.fetchone() is not None


def criar_projeto(
    nome_projeto: str,
    tipo_origem: str,
    descricao: str | None = None,
    responsavel: str | None = None,
    versao_atual_informada: str | None = None,
    status_projeto: str | None = None,
) -> dict[str, Any]:
    """
    ``tipo_origem``: ``novo`` (fixa 1.0.0) ou ``existente`` (usa ``versao_atual_informada``).
    Não permite dois projetos com o mesmo nome (comparação case-insensitive após trim).
    """
    nome_projeto = (nome_projeto or "").strip()
    if not nome_projeto:
        raise ValueError("nome_projeto é obrigatório")

    origem = (tipo_origem or "").strip().lower()
    if origem not in ("novo", "existente"):
        raise ValueError("tipo_origem deve ser 'novo' ou 'existente'")

    st = (status_projeto or "ativo").strip().lower()
    if st not in STATUS_PROJETO_VALIDOS:
        raise ValueError("status_projeto deve ser ativo, arquivado ou descontinuado.")

    if origem == "novo":
        vi = va = VERSAO_INICIAL_NOVO
    else:
        v = (versao_atual_informada or "").strip()
        if not v:
            raise ValueError("Para projeto existente, informe versao_atual (ex.: 3.11.52).")
        parse_semver(v)
        vi = va = v

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if _nome_projeto_duplicado(cur, nome_projeto):
                raise ValueError(
                    "Já existe um projeto com esse nome. Use outro nome ou edite o cadastro existente."
                )
            cur.execute(
                """
                INSERT INTO projeto (
                    nome_projeto, descricao, responsavel, tipo_origem,
                    versao_inicial, versao_atual, status_projeto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_projeto, data_cadastro, data_ultima_atualizacao
                """,
                (nome_projeto, descricao or None, responsavel or None, origem, vi, va, st),
            )
            row = cur.fetchone()
            conn.commit()
            id_projeto, dc, dua = row
            return {
                "id_projeto": id_projeto,
                "nome_projeto": nome_projeto,
                "descricao": descricao,
                "responsavel": responsavel,
                "tipo_origem": origem,
                "versao_inicial": vi,
                "versao_atual": va,
                "status_projeto": st,
                "data_cadastro": dc.isoformat() if hasattr(dc, "isoformat") else str(dc),
                "data_ultima_atualizacao": dua.isoformat() if hasattr(dua, "isoformat") else str(dua),
            }
    finally:
        conn.close()


def listar_projetos(
    tipo_origem: str | None = None,
    status_projeto: str | None = None,
    busca_nome: str | None = None,
) -> list[dict[str, Any]]:
    """
    Filtros opcionais: ``tipo_origem`` (novo/existente), ``status_projeto``, ``busca_nome`` (ILIKE).
    Inclui dados da última evolução de versão (se houver histórico).
    """
    filtro_tipo = (tipo_origem or "").strip().lower()
    if filtro_tipo and filtro_tipo not in ("novo", "existente"):
        raise ValueError("tipo_origem inválido para listagem.")
    filtro_status = (status_projeto or "").strip().lower()
    if filtro_status and filtro_status not in STATUS_PROJETO_VALIDOS:
        raise ValueError("status_projeto inválido para listagem.")
    termo = (busca_nome or "").strip()
    if len(termo) > 200:
        termo = termo[:200]

    conditions: list[str] = []
    params: list[Any] = []
    if filtro_tipo:
        conditions.append("p.tipo_origem = %s")
        params.append(filtro_tipo)
    if filtro_status:
        conditions.append("p.status_projeto = %s")
        params.append(filtro_status)
    if termo:
        conditions.append("p.nome_projeto ILIKE %s")
        params.append(f"%{termo}%")
    where_sql = " AND ".join(conditions) if conditions else "TRUE"

    sql = f"""
        SELECT p.id_projeto, p.nome_projeto, p.descricao, p.responsavel, p.tipo_origem,
               p.versao_inicial, p.versao_atual, p.data_cadastro, p.data_ultima_atualizacao,
               p.status_projeto,
               ult.criado_em, ult.usuario_responsavel, ult.nivel_evolucao, ult.versao_nova
        FROM projeto p
        LEFT JOIN LATERAL (
            SELECT h.criado_em, h.usuario_responsavel, h.nivel_evolucao, h.versao_nova
            FROM projeto_versao_historico h
            WHERE h.id_projeto = p.id_projeto
            ORDER BY h.criado_em DESC, h.id_historico DESC
            LIMIT 1
        ) ult ON true
        WHERE {where_sql}
        ORDER BY p.data_cadastro DESC, p.id_projeto DESC
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            out = []
            for r in rows:
                dc, dua = r[7], r[8]
                ue, upor, univel, uver = r[10], r[11], r[12], r[13]
                out.append({
                    "id_projeto": r[0],
                    "nome_projeto": r[1],
                    "descricao": r[2],
                    "responsavel": r[3],
                    "tipo_origem": r[4],
                    "versao_inicial": r[5],
                    "versao_atual": r[6],
                    "data_cadastro": dc.isoformat() if hasattr(dc, "isoformat") else str(dc),
                    "data_ultima_atualizacao": dua.isoformat() if hasattr(dua, "isoformat") else str(dua),
                    "status_projeto": r[9],
                    "ultima_evolucao_em": ue.isoformat() if ue and hasattr(ue, "isoformat") else (str(ue) if ue else None),
                    "ultima_evolucao_por": upor,
                    "ultima_evolucao_nivel": univel,
                    "ultima_evolucao_versao": uver,
                })
            return out
    finally:
        conn.close()


def atualizar_status_projeto(id_projeto: int, status_projeto: str) -> dict[str, Any]:
    """Altera apenas o status (ativo / arquivado / descontinuado)."""
    st = (status_projeto or "").strip().lower()
    if st not in STATUS_PROJETO_VALIDOS:
        raise ValueError("status_projeto deve ser ativo, arquivado ou descontinuado.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE projeto
                SET status_projeto = %s
                WHERE id_projeto = %s
                RETURNING id_projeto, nome_projeto, status_projeto
                """,
                (st, id_projeto),
            )
            row = cur.fetchone()
            if not row:
                raise LookupError("Projeto não encontrado")
            conn.commit()
            return {
                "id_projeto": row[0],
                "nome_projeto": row[1],
                "status_projeto": row[2],
            }
    finally:
        conn.close()


def evoluir_versao_projeto(
    id_projeto: int,
    nivel: str,
    motivo: str | None = None,
    usuario_responsavel: str | None = None,
) -> dict[str, Any]:
    """Sobe ``versao_atual``, grava linha em ``projeto_versao_historico`` e atualiza ``data_ultima_atualizacao``."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT versao_atual FROM projeto WHERE id_projeto = %s",
                (id_projeto,),
            )
            row = cur.fetchone()
            if not row:
                raise LookupError("Projeto não encontrado")
            atual = row[0]
            nova = proxima_versao_semver(atual, nivel)
            now = datetime.utcnow()
            cur.execute(
                """
                INSERT INTO projeto_versao_historico (
                    id_projeto, versao_anterior, versao_nova, nivel_evolucao, motivo, usuario_responsavel, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_projeto,
                    atual,
                    nova,
                    nivel.strip().lower(),
                    (motivo or "").strip() or None,
                    (usuario_responsavel or "").strip() or None,
                    now,
                ),
            )
            cur.execute(
                """
                UPDATE projeto
                SET versao_atual = %s, data_ultima_atualizacao = %s
                WHERE id_projeto = %s
                RETURNING nome_projeto, versao_inicial, versao_atual, data_ultima_atualizacao, status_projeto
                """,
                (nova, now, id_projeto),
            )
            r2 = cur.fetchone()
            conn.commit()
            dua = r2[3]
            return {
                "id_projeto": id_projeto,
                "nome_projeto": r2[0],
                "versao_inicial": r2[1],
                "versao_atual": r2[2],
                "status_projeto": r2[4],
                "data_ultima_atualizacao": dua.isoformat() if hasattr(dua, "isoformat") else str(dua),
            }
    finally:
        conn.close()


def listar_historico_versao_projeto(id_projeto: int, limite: int = 100) -> list[dict[str, Any]]:
    """Últimas evoluções de versão do projeto (mais recente primeiro)."""
    limite = max(1, min(int(limite), 500))
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_historico, id_projeto, versao_anterior, versao_nova, nivel_evolucao,
                       motivo, usuario_responsavel, criado_em
                FROM projeto_versao_historico
                WHERE id_projeto = %s
                ORDER BY criado_em DESC, id_historico DESC
                LIMIT %s
                """,
                (id_projeto, limite),
            )
            rows = cur.fetchall()
            out = []
            for r in rows:
                ce = r[7]
                out.append({
                    "id_historico": r[0],
                    "id_projeto": r[1],
                    "versao_anterior": r[2],
                    "versao_nova": r[3],
                    "nivel_evolucao": r[4],
                    "motivo": r[5],
                    "usuario_responsavel": r[6],
                    "criado_em": ce.isoformat() if hasattr(ce, "isoformat") else str(ce),
                })
            return out
    finally:
        conn.close()
