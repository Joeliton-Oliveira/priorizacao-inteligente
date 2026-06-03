"""
Documentação por fase Kanban (evidências para avançar coluna).
Uma linha por (id_requisito, fase_codigo).
"""
from __future__ import annotations

import json
from typing import Any

from db.connection import get_connection


def _valor_campo_doc_para_lista(val: Any) -> list[str]:
    """Aceita str (legado) ou list no JSON; devolve lista de strings (itens vazios preservados se vierem da lista)."""
    if val is None:
        return []
    if isinstance(val, list):
        return ["" if x is None else str(x) for x in val]
    s = str(val).strip()
    if not s:
        return []
    linhas = [ln.strip() for ln in s.split("\n")]
    nao_vazias = [ln for ln in linhas if ln]
    return nao_vazias if nao_vazias else [s]


def _listas_doc_padrao_vazio() -> tuple[list[str], list[str], list[str], list[str]]:
    return [""], [""], [""], [""]


def parse_doc_requisito_completo(
    conteudo: str | None,
) -> tuple[dict[str, str], list[str], list[str], list[str], list[str]]:
    """
    Extrai cabeçalho + RF, RNF, regras e critérios de aceitação do `conteudo` (fase doc_requisito).
    JSON: chaves opcionais nome_funcionalidade, descricao_detalhada, restricoes; listas como str ou array.
    Legado: só RF/RNF/regras → cabeçalho vazio e critérios [""].
    Legado texto plano: um item em RF, resto [""].
    """
    header: dict[str, str] = {"nome_funcionalidade": "", "descricao_detalhada": "", "restricoes": ""}
    raw = (conteudo or "").strip()
    if not raw:
        return header, *_listas_doc_padrao_vazio()
    try:
        o = json.loads(raw)
        if isinstance(o, dict):
            header["nome_funcionalidade"] = str(o.get("nome_funcionalidade") or "").strip()
            header["descricao_detalhada"] = str(o.get("descricao_detalhada") or "").strip()
            header["restricoes"] = str(o.get("restricoes") or "").strip()
            rf = _valor_campo_doc_para_lista(o.get("requisitos_funcionais"))
            rnf = _valor_campo_doc_para_lista(o.get("requisitos_nao_funcionais"))
            rg = _valor_campo_doc_para_lista(o.get("regras_negocio"))
            crit = _valor_campo_doc_para_lista(o.get("criterios_aceitacao"))
            if not rf:
                rf = [""]
            if not rnf:
                rnf = [""]
            if not rg:
                rg = [""]
            if not crit:
                crit = [""]
            return header, rf, rnf, rg, crit
    except json.JSONDecodeError:
        pass
    rf0, rnf0, rg0, cr0 = _listas_doc_padrao_vazio()
    rf0 = [raw] if raw else [""]
    return header, rf0, rnf0, rg0, cr0


def serialize_doc_requisito_completo(
    header: dict[str, str] | None,
    rf: list[str] | None,
    rnf: list[str] | None,
    regras: list[str] | None,
    criterios: list[str] | None,
) -> str:
    def _limpar(xs: list[str] | None) -> list[str]:
        if not xs:
            return []
        return [str(x).strip() for x in xs if str(x).strip()]

    h = header or {}
    return json.dumps(
        {
            "nome_funcionalidade": str(h.get("nome_funcionalidade") or "").strip(),
            "descricao_detalhada": str(h.get("descricao_detalhada") or "").strip(),
            "restricoes": str(h.get("restricoes") or "").strip(),
            "requisitos_funcionais": _limpar(rf),
            "requisitos_nao_funcionais": _limpar(rnf),
            "regras_negocio": _limpar(regras),
            "criterios_aceitacao": _limpar(criterios),
        },
        ensure_ascii=False,
    )


