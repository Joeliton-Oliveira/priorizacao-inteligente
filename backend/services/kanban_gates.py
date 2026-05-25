# -*- coding: utf-8 -*-
"""
Regras de gate documental da esteira Kanban — partilhadas entre Dash (app.py) e API (api.py).
Proíbe avanço de coluna na persistência se faltar documentação gravada em requisito_doc_fase.
"""
from __future__ import annotations

from db.doc_fase_repo import (
    obter_documentacao_fases,
    parse_casos_teste_conteudo,
    parse_deploy_conteudo,
    parse_doc_requisito_completo,
    parse_entrega_dev_conteudo,
    parse_prontidao_dev_conteudo,
)

KANBAN_COLUNAS = ["BACKLOG", "TO DO", "DEVELOP", "TEST", "DEPLOY", "DONE"]
KANBAN_NEXT = {"BACKLOG": "TO DO", "TO DO": "DEVELOP", "DEVELOP": "TEST", "TEST": "DEPLOY", "DEPLOY": "DONE"}

PRONTIDAO_CHECKLIST_OPCOES = [
    {"label": " Documento de requisito revisado", "value": "documento_revisado"},
    {"label": " Critérios de aceitação existentes / compreendidos", "value": "criterios_existem"},
    {"label": " Escopo entendido pela equipa", "value": "escopo_entendido"},
    {"label": " Responsável pelo desenvolvimento definido", "value": "responsavel_definido"},
]
PRONTIDAO_CHECKLIST_VALORES = [o["value"] for o in PRONTIDAO_CHECKLIST_OPCOES]

COLUNA_PARA_DOC_GATE: dict[str, tuple[str, str]] = {
    "BACKLOG": ("doc_requisito", "BACKLOG → TO DO"),
    "TO DO": ("prontidao_dev", "TO DO → DEVELOP"),
    "DEVELOP": ("entrega_dev", "DEVELOP → TEST"),
    "TEST": ("casos_teste", "TEST → DEPLOY"),
    "DEPLOY": ("deploy", "DEPLOY → DONE"),
}


def status_api_para_coluna_kanban(status_raw: str | None) -> str:
    """Alinha a app.status_atual_para_coluna_kanban (status vindo da API / BD)."""
    s = (status_raw or "").strip().upper().replace(" ", "_")
    mapping = {
        "BACKLOG": "BACKLOG",
        "TO_DO": "TO DO",
        "TODO": "TO DO",
        "DEVELOP": "DEVELOP",
        "EM_DESENVOLVIMENTO": "DEVELOP",
        "TEST": "TEST",
        "EM_TESTE": "TEST",
        "DEPLOY": "DEPLOY",
        "DONE": "DONE",
        "CONCLUIDO": "DONE",
        "CONCLUÍDO": "DONE",
        "AVALIADO": "TO DO",
        "PRIORIZADO": "TO DO",
    }
    if s in mapping:
        return mapping[s]
    for col in KANBAN_COLUNAS:
        if s == col.upper().replace(" ", "_"):
            return col
    return "BACKLOG"


def doc_lista_tem_item_preenchido(vals) -> bool:
    if vals is None:
        return False
    if not isinstance(vals, list):
        return bool(str(vals).strip())
    return any(str(v).strip() for v in vals if v is not None)


def caso_linha_aprovada_completa(r, p, esp, obt, st, ex, dt, ev) -> bool:
    if (st or "").strip().upper() != "APROVADO":
        return False
    for v in (r, p, esp, obt, ex):
        if not str(v or "").strip():
            return False
    if not (dt or "").strip():
        return False
    if not str(ev or "").strip():
        return False
    return True


def doc_requisito_criterios_aceitacao_preenchidos(fase_docs: dict | None) -> bool:
    """True se a fase doc_requisito (gravada) contém pelo menos um critério de aceitação."""
    fd = fase_docs if isinstance(fase_docs, dict) else {}
    raw = fd.get("doc_requisito")
    if raw is None:
        s = ""
    elif isinstance(raw, str):
        s = raw
    else:
        s = str(raw)
    _cab, _rf, _rnf, _rg, crit = parse_doc_requisito_completo(s)
    return doc_lista_tem_item_preenchido(crit)