def parse_prontidao_dev_conteudo(conteudo: str | None) -> dict[str, Any]:
    """
    Fase prontidao_dev: JSON estruturado ou legado (texto livre em observacoes_tecnicas).
    checklist: lista de chaves marcadas ou dict legado com booleanos.
    """
    out: dict[str, Any] = {
        "id_requisito": None,
        "responsavel_desenvolvimento": "",
        "registrado_por": "",
        "data_prontidao": "",
        "observacoes_tecnicas": "",
        "checklist": [],
    }
    raw = (conteudo or "").strip()
    if not raw:
        return out
    try:
        o = json.loads(raw)
        if isinstance(o, dict):
            rid = o.get("id_requisito")
            if rid is not None and str(rid).strip() != "":
                try:
                    out["id_requisito"] = int(rid)
                except (TypeError, ValueError):
                    out["id_requisito"] = None
            out["responsavel_desenvolvimento"] = str(o.get("responsavel_desenvolvimento") or "").strip()
            out["registrado_por"] = str(o.get("registrado_por") or "").strip()
            out["data_prontidao"] = str(o.get("data_prontidao") or "").strip()
            out["observacoes_tecnicas"] = str(o.get("observacoes_tecnicas") or "").strip()
            ch = o.get("checklist")
            if isinstance(ch, list):
                out["checklist"] = [str(x) for x in ch if str(x).strip()]
            elif isinstance(ch, dict):
                out["checklist"] = [str(k) for k, v in ch.items() if v]
            return out
    except json.JSONDecodeError:
        pass
    out["observacoes_tecnicas"] = raw
    return out


def serialize_prontidao_dev_conteudo(payload: dict[str, Any], id_requisito_atividade: int) -> str:
    ch = payload.get("checklist")
    if not isinstance(ch, list):
        ch = []
    ch_limpa = [str(x).strip() for x in ch if str(x).strip()]
    return json.dumps(
        {
            "id_requisito": int(id_requisito_atividade),
            "responsavel_desenvolvimento": str(payload.get("responsavel_desenvolvimento") or "").strip(),
            "registrado_por": str(payload.get("registrado_por") or "").strip(),
            "data_prontidao": str(payload.get("data_prontidao") or "").strip(),
            "observacoes_tecnicas": str(payload.get("observacoes_tecnicas") or "").strip(),
            "checklist": ch_limpa,
        },
        ensure_ascii=False,
    )


def parse_entrega_dev_conteudo(conteudo: str | None) -> dict[str, Any]:
    """
    Fase entrega_dev (DEVELOP → TEST): JSON estruturado ou legado (texto em descricao_desenvolvido).
    """
    out: dict[str, Any] = {
        "id_requisito": None,
        "nome_entrega": "",
        "descricao_desenvolvido": "",
        "alteracoes": "",
        "validacao_qa": "",
        "branch_referencia": "",
        "commit_referencia": "",
        "desenvolvedor": "",
        "data_entrega_teste": "",
    }
    raw = (conteudo or "").strip()
    if not raw:
        return out
    try:
        o = json.loads(raw)
        if isinstance(o, dict):
            rid = o.get("id_requisito")
            if rid is not None and str(rid).strip() != "":
                try:
                    out["id_requisito"] = int(rid)
                except (TypeError, ValueError):
                    out["id_requisito"] = None
            out["nome_entrega"] = str(o.get("nome_entrega") or o.get("nome_funcionalidade") or "").strip()
            out["descricao_desenvolvido"] = str(o.get("descricao_desenvolvido") or o.get("o_que_foi_desenvolvido") or "").strip()
            out["alteracoes"] = str(o.get("alteracoes") or o.get("o_que_foi_alterado") or "").strip()
            out["validacao_qa"] = str(o.get("validacao_qa") or o.get("o_que_deve_ser_validado") or "").strip()
            out["branch_referencia"] = str(o.get("branch_referencia") or "").strip()
            out["commit_referencia"] = str(o.get("commit_referencia") or "").strip()
            out["desenvolvedor"] = str(o.get("desenvolvedor") or o.get("id_desenvolvedor") or "").strip()
            out["data_entrega_teste"] = str(o.get("data_entrega_teste") or "").strip()
            return out
    except json.JSONDecodeError:
        pass
    out["descricao_desenvolvido"] = raw
    return out


def serialize_entrega_dev_conteudo(payload: dict[str, Any], id_requisito_atividade: int) -> str:
    return json.dumps(
        {
            "id_requisito": int(id_requisito_atividade),
            "nome_entrega": str(payload.get("nome_entrega") or "").strip(),
            "descricao_desenvolvido": str(payload.get("descricao_desenvolvido") or "").strip(),
            "alteracoes": str(payload.get("alteracoes") or "").strip(),
            "validacao_qa": str(payload.get("validacao_qa") or "").strip(),
            "branch_referencia": str(payload.get("branch_referencia") or "").strip(),
            "commit_referencia": str(payload.get("commit_referencia") or "").strip(),
            "desenvolvedor": str(payload.get("desenvolvedor") or "").strip(),
            "data_entrega_teste": str(payload.get("data_entrega_teste") or "").strip(),
        },
        ensure_ascii=False,
    )


def caso_teste_vazio() -> dict[str, str]:
    """Modelo de um caso vazio (para UI: novo cartão)."""
    return _caso_teste_vazio()


def _caso_teste_vazio() -> dict[str, str]:
    return {
        "resumo": "",
        "passos": "",
        "resultado_esperado": "",
        "resultado_obtido": "",
        "status": "PENDENTE",
        "executor": "",
        "data_execucao": "",
        "evidencia": "",
    }


def _normalize_caso_teste_dict(o: dict) -> dict[str, str]:
    st = str(o.get("status") or "PENDENTE").strip().upper()
    if st not in ("APROVADO", "REPROVADO", "PENDENTE"):
        st = "PENDENTE"
    return {
        "resumo": str(o.get("resumo") or "").strip(),
        "passos": str(o.get("passos") or o.get("passos_execucao") or "").strip(),
        "resultado_esperado": str(o.get("resultado_esperado") or "").strip(),
        "resultado_obtido": str(o.get("resultado_obtido") or "").strip(),
        "status": st,
        "executor": str(o.get("executor") or o.get("usuario_executor") or "").strip(),
        "data_execucao": str(o.get("data_execucao") or "").strip(),
        "evidencia": str(o.get("evidencia") or o.get("observacao") or "").strip(),
    }


def parse_casos_teste_conteudo(conteudo: str | None) -> dict[str, Any]:
    """Fase casos_teste (TEST → DEPLOY): lista de casos em JSON ou legado texto em passos."""
    out: dict[str, Any] = {"id_requisito": None, "casos": [_caso_teste_vazio()]}
    raw = (conteudo or "").strip()
    if not raw:
        return out
    try:
        o = json.loads(raw)
        if isinstance(o, dict):
            rid = o.get("id_requisito")
            if rid is not None and str(rid).strip() != "":
                try:
                    out["id_requisito"] = int(rid)
                except (TypeError, ValueError):
                    out["id_requisito"] = None
            casos = o.get("casos")
            if isinstance(casos, list) and len(casos) > 0:
                norm: list[dict[str, str]] = []
                for x in casos:
                    norm.append(_normalize_caso_teste_dict(x) if isinstance(x, dict) else _caso_teste_vazio())
                out["casos"] = norm
            return out
    except json.JSONDecodeError:
        pass
    leg = _caso_teste_vazio()
    leg["passos"] = raw
    out["casos"] = [leg]
    return out


def serialize_casos_teste_conteudo(payload: dict[str, Any], id_requisito_atividade: int) -> str:
    casos = payload.get("casos")
    if not isinstance(casos, list):
        casos = []
    limpos = [_normalize_caso_teste_dict(x) for x in casos if isinstance(x, dict)]
    return json.dumps(
        {"id_requisito": int(id_requisito_atividade), "casos": limpos},
        ensure_ascii=False,
    )


def parse_deploy_conteudo(conteudo: str | None) -> dict[str, Any]:
    """Fase deploy (DEPLOY → DONE): registo de implantação; legado texto em observações."""
    out: dict[str, Any] = {
        "id_requisito": None,
        "versao_entregue": "",
        "ambiente": "",
        "data_deploy": "",
        "responsavel_deploy": "",
        "observacoes": "",
    }
    raw = (conteudo or "").strip()
    if not raw:
        return out
    try:
        o = json.loads(raw)
        if isinstance(o, dict):
            rid = o.get("id_requisito")
            if rid is not None and str(rid).strip() != "":
                try:
                    out["id_requisito"] = int(rid)
                except (TypeError, ValueError):
                    out["id_requisito"] = None
            out["versao_entregue"] = str(o.get("versao_entregue") or o.get("versao") or "").strip()
            out["ambiente"] = str(o.get("ambiente") or "").strip()
            out["data_deploy"] = str(o.get("data_deploy") or "").strip()
            out["responsavel_deploy"] = str(
                o.get("responsavel_deploy") or o.get("responsavel") or o.get("id_responsavel_deploy") or ""
            ).strip()
            out["observacoes"] = str(o.get("observacoes") or "").strip()
            return out
    except json.JSONDecodeError:
        pass
    out["observacoes"] = raw
    return out