def eval_fase_docs_doc_requisito_gate(raw: str | None) -> tuple[bool, list[str]]:
    cab, rf, rnf, rg, crit = parse_doc_requisito_completo(raw or "")
    nome = (cab.get("nome_funcionalidade") or "").strip()
    desc = (cab.get("descricao_detalhada") or "").strip()
    restr = (cab.get("restricoes") or "").strip()
    falta: list[str] = []
    if not nome:
        falta.append("Nome da funcionalidade")
    if not desc:
        falta.append("Descrição detalhada")
    if not restr:
        falta.append("Restrições (ou «Nenhuma»)")
    if not doc_lista_tem_item_preenchido(rf):
        falta.append("Pelo menos um requisito funcional (RF)")
    if not doc_lista_tem_item_preenchido(rnf):
        falta.append("Pelo menos um requisito não funcional (RNF)")
    if not doc_lista_tem_item_preenchido(rg):
        falta.append("Pelo menos uma regra de negócio")
    if not doc_lista_tem_item_preenchido(crit):
        falta.append("Pelo menos um critério de aceitação")
    return (not falta, falta)


def eval_fase_docs_prontidao_gate(raw: str | None, fase_docs: dict | None = None) -> tuple[bool, list[str]]:
    pr = parse_prontidao_dev_conteudo(raw or "")
    falta: list[str] = []
    if not (pr.get("responsavel_desenvolvimento") or "").strip():
        falta.append("Responsável pelo desenvolvimento")
    if not (pr.get("registrado_por") or "").strip():
        falta.append("Registado por")
    if not pr.get("data_prontidao"):
        falta.append("Data da prontidão")
    sel = set(pr.get("checklist") if isinstance(pr.get("checklist"), list) else [])
    resp_txt = (pr.get("responsavel_desenvolvimento") or "").strip()
    rotulos = {o["value"]: o["label"].strip() for o in PRONTIDAO_CHECKLIST_OPCOES}
    for k in PRONTIDAO_CHECKLIST_VALORES:
        if k in sel:
            continue
        # O campo de texto «Responsável…» cumpre o mesmo critério que o item de checklist homónimo.
        if k == "responsavel_definido" and resp_txt:
            continue
        # Critérios já registados na aba BACKLOG (doc_requisito) dispensam marcar só o checklist TO DO.
        if k == "criterios_existem" and doc_requisito_criterios_aceitacao_preenchidos(fase_docs):
            continue
        falta.append(rotulos.get(k, k))
    return (not falta, falta)


def eval_fase_docs_entrega_gate(raw: str | None) -> tuple[bool, list[str]]:
    ed = parse_entrega_dev_conteudo(raw or "")
    checks = [
        ((ed.get("nome_entrega") or "").strip(), "Nome da funcionalidade / correção"),
        ((ed.get("descricao_desenvolvido") or "").strip(), "O que foi desenvolvido"),
        ((ed.get("alteracoes") or "").strip(), "O que foi alterado"),
        ((ed.get("validacao_qa") or "").strip(), "O que deve ser validado (QA)"),
        ((ed.get("branch_referencia") or "").strip(), "Branch de referência"),
        ((ed.get("commit_referencia") or "").strip(), "Commit de referência"),
        ((ed.get("desenvolvedor") or "").strip(), "Desenvolvedor (quem entregou)"),
        (bool((ed.get("data_entrega_teste") or "").strip()), "Data de entrega para teste"),
    ]
    falta = [label for ok, label in checks if not ok]
    return (not falta, falta)


def eval_fase_docs_deploy_gate(raw: str | None) -> tuple[bool, list[str]]:
    dep = parse_deploy_conteudo(raw or "")
    falta: list[str] = []
    if not (dep.get("versao_entregue") or "").strip():
        falta.append("Versão entregue")
    if not (dep.get("ambiente") or "").strip():
        falta.append("Ambiente (ex.: produção, homologação, staging)")
    if not (dep.get("data_deploy") or "").strip():
        falta.append("Data do deploy")
    if not (dep.get("responsavel_deploy") or "").strip():
        falta.append("Responsável pelo deploy")
    return (not falta, falta)