def serialize_deploy_conteudo(payload: dict[str, Any], id_requisito_atividade: int) -> str:
    return json.dumps(
        {
            "id_requisito": int(id_requisito_atividade),
            "versao_entregue": str(payload.get("versao_entregue") or "").strip(),
            "ambiente": str(payload.get("ambiente") or "").strip(),
            "data_deploy": str(payload.get("data_deploy") or "").strip(),
            "responsavel_deploy": str(payload.get("responsavel_deploy") or "").strip(),
            "observacoes": str(payload.get("observacoes") or "").strip(),
        },
        ensure_ascii=False,
    )


FASES_DOC_VALIDAS: tuple[str, ...] = (
    "doc_requisito",
    "prontidao_dev",
    "entrega_dev",
    "casos_teste",
    "deploy",
    "encerramento",
)

_DDL = """
CREATE TABLE IF NOT EXISTS requisito_doc_fase (
    id_requisito INTEGER NOT NULL REFERENCES requisito_estruturado(id_requisito) ON DELETE CASCADE,
    fase_codigo VARCHAR(40) NOT NULL,
    conteudo TEXT NOT NULL DEFAULT '',
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_requisito, fase_codigo),
    CONSTRAINT requisito_doc_fase_codigo_check CHECK (fase_codigo IN (
        'doc_requisito', 'prontidao_dev', 'entrega_dev', 'casos_teste', 'deploy', 'encerramento'
    ))
);
CREATE INDEX IF NOT EXISTS idx_requisito_doc_fase_requisito ON requisito_doc_fase(id_requisito);
"""


def _ensure_table(cur) -> None:
    for stmt in _DDL.strip().split(";"):
        s = stmt.strip()
        if s:
            cur.execute(s)


def _requisito_existe(cur, id_requisito: int) -> bool:
    cur.execute("SELECT 1 FROM requisito_estruturado WHERE id_requisito = %s", (id_requisito,))
    return cur.fetchone() is not None


def obter_documentacao_fases(id_requisito: int) -> dict[str, str]:
    """Devolve dict com as seis chaves; valores vazios se ainda não gravados."""
    base = {k: "" for k in FASES_DOC_VALIDAS}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_table(cur)
            cur.execute(
                "SELECT fase_codigo, conteudo FROM requisito_doc_fase WHERE id_requisito = %s",
                (id_requisito,),
            )
            rows = cur.fetchall()
        conn.commit()
        for row in rows:
            cod, txt = row[0], row[1] or ""
            if cod in base:
                base[cod] = txt
        return base
    finally:
        conn.close()


def salvar_documentacao_fase(id_requisito: int, fase_codigo: str, conteudo: str) -> dict[str, Any]:
    fase = (fase_codigo or "").strip()
    if fase not in FASES_DOC_VALIDAS:
        raise ValueError(f"fase_codigo inválido. Use: {', '.join(FASES_DOC_VALIDAS)}")
    texto = (conteudo or "").strip()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_table(cur)
            if not _requisito_existe(cur, id_requisito):
                raise ValueError("Requisito não encontrado.")
            cur.execute(
                """
                INSERT INTO requisito_doc_fase (id_requisito, fase_codigo, conteudo, atualizado_em)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id_requisito, fase_codigo)
                DO UPDATE SET conteudo = EXCLUDED.conteudo, atualizado_em = CURRENT_TIMESTAMP
                RETURNING atualizado_em
                """,
                (id_requisito, fase, texto),
            )
            row = cur.fetchone()
            conn.commit()
            ts = row[0] if row else None
            return {"ok": True, "fase_codigo": fase, "atualizado_em": ts.isoformat() if ts and hasattr(ts, "isoformat") else str(ts)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