def eval_fase_docs_casos_teste_gate(raw: str | None) -> tuple[bool, list[str], int, int]:
    ct = parse_casos_teste_conteudo(raw or "")
    casos = ct.get("casos") if isinstance(ct.get("casos"), list) else []
    n = len(casos)
    aprov_ok = 0
    for c in casos:
        if not isinstance(c, dict):
            continue
        if caso_linha_aprovada_completa(
            c.get("resumo"),
            c.get("passos"),
            c.get("resultado_esperado"),
            c.get("resultado_obtido"),
            c.get("status"),
            c.get("executor"),
            c.get("data_execucao"),
            c.get("evidencia"),
        ):
            aprov_ok += 1
    if n == 0:
        return False, ["Adicione pelo menos um caso de teste e preencha os campos."], n, aprov_ok
    if aprov_ok >= 1:
        return True, [], n, aprov_ok
    return (
        False,
        [
            "Pelo menos um caso com status APROVADO",
            "Todos os campos obrigatórios preenchidos (resumo, passos, esperado, obtido, executor, data)",
            "Evidência ou observação do teste (campo Evidência)",
        ],
        n,
        aprov_ok,
    )


def gate_documental_para_avancar_de_coluna(col_k: str, fase_docs: dict | None) -> tuple[bool, list[str]]:
    if col_k not in COLUNA_PARA_DOC_GATE:
        return True, []
    fd = fase_docs if isinstance(fase_docs, dict) else {}
    cod, _rot = COLUNA_PARA_DOC_GATE[col_k]
    raw = fd.get(cod)
    if raw is None:
        s = ""
    elif isinstance(raw, str):
        s = raw
    else:
        s = str(raw)
    if cod == "doc_requisito":
        return eval_fase_docs_doc_requisito_gate(s)
    if cod == "prontidao_dev":
        return eval_fase_docs_prontidao_gate(s, fd)
    if cod == "entrega_dev":
        return eval_fase_docs_entrega_gate(s)
    if cod == "deploy":
        return eval_fase_docs_deploy_gate(s)
    if cod == "casos_teste":
        ok, falta, _n, _a = eval_fase_docs_casos_teste_gate(s)
        return ok, falta
    return True, []


def validar_transicao_status_kanban(id_requisito: int, status_destino_bruto: str) -> tuple[bool, str | None]:
    """
    Impede persistência de avanço de coluna sem documentação exigida.
    Retrocesso (qualquer número de colunas) é permitido. Avanço só de uma coluna.
    Retorna (True, None) se pode gravar, (False, mensagem) caso contrário.
    """
    from db.avaliacao_repo import obter_status_atual_requisito

    dest_api = (status_destino_bruto or "").upper().strip().replace(" ", "_") or "BACKLOG"
    cur_row = obter_status_atual_requisito(id_requisito)
    cur_api = (cur_row or "BACKLOG").upper().strip().replace(" ", "_") if cur_row else "BACKLOG"
    if not cur_api:
        cur_api = "BACKLOG"

    cur_col = status_api_para_coluna_kanban(cur_api)
    dest_col = status_api_para_coluna_kanban(dest_api)

    if dest_col not in KANBAN_COLUNAS:
        return False, "Status de destino inválido para a esteira Kanban."

    try:
        idx_cur = KANBAN_COLUNAS.index(cur_col)
        idx_dest = KANBAN_COLUNAS.index(dest_col)
    except ValueError:
        return False, "Não foi possível interpretar a posição atual ou destino na esteira."

    if idx_dest < idx_cur:
        return True, None
    if idx_dest == idx_cur:
        return True, None
    if idx_dest > idx_cur + 1:
        return False, "Avance apenas uma coluna de cada vez. Salto de fase não é permitido."

    fases = obter_documentacao_fases(id_requisito)
    ok, falta = gate_documental_para_avancar_de_coluna(cur_col, fases)
    if not ok:
        return False, "Transição bloqueada: documentação da fase atual incompleta. Falta: " + "; ".join(falta)
    return True, None
