"""
Front-end Dash — Priorização Inteligente de Requisitos (Matriz).
Contrato funcional: README.md (secção Front-end).

Hub /atividade/<id>: consome GET estáveis quando existirem; visão 360, auditoria e gates
usam os paths documentados para o backend consolidado — 404 = indisponível neste workspace.
"""
import json
import re
import unicodedata
from dash import Dash, dcc, html, Input, Output, State, ALL, MATCH, no_update, callback_context
import plotly.graph_objs as go

from services.api_client import (
    EP_NOT_FOUND,
    analisar_requisito as api_analisar,
    salvar_avaliacao as api_salvar,
    listar_atividades as api_listar_atividades,
    atualizar_status_requisito as api_atualizar_status_requisito,
    obter_fila_duas as api_obter_fila_duas,
    get_auditoria_demanda as api_get_auditoria_demanda,
    get_kanban_gates_demanda as api_get_kanban_gates_demanda,
    get_visao_360_demanda as api_get_visao_360_demanda,
    criar_projeto_cadastro as api_criar_projeto,
    listar_projetos_cadastro as api_listar_projetos,
    evoluir_versao_projeto_cadastro as api_evoluir_projeto,
    atualizar_status_projeto_cadastro as api_patch_status_projeto,
    obter_documentacao_fase_requisito as api_obter_documentacao_fase,
    salvar_documentacao_fase_requisito as api_salvar_documentacao_fase,
)
from config_fila import get_config_fila, save_config_fila
from db.doc_fase_repo import (
    caso_teste_vazio,
    parse_doc_requisito_completo,
    parse_casos_teste_conteudo,
    parse_deploy_conteudo,
    parse_entrega_dev_conteudo,
    parse_prontidao_dev_conteudo,
    serialize_casos_teste_conteudo,
    serialize_deploy_conteudo,
    serialize_doc_requisito_completo,
    serialize_entrega_dev_conteudo,
    serialize_prontidao_dev_conteudo,
)
from services.kanban_gates import (
    PRONTIDAO_CHECKLIST_OPCOES as _PRONTIDAO_CHECKLIST_OPCOES,
    PRONTIDAO_CHECKLIST_VALORES as _PRONTIDAO_CHECKLIST_VALORES,
    COLUNA_PARA_DOC_GATE as _COLUNA_PARA_DOC_GATE,
    doc_lista_tem_item_preenchido as _doc_lista_tem_item_preenchido,
    caso_linha_aprovada_completa as _caso_linha_aprovada_completa,
    eval_fase_docs_doc_requisito_gate as _eval_fase_docs_doc_requisito_gate,
    eval_fase_docs_prontidao_gate as _eval_fase_docs_prontidao_gate,
    eval_fase_docs_entrega_gate as _eval_fase_docs_entrega_gate,
    eval_fase_docs_deploy_gate as _eval_fase_docs_deploy_gate,
    eval_fase_docs_casos_teste_gate as _eval_fase_docs_casos_teste_gate,
    gate_documental_para_avancar_de_coluna as _gate_documental_para_avancar_de_coluna,
    doc_requisito_criterios_aceitacao_preenchidos as _doc_requisito_criterios_ok,
)
import version as version_info

CORES = {
    "bg": "#f1f5f9",
    "surface": "#ffffff",
    "primary": "#2563eb",
    "text": "#1e293b",
    "text_muted": "#64748b",
    "border": "#e2e8f0",
    "error": "#dc2626",
    "success": "#16a34a",
    "bug": "#dc2626",
    "feature": "#2563eb",
}
R = 10
S = 8

ESTILO_APP = {
    "fontFamily": '"Inter", "Segoe UI", system-ui, sans-serif',
    "backgroundColor": CORES["bg"],
    "minHeight": "100vh",
    "height": "100%",
    "padding": "0",
    "margin": "0",
}
ESTILO_SIDEBAR = {
    "width": "220px",
    "minWidth": "220px",
    "flexShrink": 0,
    "height": "100%",
    "minHeight": "100vh",
    "alignSelf": "stretch",
    "backgroundColor": CORES["bg"],
    "borderRight": f"1px solid {CORES['border']}",
    "padding": f"{S*4}px {S*2}px",
    "boxSizing": "border-box",
    "overflowY": "auto",
}
ESTILO_NAV_LINK = {
    "display": "block",
    "padding": f"{S*2}px {S*3}px",
    "fontSize": "0.9375rem",
    "color": CORES["primary"],
    "textDecoration": "none",
    "borderRadius": f"{R}px",
    "marginBottom": f"{S}px",
}
ESTILO_MAIN = {
    "flex": "1",
    "minWidth": 0,
    "minHeight": "100vh",
    "padding": f"{S*3}px",
    "boxSizing": "border-box",
    "overflowY": "auto",
}
ESTILO_SECAO = {
    "marginBottom": f"{S*4}px",
    "padding": f"{S*3}px",
    "borderRadius": f"{R}px",
    "backgroundColor": CORES["surface"],
    "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)",
    "border": f"1px solid {CORES['border']}",
}
ESTILO_CAMPO = {"marginBottom": f"{S*2}px"}
ESTILO_LABEL = {
    "fontWeight": "600",
    "display": "block",
    "marginBottom": f"{S//2}px",
    "fontSize": "0.875rem",
    "color": CORES["text"],
}
ESTILO_INPUT = {
    "width": "100%",
    "padding": f"{S}px {S*2}px",
    "borderRadius": f"{R-2}px",
    "border": f"1px solid {CORES['border']}",
    "fontSize": "0.9375rem",
}
ESTILO_INPUT_READONLY = {**ESTILO_INPUT, "backgroundColor": "#f1f5f9", "cursor": "not-allowed", "color": CORES["text_muted"]}
ESTILO_BOTAO = {
    "padding": f"{S*2}px {S*4}px",
    "fontSize": "1rem",
    "fontWeight": "600",
    "cursor": "pointer",
    "backgroundColor": CORES["primary"],
    "color": "#fff",
    "border": "none",
    "borderRadius": f"{R}px",
    "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
}
ESTILO_ERRO = {"color": CORES["error"], "marginTop": f"{S}px", "fontSize": "0.875rem"}
ESTILO_BOTAO_SEC = {
    **ESTILO_BOTAO,
    "backgroundColor": CORES["surface"],
    "color": CORES["primary"],
    "border": f"1px solid {CORES['primary']}",
    "boxShadow": "none",
}
_OP_STATUS_PROJETO = [
    {"label": "ativo", "value": "ativo"},
    {"label": "arquivado", "value": "arquivado"},
    {"label": "descontinuado", "value": "descontinuado"},
]
ESTILO_SUCESSO = {"color": CORES["success"], "marginTop": f"{S}px", "fontSize": "0.875rem"}
ESTILO_TABELA = {"padding": f"{S}px {S*2}px", "border": f"1px solid {CORES['border']}", "textAlign": "left"}
ESTILO_APOIO = {"fontSize": "0.8125rem", "color": CORES["text_muted"], "marginBottom": f"{S}px", "lineHeight": "1.4"}

KANBAN_COLUNAS = ["BACKLOG", "TO DO", "DEVELOP", "TEST", "DEPLOY", "DONE"]
KANBAN_NEXT = {"BACKLOG": "TO DO", "TO DO": "DEVELOP", "DEVELOP": "TEST", "TEST": "DEPLOY", "DEPLOY": "DONE"}
KANBAN_PREV = {"TO DO": "BACKLOG", "DEVELOP": "TO DO", "TEST": "DEVELOP", "DEPLOY": "TEST", "DONE": "DEPLOY"}

# Abas de documentação: mesmos rótulos que as colunas da esteira Kanban (KANBAN_COLUNAS)
_ATIVIDADE_DOC_FASES_UI = (
    ("doc_requisito", KANBAN_COLUNAS[0], KANBAN_COLUNAS[0], "BACKLOG → TO DO"),
    ("prontidao_dev", KANBAN_COLUNAS[1], KANBAN_COLUNAS[1], "TO DO → DEVELOP"),
    ("entrega_dev", KANBAN_COLUNAS[2], KANBAN_COLUNAS[2], "DEVELOP → TEST"),
    ("casos_teste", KANBAN_COLUNAS[3], KANBAN_COLUNAS[3], "TEST → DEPLOY"),
    ("deploy", KANBAN_COLUNAS[4], KANBAN_COLUNAS[4], "DEPLOY → DONE"),
    ("encerramento", KANBAN_COLUNAS[5], KANBAN_COLUNAS[5], "DONE (lições aprendidas, comunicação)"),
)

_COL_API = {"BACKLOG": "BACKLOG", "TO DO": "TO_DO", "DEVELOP": "DEVELOP", "TEST": "TEST", "DEPLOY": "DEPLOY", "DONE": "DONE"}

_CASOS_TESTE_STATUS_OPTS = [
    {"label": "Pendente", "value": "PENDENTE"},
    {"label": "Aprovado", "value": "APROVADO"},
    {"label": "Reprovado", "value": "REPROVADO"},
]

PERFIL_SOLICITANTE_OPCOES_BASE = [
    {"label": "Selecione", "value": ""},
    {"label": "Usuário final", "value": "usuario_final"},
    {"label": "Analista", "value": "analista"},
    {"label": "Gestor", "value": "gestor"},
    {"label": "Desenvolvedor", "value": "desenvolvedor"},
    {"label": "Suporte", "value": "suporte"},
]


def _slug_perfil_solicitante(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^a-z0-9_]", "", t)
    return t or ""


def status_atual_para_coluna_kanban(status_raw: str | None) -> str:
    s = (status_raw or "").strip().upper().replace(" ", "_")
    mapping = {
        "BACKLOG": "BACKLOG",
        "TO_DO": "TO DO", "TODO": "TO DO",
        "DEVELOP": "DEVELOP", "EM_DESENVOLVIMENTO": "DEVELOP",
        "TEST": "TEST", "EM_TESTE": "TEST",
        "DEPLOY": "DEPLOY",
        "DONE": "DONE", "CONCLUIDO": "DONE", "CONCLUÍDO": "DONE",
        "AVALIADO": "TO DO", "PRIORIZADO": "TO DO",
    }
    if s in mapping:
        return mapping[s]
    for col in KANBAN_COLUNAS:
        if s == col.upper().replace(" ", "_"):
            return col
    return "BACKLOG"


def coluna_para_status_api(col: str) -> str:
    return _COL_API.get(col, "BACKLOG")


def _status_item_para_coluna_kanban(it: dict) -> str:
    sk = it.get("status_kanban")
    if sk is not None and str(sk).strip() != "":
        return status_atual_para_coluna_kanban(str(sk))
    return status_atual_para_coluna_kanban(it.get("status_atual"))


app = Dash(__name__, title="Priorização Inteligente de Requisitos")
app.config.suppress_callback_exceptions = True

_HIDE = {"display": "none"}
_SHOW = {"display": "block"}

layout_secao1 = html.Div([
    html.Div([
        html.Span("1", style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "fontSize": "0.875rem", "marginRight": f"{S*2}px"}),
        html.H2("Identificação da Demanda", style={"margin": 0, "fontSize": "1.25rem", "fontWeight": "700", "color": CORES["text"]}),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"}),
    html.Div([
        html.Label("Descrição inicial da demanda", style=ESTILO_LABEL),
        html.Span("Explique o problema ou a melhoria.", style=ESTILO_APOIO),
        dcc.Textarea(id="texto_original", placeholder="Ex.: Quando o cliente tenta finalizar a compra...", style={**ESTILO_INPUT, "minHeight": "100px", "resize": "vertical"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Tipo da demanda", style=ESTILO_LABEL),
        dcc.Dropdown(id="tipo_informado_usuario", options=[
            {"label": "Bug", "value": "BUG"},
            {"label": "Melhoria / nova funcionalidade", "value": "INCREMENTO"},
            {"label": "Não sei informar", "value": "NAO_SEI"},
        ], value="NAO_SEI", clearable=False),
    ], style=ESTILO_CAMPO),
    html.Div([html.Label("Área do sistema envolvida", style=ESTILO_LABEL), dcc.Input(id="modulo_afetado", type="text", placeholder="Ex.: checkout", style=ESTILO_INPUT)], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Importância dessa área para o negócio", style=ESTILO_LABEL),
        dcc.Textarea(id="contexto_negocio", placeholder="Explique a importância operacional ou de negócio.", style={**ESTILO_INPUT, "minHeight": "72px"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Resultado esperado", style=ESTILO_LABEL),
        dcc.Textarea(id="objetivo_desejado", placeholder="O que deveria acontecer corretamente?", style={**ESTILO_INPUT, "minHeight": "72px"}),
    ], style=ESTILO_CAMPO),
    html.Div([html.Label("Impacto percebido", style=ESTILO_LABEL), dcc.Input(id="impacto_percebido_usuario", type="text", style=ESTILO_INPUT)], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Com que frequência isso acontece?", style=ESTILO_LABEL),
        dcc.Dropdown(id="frequencia_ocorrencia", options=[
            {"label": "Selecione", "value": ""},
            {"label": "Nunca", "value": "nunca"},
            {"label": "Raramente", "value": "raramente"},
            {"label": "Às vezes", "value": "as_vezes"},
            {"label": "Com frequência", "value": "com_frequencia"},
            {"label": "Sempre", "value": "sempre"},
        ], value="", clearable=True),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Urgência", style=ESTILO_LABEL),
        dcc.Dropdown(id="urgencia_percebida", options=[
            {"label": "Selecione", "value": ""}, {"label": "Baixa", "value": "baixa"},
            {"label": "Média", "value": "media"}, {"label": "Alta", "value": "alta"}, {"label": "Crítica", "value": "critica"},
        ], value="", clearable=True),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Existe alternativa temporária / contorno?", style=ESTILO_LABEL),
        html.Span("Descreva em texto livre, se houver.", style=ESTILO_APOIO),
        dcc.Textarea(id="ha_contorno", placeholder="Descreva um workaround ou deixe em branco.", style={**ESTILO_INPUT, "minHeight": "72px"}),
    ], style=ESTILO_CAMPO),
    html.Div([html.Label("Sistema ou produto relacionado", style=ESTILO_LABEL), dcc.Input(id="sistema_ou_produto", type="text", style=ESTILO_INPUT)], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Projeto vinculado", style=ESTILO_LABEL),
        html.Span(
            "Obrigatório: toda demanda fica vinculada a um projeto. Escolha um projeto existente ou cadastre um novo aqui. "
            "Ao salvar a priorização na matriz, a versão do projeto sobe automaticamente um patch.",
            style=ESTILO_APOIO,
        ),
        dcc.Dropdown(
            id="cadastro-id-projeto",
            options=[],
            value=None,
            placeholder="Selecione um projeto",
            clearable=False,
            style=ESTILO_INPUT,
        ),
        html.Button(
            "+ Adicionar novo projeto",
            id="btn-cadastro-novo-projeto",
            n_clicks=0,
            type="button",
            style={**ESTILO_BOTAO_SEC, "marginTop": f"{S*2}px"},
        ),
        html.Div(
            id="cad-proj-form-wrap",
            style={**_HIDE, "marginTop": f"{S*3}px", "padding": f"{S*3}px", "borderRadius": f"{R}px", "border": f"1px dashed {CORES['border']}", "backgroundColor": "#f8fafc"},
            children=[
                html.H4("Cadastrar novo projeto", style={"margin": f"0 0 {S*2}px 0", "fontSize": "1rem", "fontWeight": "600"}),
                dcc.RadioItems(
                    id="cad-proj-tipo-origem",
                    options=[
                        {"label": "Novo (inicia em 1.0.0)", "value": "novo"},
                        {"label": "Já operacional (informar versão atual)", "value": "existente"},
                    ],
                    value="novo",
                    style={"marginBottom": f"{S*2}px"},
                ),
                html.Div(id="cad-proj-hint-versao-novo", children=html.P("Versão inicial será 1.0.0.", style=ESTILO_APOIO)),
                html.Div(
                    id="cad-proj-wrap-versao-existente",
                    style=_HIDE,
                    children=[
                        html.Label("Versão atual (semver)", style=ESTILO_LABEL),
                        dcc.Input(id="cad-proj-versao-existente", type="text", placeholder="ex.: 2.4.0", style=ESTILO_INPUT),
                    ],
                ),
                html.Label("Nome do projeto", style=ESTILO_LABEL),
                dcc.Input(id="cad-proj-nome", type="text", placeholder="Ex.: Portal do cliente", style=ESTILO_INPUT),
                html.Label("Descrição / contexto inicial", style=ESTILO_LABEL),
                dcc.Textarea(
                    id="cad-proj-descricao",
                    placeholder="Objetivo do produto, escopo inicial, observações…",
                    style={**ESTILO_INPUT, "minHeight": "72px"},
                ),
                html.Label("Responsável pelo projeto", style=ESTILO_LABEL),
                dcc.Input(id="cad-proj-responsavel", type="text", placeholder="Nome ou equipe", style=ESTILO_INPUT),
                html.Label("Status do projeto", style=ESTILO_LABEL),
                dcc.Dropdown(id="cad-proj-status-cadastro", options=_OP_STATUS_PROJETO, value="ativo", clearable=False, style=ESTILO_INPUT),
                html.Button(
                    "Salvar e vincular à demanda",
                    id="btn-cadastro-salvar-projeto",
                    n_clicks=0,
                    type="button",
                    style={**ESTILO_BOTAO, "marginTop": f"{S*3}px"},
                ),
            ],
        ),
        html.Div(id="msg-cadastro-projeto", style={"fontSize": "0.875rem", "minHeight": "1.25em", "marginTop": f"{S}px"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Quem está solicitando?", style=ESTILO_LABEL),
        dcc.Dropdown(id="perfil_solicitante", options=PERFIL_SOLICITANTE_OPCOES_BASE, value="", clearable=True),
        html.Span("Não encontrou o perfil? Digite um nome e clique em Adicionar para incluir na lista desta sessão.", style={**ESTILO_APOIO, "display": "block", "marginTop": f"{S}px"}),
        html.Div([
            dcc.Input(id="cadastro-perfil-solicitante-novo", type="text", placeholder="Ex.: Product owner, Arquiteto…", style={**ESTILO_INPUT, "flex": "1", "minWidth": "140px"}),
            html.Button("Adicionar solicitante", id="btn-adicionar-perfil-solicitante", n_clicks=0, style={**ESTILO_BOTAO, "whiteSpace": "nowrap", "flexShrink": 0}),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "alignItems": "center", "marginTop": f"{S}px"}),
        html.Div(id="msg-perfil-solicitante-adicionar", style={"fontSize": "0.8125rem", "minHeight": "1.25em", "marginTop": f"{S//2}px"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Button("Analisar e estruturar com IA", id="btn-analisar", n_clicks=0, style=ESTILO_BOTAO, className="dash-button"),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "marginTop": f"{S*2}px"}),
    html.Div(id="msg-analise"),
], style=ESTILO_SECAO)


def _layout_cadastro():
    return html.Div([
        html.Header([
            html.H1("Priorização Inteligente de Requisitos", style={"textAlign": "center", "marginBottom": f"{S*2}px", "fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text"]}),
            html.P("Descreva a demanda, analise com IA e avalie para definir a prioridade.", style={"textAlign": "center", "color": CORES["text_muted"], "margin": 0, "fontSize": "0.9375rem"}),
        ], style={"marginBottom": f"{S*5}px"}),
        html.Div([layout_secao1], style={"maxWidth": "720px", "margin": "0 auto", "padding": f"0 {S*3}px"}),
        dcc.Store(id="store-analise"),
        dcc.Store(id="store-perfil-solicitante-extra", data=[]),
        dcc.Store(id="store-cad-proj-selecionar", data=None),
        html.Div(id="secao2-container", style={"maxWidth": "720px", "margin": "0 auto", "padding": f"0 {S*3}px"}),
        html.Div(id="secao3-container", style={"maxWidth": "720px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
        dcc.ConfirmDialog(id="confirm-salvo", message="Dados persistidos no banco de dados.", submit_n_clicks=0),
    ])


def _layout_atividades_corpo():
    op_tipo = [{"label": "Todos", "value": ""}, {"label": "BUG", "value": "BUG"}, {"label": "Incremento", "value": "INCREMENTO"}]
    op_status = [
        {"label": "Padrão (oculta concluídos)", "value": ""},
        {"label": "Todos os status", "value": "__all__"},
        {"label": "BACKLOG", "value": "BACKLOG"},
        {"label": "TO DO", "value": "TO_DO"},
        {"label": "DEVELOP", "value": "DEVELOP"},
        {"label": "TEST", "value": "TEST"},
        {"label": "DEPLOY", "value": "DEPLOY"},
        {"label": "DONE", "value": "DONE"},
        {"label": "AVALIADO", "value": "AVALIADO"},
        {"label": "Concluído", "value": "CONCLUIDO"},
    ]
    filtros = html.Div([
        html.H3("Filtros", style={"fontSize": "1.05rem", "marginBottom": f"{S*2}px"}),
        html.Div([
            html.Div([
                html.Label("Tipo", style=ESTILO_LABEL),
                dcc.Dropdown(id="ativ-filtro-tipo", options=op_tipo, value="", clearable=False),
            ], style={"flex": "1", "minWidth": "140px"}),
            html.Div([
                html.Label("Status", style=ESTILO_LABEL),
                dcc.Dropdown(id="ativ-filtro-status", options=op_status, value="", clearable=False),
            ], style={"flex": "2", "minWidth": "220px"}),
            html.Div([
                html.Label("Busca (título ou ID)", style=ESTILO_LABEL),
                dcc.Input(id="ativ-filtro-busca", type="text", debounce=True, placeholder="Trecho do título ou ID…", style=ESTILO_INPUT),
            ], style={"flex": "2", "minWidth": "180px"}),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px"}),
    ], style={**ESTILO_SECAO, "maxWidth": "900px", "margin": "0 auto", "marginBottom": f"{S*3}px", "padding": f"{S*3}px"})
    return [
        filtros,
        html.Div(id="atividades-resumo", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px", "marginBottom": f"{S*4}px"}),
        html.Div(id="atividades-grafico-bugs", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px", "marginBottom": f"{S*4}px"}),
        html.Div(id="atividades-grafico-incrementos", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px", "marginBottom": f"{S*4}px"}),
        html.Div(id="atividades-tabela", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
    ]


def _campo_calib(label, id_, ajuda="", readonly=False, min_val=None, max_val=None, default=None):
    ch = [html.Label(label, style=ESTILO_LABEL)]
    if ajuda:
        ch.append(html.Span(ajuda, style=ESTILO_APOIO))
    # readOnly em vez de disabled: inputs disabled não entram nos States dos callbacks no Dash.
    ch.append(dcc.Input(
        id=id_, type="number", placeholder="", style=ESTILO_INPUT_READONLY if readonly else ESTILO_INPUT,
        step=1, readOnly=readonly, min=min_val, max=max_val, value=default,
    ))
    return html.Div(ch, style=ESTILO_CAMPO)


def _layout_calibragem():
    bloco_v = html.Div([
        html.H3("Distribuição da fila entre bugs e melhorias", style={"fontSize": "1rem", "marginBottom": f"{S*2}px", "color": CORES["text"]}),
        html.P("Defina o percentual para bugs; melhorias completam 100%.", style=ESTILO_APOIO),
        _campo_calib("Percentual da fila para bugs", "calib-vazao-bugs", "", False, 0, 100, 50),
        _campo_calib("Percentual para melhorias", "calib-vazao-incrementos", "Calculado automaticamente.", True, None, None, 50),
    ], style={**ESTILO_SECAO, "maxWidth": "520px"})
    def _wip_row(lbl, dec_id, inp_id, inc_id, hint, v_def):
        return [
            html.Label(lbl, style=ESTILO_LABEL), html.Span(hint, style=ESTILO_APOIO),
            html.Div([
                html.Button("-", id=dec_id, n_clicks=0, style={**ESTILO_BOTAO, "padding": f"{S}px {S*2}px"}),
                dcc.Input(id=inp_id, type="number", style={**ESTILO_INPUT, "maxWidth": "120px"}, step=1, min=0, value=v_def),
                html.Button("+", id=inc_id, n_clicks=0, style={**ESTILO_BOTAO, "padding": f"{S}px {S*2}px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": f"{S}px", "marginBottom": f"{S*2}px"}),
        ]
    w = []
    w.extend(_wip_row("WIP — TO DO", "wip-todo-dec", "calib-wip-todo", "wip-todo-inc", "Sugestão: 5 a 8.", 5))
    w.extend(_wip_row("WIP — DEVELOP", "wip-develop-dec", "calib-wip-develop", "wip-develop-inc", "Sugestão: 2–3.", 2))
    w.extend(_wip_row("WIP — TEST", "wip-test-dec", "calib-wip-test", "wip-test-inc", "Sugestão: 2.", 2))
    w.extend(_wip_row("WIP — DEPLOY", "wip-deploy-dec", "calib-wip-deploy", "wip-deploy-inc", "Sugestão: 1.", 1))
    bloco_w = html.Div([html.H3("Limites WIP por coluna", style={"fontSize": "1rem", "marginBottom": f"{S*2}px"})] + w, style={**ESTILO_SECAO, "maxWidth": "520px"})
    return html.Div([
        html.Header([
            html.H1("Configuração da Fila de Prioridade", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text"]}),
            html.P("Ajuste vazão e WIP consumidos localmente (config_fila.json).", style={"textAlign": "center", "color": CORES["text_muted"], "fontSize": "0.9375rem"}),
        ], style={"marginBottom": f"{S*4}px"}),
        html.Div([bloco_v, bloco_w], style={"margin": "0 auto", "maxWidth": "560px"}),
        html.Div([
            html.Button("Salvar regras da fila", id="btn-salvar-calibragem", n_clicks=0, style=ESTILO_BOTAO),
            html.Div(id="msg-calibragem", style={"marginTop": f"{S*2}px"}),
        ], style={"maxWidth": "560px", "margin": "0 auto", "paddingBottom": f"{S*5}px"}),
        html.Div([
            dcc.Input(id="calib-env-intervalo", type="number", style={"display": "none"}),
            dcc.Input(id="calib-env-limite", type="number", style={"display": "none"}),
        ]),
    ])


def _layout_fila():
    return html.Div([
        html.Header([
            html.H1("Fila de priorização", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text"]}),
            html.P(
                "Ordem sugerida pela API com base em score, calibragem e vazão bugs/melhorias. Atualiza ao abrir esta página.",
                style={"textAlign": "center", "color": CORES["text_muted"], "fontSize": "0.9375rem", "marginBottom": 0},
            ),
        ], style={"marginBottom": f"{S*4}px"}),
        html.Div(id="fila-conteudo", style={"maxWidth": "960px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
    ])


def _layout_atividade_detalhe():
    return html.Div([
        html.Header([
            html.H1("Detalhe da atividade", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text"]}),
            html.P(
                "Hub operacional — leitura consolidada e espaço reservado para evidências por fase (escrita após contrato estável).",
                style={"textAlign": "center", "color": CORES["text_muted"], "fontSize": "0.9375rem", "marginBottom": 0},
            ),
        ], style={"marginBottom": f"{S*4}px"}),
        html.Div(id="atividade-detalhe-conteudo", style={"maxWidth": "1000px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
    ])


def _parse_atividade_id_path(path: str) -> int | None:
    m = re.match(r"^/atividade/(\d+)/?$", path or "")
    return int(m.group(1)) if m else None


def _store_merge_documentacao_fase(store_data: dict | None, fase_codigo: str, conteudo: str) -> dict:
    """Mantém o resto do store e substitui/atualiza só o texto da fase gravada (para o bloco 5 acompanhar sem F5)."""
    if not isinstance(store_data, dict):
        return {}
    out = {**store_data}
    prev = store_data.get("documentacao_fase")
    docs = {**(prev if isinstance(prev, dict) else {})}
    docs[str(fase_codigo)] = conteudo
    out["documentacao_fase"] = docs
    return out


def _montar_store_atividade_detalhe(aid: int) -> dict:
    out: dict = {
        "id": aid,
        "snapshot": None,
        "list_error": None,
        "not_found_in_list": False,
        "visao_360": None,
        "visao_360_error": None,
        "auditoria": None,
        "auditoria_error": None,
        "gates": None,
        "gates_error": None,
    }
    rows, err = api_listar_atividades()
    if err:
        out["list_error"] = err
    elif rows:
        for r in rows:
            try:
                if int(r.get("id", -1)) == int(aid):
                    out["snapshot"] = r
                    break
            except (TypeError, ValueError):
                continue
        if out["snapshot"] is None:
            out["not_found_in_list"] = True
    v360, e360 = api_get_visao_360_demanda(aid)
    out["visao_360"], out["visao_360_error"] = v360, e360
    aud, eaud = api_get_auditoria_demanda(aid)
    out["auditoria"], out["auditoria_error"] = aud, eaud
    gts, egts = api_get_kanban_gates_demanda(aid)
    out["gates"], out["gates_error"] = gts, egts
    docs, derr = api_obter_documentacao_fase(aid)
    out["documentacao_fase"] = docs if isinstance(docs, dict) else {}
    out["documentacao_fase_error"] = derr
    return out


def _atividade_meta_endpoint(nome: str, err: str | None):
    if err is None:
        return html.P(f"{nome}: dados recebidos da API.", style={**ESTILO_SUCESSO, "fontSize": "0.8125rem", "marginBottom": f"{S}px"})
    if err == EP_NOT_FOUND:
        return html.P(
            f"{nome}: endpoint não disponível neste workspace (HTTP 404). Quando o backend consolidado expuser a rota, este bloco passará a consumi-la.",
            style={**ESTILO_APOIO, "fontSize": "0.8125rem", "marginBottom": f"{S}px"},
        )
    return html.P(f"{nome}: {err}", style={**ESTILO_ERRO, "fontSize": "0.8125rem", "marginBottom": f"{S}px"})


def _atividade_kv(label: str, value):
    v = value if value is not None and str(value).strip() != "" else "—"
    return html.Div([
        html.Span(label, style={"fontWeight": "600", "color": CORES["text"]}),
        html.Span(f": {v}", style={"color": CORES["text"]}),
    ], style={"fontSize": "0.9rem", "marginBottom": f"{S}px"})


def _atividade_secao_titulo(num: str, texto: str):
    return html.Div([
        html.Span(num, style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "fontSize": "0.875rem", "marginRight": f"{S*2}px"}),
        html.H2(texto, style={"margin": 0, "fontSize": "1.15rem", "fontWeight": "700", "color": CORES["text"]}),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"})


def _atividade_bloco_wrap(num: str, titulo: str, children):
    return html.Div([_atividade_secao_titulo(num, titulo), *children], style={**ESTILO_SECAO, "marginBottom": f"{S*3}px"})


def _visao_subbloco(visao: dict | None, chaves: tuple[str, ...], titulo_fallback: str):
    """Exibe sub-objeto da visão 360 se existir, sem assumir contrato fixo."""
    if not isinstance(visao, dict):
        return None
    sub = visao
    for k in chaves:
        if not isinstance(sub, dict):
            return None
        sub = sub.get(k)
    if sub is None:
        return None
    label = " → ".join(chaves) if chaves else titulo_fallback
    if isinstance(sub, (dict, list)):
        try:
            txt = json.dumps(sub, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            txt = str(sub)
        if len(txt) > 4000:
            txt = txt[:4000] + "\n…"
        return html.Details([
            html.Summary(f"Dados visão 360 ({label})", style={"cursor": "pointer", "fontWeight": "600", "fontSize": "0.875rem"}),
            html.Pre(txt, style={"fontSize": "0.75rem", "overflowX": "auto", "background": "#f1f5f9", "padding": f"{S*2}px", "borderRadius": f"{R}px"}),
        ], style={"marginTop": f"{S*2}px"})
    return html.P(str(sub), style=ESTILO_APOIO)


def _render_atividade_auditoria(aud):
    if aud is None:
        return html.P("Sem dados de auditoria.", style=ESTILO_APOIO)
    rows = None
    if isinstance(aud, list):
        rows = aud
    elif isinstance(aud, dict):
        for k in ("eventos", "itens", "registros", "historico"):
            if isinstance(aud.get(k), list):
                rows = aud[k]
                break
        if rows is None:
            try:
                txt = json.dumps(aud, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                txt = str(aud)
            return html.Pre(txt[:5000], style={"fontSize": "0.75rem", "overflowX": "auto"})
    if rows is not None:
        if len(rows) == 0:
            return html.P("Nenhum registro de auditoria.", style=ESTILO_APOIO)
        if isinstance(rows[0], dict):
            keys = list(rows[0].keys())[:8]
            head = html.Tr([html.Th(str(k), style=ESTILO_TABELA) for k in keys])
            body = []
            for item in rows[:200]:
                if not isinstance(item, dict):
                    continue
                body.append(html.Tr([html.Td(str(item.get(k, ""))[:200], style=ESTILO_TABELA) for k in keys]))
            return html.Table([html.Thead(head), html.Tbody(body)], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.8125rem"})
        return html.Pre(json.dumps(rows, ensure_ascii=False, indent=2)[:4000], style={"fontSize": "0.75rem"})
    return html.Pre(str(aud)[:2000], style={"fontSize": "0.75rem"})


def _atividade_form_doc_fase(
    codigo: str,
    titulo: str,
    transicao: str,
    valor_inicial: str,
    id_atividade: int | None = None,
    fase_docs: dict | None = None,
):
    ta = {**ESTILO_INPUT, "minHeight": "120px", "width": "100%", "boxSizing": "border-box"}
    if codigo == "doc_requisito":
        cab, rf_l, rnf_l, reg_l, crit_l = parse_doc_requisito_completo(valor_inicial)
        est_btn_mais = {
            "padding": f"{S}px {S*2}px",
            "fontSize": "0.8125rem",
            "fontWeight": "600",
            "cursor": "pointer",
            "backgroundColor": CORES["surface"],
            "color": CORES["primary"],
            "border": f"1px solid {CORES['primary']}",
            "borderRadius": f"{R - 2}px",
            "marginTop": f"{S}px",
        }
        ta_cab = {**ESTILO_INPUT, "width": "100%", "boxSizing": "border-box"}
        ta_cab_grande = {**ta_cab, "minHeight": "100px"}
        return html.Div([
            html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
            html.P(
                f"Transição sugerida: {transicao}. Preencha o cabeçalho, as listas (mínimo um item não vazio em cada) e guarde.",
                style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
            ),
            html.Div(id="atividade-doc-gate-backlog"),
            html.P("Cabeçalho do documento de requisito", style={"fontWeight": "600", "marginTop": f"{S*2}px", "marginBottom": f"{S}px", "fontSize": "0.9rem"}),
            html.Label("Nome da funcionalidade", style=ESTILO_LABEL),
            dcc.Input(
                id="atividade-doc-nome-funcionalidade",
                value=cab.get("nome_funcionalidade") or "",
                type="text",
                style=ta_cab,
            ),
            html.Label("Descrição detalhada", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(
                id="atividade-doc-descricao-detalhada",
                value=cab.get("descricao_detalhada") or "",
                style=ta_cab_grande,
            ),
            html.Label("Restrições (use «Nenhuma» se não houver)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(
                id="atividade-doc-restricoes",
                value=cab.get("restricoes") or "",
                style=ta_cab_grande,
            ),
            html.Label("Requisitos funcionais (RF)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Store(id="atividade-doc-store-rf", data=rf_l),
            html.Div(id="atividade-doc-rf-rows"),
            html.Button("Adicionar mais um RF", id="atividade-doc-btn-add-rf", n_clicks=0, style=est_btn_mais),
            html.Label("Requisitos não funcionais (RNF)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Store(id="atividade-doc-store-rnf", data=rnf_l),
            html.Div(id="atividade-doc-rnf-rows"),
            html.Button("Adicionar mais um RNF", id="atividade-doc-btn-add-rnf", n_clicks=0, style=est_btn_mais),
            html.Label("Regras de negócio", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Store(id="atividade-doc-store-regras", data=reg_l),
            html.Div(id="atividade-doc-regras-rows"),
            html.Button("Adicionar mais uma regra", id="atividade-doc-btn-add-regras", n_clicks=0, style=est_btn_mais),
            html.Label("Critérios de aceitação", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Store(id="atividade-doc-store-criterios", data=crit_l),
            html.Div(id="atividade-doc-criterios-rows"),
            html.Button("Adicionar mais um critério", id="atividade-doc-btn-add-criterios", n_clicks=0, style=est_btn_mais),
            html.Button(
                "Guardar esta fase",
                id="atividade-doc-btn-requisito-tres-campos",
                n_clicks=0,
                style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
            ),
            html.Div(
                id="atividade-doc-msg-requisito-tres-campos",
                style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
            ),
        ], style={"padding": f"{S*2}px", "maxWidth": "100%"})
    if codigo == "prontidao_dev":
        pd = parse_prontidao_dev_conteudo(valor_inicial)
        ch_val = pd.get("checklist") if isinstance(pd.get("checklist"), list) else []
        ch_val = [x for x in ch_val if x in _PRONTIDAO_CHECKLIST_VALORES]
        data_iso = (pd.get("data_prontidao") or "").strip() or None
        ta_obs = {**ESTILO_INPUT, "minHeight": "120px", "width": "100%", "boxSizing": "border-box"}
        inp = {**ESTILO_INPUT, "width": "100%", "boxSizing": "border-box"}
        aid_txt = f"#{int(id_atividade)}" if id_atividade is not None else "—"
        return html.Div([
            html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
            html.P(
                f"Transição sugerida: {transicao}. Preencha os campos, marque os quatro itens do checklist e clique em «Guardar esta fase» para gravar na base. "
                "Enquanto não gravar, outras áreas (ex.: situação operacional) continuam a mostrar o último estado guardado.",
                style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
            ),
            html.Div(id="atividade-doc-gate-prontidao"),
            html.P(
                f"Documento de requisito (vínculo): requisito {aid_txt}",
                style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S*2}px"},
            ),
            html.Label("Responsável pelo desenvolvimento (nome ou identificador)", style=ESTILO_LABEL),
            dcc.Input(
                id="atividade-prontidao-responsavel",
                value=pd.get("responsavel_desenvolvimento") or "",
                type="text",
                style=inp,
            ),
            html.Label("Registado por (quem formaliza a prontidão)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Input(
                id="atividade-prontidao-registrado",
                value=pd.get("registrado_por") or "",
                type="text",
                style=inp,
            ),
            html.Label("Data da prontidão", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.DatePickerSingle(
                id="atividade-prontidao-data",
                date=data_iso,
                display_format="DD/MM/YYYY",
                first_day_of_week=1,
                style={"width": "100%", "marginBottom": f"{S}px"},
            ),
            html.Label("Observações técnicas (links, dependências, notas)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(
                id="atividade-prontidao-observacoes",
                value=pd.get("observacoes_tecnicas") or "",
                style=ta_obs,
            ),
            html.Label("Checklist de prontidão (obrigatório marcar todos para liberar o gate)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            html.P(
                "O item «Responsável… definido» conta como satisfeito se preencheu o campo «Responsável…» acima. "
                "«Critérios de aceitação…» conta como satisfeito se na aba BACKLOG existir pelo menos um critério de aceitação guardado.",
                style={**ESTILO_APOIO, "fontSize": "0.8125rem", "marginBottom": f"{S}px"},
            ),
            dcc.Checklist(
                id="atividade-prontidao-checklist",
                options=_PRONTIDAO_CHECKLIST_OPCOES,
                value=ch_val,
                style={"display": "flex", "flexDirection": "column", "gap": f"{S}px", "fontSize": "0.875rem"},
                labelStyle={"display": "flex", "alignItems": "flex-start", "cursor": "pointer"},
                inputStyle={"marginRight": f"{S}px", "marginTop": "2px"},
            ),
            html.Button(
                "Guardar esta fase",
                id="atividade-doc-btn-prontidao",
                n_clicks=0,
                style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
            ),
            html.Div(
                id="atividade-doc-msg-prontidao",
                style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
            ),
        ], style={"padding": f"{S*2}px", "maxWidth": "100%"})
    if codigo == "entrega_dev":
        ed = parse_entrega_dev_conteudo(valor_inicial)
        data_iso = (ed.get("data_entrega_teste") or "").strip() or None
        ta = {**ESTILO_INPUT, "minHeight": "88px", "width": "100%", "boxSizing": "border-box"}
        inp = {**ESTILO_INPUT, "width": "100%", "boxSizing": "border-box"}
        aid_txt = f"#{int(id_atividade)}" if id_atividade is not None else "—"
        return html.Div([
            html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
            html.P(
                f"Transição sugerida: {transicao}. Registe a entrega formal ao QA: o que foi feito, onde validar e referências de código.",
                style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
            ),
            html.Div(id="atividade-doc-gate-entrega"),
            html.P(
                f"Requisito {aid_txt} — entrega de desenvolvimento",
                style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S*2}px"},
            ),
            html.Label("Nome da funcionalidade / correção", style=ESTILO_LABEL),
            dcc.Input(id="atividade-entrega-nome", value=ed.get("nome_entrega") or "", type="text", style=inp),
            html.Label("O que foi desenvolvido", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(id="atividade-entrega-desenvolvido", value=ed.get("descricao_desenvolvido") or "", style=ta),
            html.Label("O que foi alterado (módulos, serviços, ecrãs…)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(id="atividade-entrega-alteracoes", value=ed.get("alteracoes") or "", style=ta),
            html.Label("O que deve ser validado (orientação ao QA)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(id="atividade-entrega-validacao", value=ed.get("validacao_qa") or "", style=ta),
            html.Label("Branch de referência", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Input(id="atividade-entrega-branch", value=ed.get("branch_referencia") or "", type="text", style=inp),
            html.Label("Commit de referência (hash ou link)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Input(id="atividade-entrega-commit", value=ed.get("commit_referencia") or "", type="text", style=inp),
            html.Label("Desenvolvedor (nome ou identificador)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Input(id="atividade-entrega-desenvolvedor", value=ed.get("desenvolvedor") or "", type="text", style=inp),
            html.Label("Data de entrega para teste", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.DatePickerSingle(
                id="atividade-entrega-data",
                date=data_iso,
                display_format="DD/MM/YYYY",
                first_day_of_week=1,
                style={"width": "100%", "marginBottom": f"{S}px"},
            ),
            html.Button(
                "Guardar esta fase",
                id="atividade-doc-btn-entrega-dev",
                n_clicks=0,
                style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
            ),
            html.Div(
                id="atividade-doc-msg-entrega-dev",
                style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
            ),
        ], style={"padding": f"{S*2}px", "maxWidth": "100%"})
    if codigo == "casos_teste":
        ct = parse_casos_teste_conteudo(valor_inicial)
        casos = ct.get("casos") if isinstance(ct.get("casos"), list) else [caso_teste_vazio()]
        if not casos:
            casos = [caso_teste_vazio()]
        est_btn_mais = {
            "padding": f"{S}px {S*2}px",
            "fontSize": "0.8125rem",
            "fontWeight": "600",
            "cursor": "pointer",
            "backgroundColor": CORES["surface"],
            "color": CORES["primary"],
            "border": f"1px solid {CORES['primary']}",
            "borderRadius": f"{R - 2}px",
            "marginTop": f"{S}px",
        }
        aid_txt = f"#{int(id_atividade)}" if id_atividade is not None else "—"
        return html.Div([
            html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
            html.P(
                f"Transição sugerida: {transicao}. Registe casos de teste com resultado e evidência; pelo menos um APROVADO completo libera o gate.",
                style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
            ),
            html.Div(id="atividade-doc-gate-casos-teste"),
            html.P(
                f"Requisito {aid_txt} — casos de teste",
                style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S*2}px"},
            ),
            dcc.Store(id="atividade-doc-store-casos-teste", data=casos),
            html.Div(id="atividade-doc-casos-teste-rows"),
            html.Button("Adicionar caso de teste", id="atividade-doc-btn-add-caso-teste", n_clicks=0, style=est_btn_mais),
            html.Button(
                "Guardar esta fase",
                id="atividade-doc-btn-casos-teste",
                n_clicks=0,
                style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
            ),
            html.Div(
                id="atividade-doc-msg-casos-teste",
                style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
            ),
        ], style={"padding": f"{S*2}px", "maxWidth": "100%"})
    if codigo == "deploy":
        dep = parse_deploy_conteudo(valor_inicial)
        data_iso = (dep.get("data_deploy") or "").strip() or None
        ta = {**ESTILO_INPUT, "minHeight": "100px", "width": "100%", "boxSizing": "border-box"}
        inp = {**ESTILO_INPUT, "width": "100%", "boxSizing": "border-box"}
        aid_txt = f"#{int(id_atividade)}" if id_atividade is not None else "—"
        return html.Div([
            html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
            html.P(
                f"Transição sugerida: {transicao}. Registe a implantação: versão, ambiente, data e responsável.",
                style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
            ),
            html.Div(id="atividade-doc-gate-deploy"),
            html.P(
                f"Requisito {aid_txt} — registo de deploy",
                style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S*2}px"},
            ),
            html.Label("Versão entregue (release / tag)", style=ESTILO_LABEL),
            dcc.Input(id="atividade-deploy-versao", value=dep.get("versao_entregue") or "", type="text", style=inp),
            html.Label("Ambiente (ex.: produção, homologação, staging)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Input(id="atividade-deploy-ambiente", value=dep.get("ambiente") or "", type="text", style=inp),
            html.Label("Data do deploy", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.DatePickerSingle(
                id="atividade-deploy-data",
                date=data_iso,
                display_format="DD/MM/YYYY",
                first_day_of_week=1,
                style={"width": "100%", "marginBottom": f"{S}px"},
            ),
            html.Label("Responsável pelo deploy (nome ou identificador)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Input(id="atividade-deploy-responsavel", value=dep.get("responsavel_deploy") or "", type="text", style=inp),
            html.Label("Observações (opcional: pipeline, URL, rollback…)", style={**ESTILO_LABEL, "marginTop": f"{S*2}px"}),
            dcc.Textarea(id="atividade-deploy-observacoes", value=dep.get("observacoes") or "", style=ta),
            html.Button(
                "Guardar esta fase",
                id="atividade-doc-btn-deploy",
                n_clicks=0,
                style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
            ),
            html.Div(
                id="atividade-doc-msg-deploy",
                style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
            ),
        ], style={"padding": f"{S*2}px", "maxWidth": "100%"})
    if codigo == "encerramento":
        fd = fase_docs if isinstance(fase_docs, dict) else {}
        ta_enc = {**ESTILO_INPUT, "minHeight": "160px", "width": "100%", "boxSizing": "border-box"}
        return html.Div(
            [
                html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
                html.P(
                    f"Transição sugerida: {transicao}. Em primeiro lugar vê o resumo do que foi guardado de BACKLOG a DEPLOY; em seguida regista notas de encerramento.",
                    style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
                ),
                _render_resumo_documentacao_ate_deploy(fd),
                html.P(
                    "Encerramento (lições aprendidas, comunicação, notas finais)",
                    style={"fontWeight": "600", "marginTop": f"{S*3}px", "marginBottom": f"{S}px", "fontSize": "0.9rem"},
                ),
                dcc.Textarea(
                    id={"type": "atividade-doc-ta", "fase": codigo},
                    value=valor_inicial or "",
                    style=ta_enc,
                ),
                html.Button(
                    "Guardar esta fase",
                    id={"type": "atividade-doc-btn", "fase": codigo},
                    n_clicks=0,
                    style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
                ),
                html.Div(
                    id={"type": "atividade-doc-msg", "fase": codigo},
                    style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
                ),
            ],
            style={"padding": f"{S*2}px", "maxWidth": "100%"},
        )
    return html.Div([
        html.P(titulo, style={"fontWeight": "600", "marginBottom": f"{S}px", "fontSize": "0.95rem", "color": CORES["text"]}),
        html.P(
            f"Transição sugerida: {transicao}. Use este espaço para RF/RNF, links, critérios de aceite e notas que sustentem o avanço no Kanban.",
            style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
        ),
        dcc.Textarea(
            id={"type": "atividade-doc-ta", "fase": codigo},
            value=valor_inicial or "",
            style={**ESTILO_INPUT, "minHeight": "180px", "width": "100%", "boxSizing": "border-box"},
        ),
        html.Button(
            "Guardar esta fase",
            id={"type": "atividade-doc-btn", "fase": codigo},
            n_clicks=0,
            style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"},
        ),
        html.Div(
            id={"type": "atividade-doc-msg", "fase": codigo},
            style={"fontSize": "0.8125rem", "marginTop": f"{S}px", "minHeight": "1.25em"},
        ),
    ], style={"padding": f"{S*2}px", "maxWidth": "100%"})


def _render_atividade_gates(gates):
    if gates is None:
        return html.P("Sem payload de gates.", style=ESTILO_APOIO)
    try:
        txt = json.dumps(gates, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        txt = str(gates)
    return html.Pre(txt[:6000], style={"fontSize": "0.8125rem", "overflowX": "auto", "background": "#f8fafc", "padding": f"{S*2}px", "borderRadius": f"{R}px"})


def _doc_resumo_linhas_lista(label_itens: str, items) -> html.Div | html.P:
    limpo = [str(x).strip() for x in (items or []) if str(x).strip()]
    if not limpo:
        return html.P(f"{label_itens}: —", style={**ESTILO_APOIO, "marginBottom": f"{S}px", "fontSize": "0.8125rem"})
    return html.Div(
        [
            html.P(
                label_itens,
                style={
                    "fontWeight": "600",
                    "fontSize": "0.75rem",
                    "color": CORES["text_muted"],
                    "marginBottom": f"{S // 2}px",
                    "textTransform": "uppercase",
                },
            ),
            html.Ul([html.Li(x, style={"fontSize": "0.8125rem"}) for x in limpo], style={"marginBottom": f"{S * 2}px", "paddingLeft": f"{S * 3}px"}),
        ]
    )


def _doc_resumo_campo_texto(label: str, valor) -> html.Div | html.P:
    v = (valor or "").strip() if valor is not None else ""
    if not v:
        return html.P(
            [html.Span(f"{label}: ", style={"fontWeight": "600", "fontSize": "0.8125rem"}), html.Span("—", style=ESTILO_APOIO)],
            style={"marginBottom": f"{S}px"},
        )
    return html.Div(
        [
            html.P(
                label,
                style={
                    "fontWeight": "600",
                    "fontSize": "0.75rem",
                    "color": CORES["text_muted"],
                    "marginBottom": f"{S // 2}px",
                },
            ),
            html.Div(v, style={"fontSize": "0.8125rem", "whiteSpace": "pre-wrap", "marginBottom": f"{S * 2}px"}),
        ]
    )


def _render_resumo_documentacao_ate_deploy(fase_docs: dict | None) -> html.Div:
    """Leitura consolidada do que foi gravado de BACKLOG a DEPLOY (só leitura)."""
    fd = fase_docs if isinstance(fase_docs, dict) else {}
    wrap = {"marginBottom": f"{S * 3}px", "paddingBottom": f"{S * 2}px", "borderBottom": f"1px solid {CORES['border']}"}
    tit = {"fontWeight": "700", "fontSize": "0.9rem", "marginBottom": f"{S * 2}px", "color": CORES["primary"]}

    secoes: list = []

    cab, rf, rnf, rg, crit = parse_doc_requisito_completo(fd.get("doc_requisito") or "")
    vazio_dr = not any(
        [
            (cab.get("nome_funcionalidade") or "").strip(),
            (cab.get("descricao_detalhada") or "").strip(),
            (cab.get("restricoes") or "").strip(),
            *[str(x).strip() for x in rf],
            *[str(x).strip() for x in rnf],
            *[str(x).strip() for x in rg],
            *[str(x).strip() for x in crit],
        ]
    )
    bl0 = [html.P(f"{KANBAN_COLUNAS[0]} — documento de requisito", style=tit)]
    if vazio_dr:
        bl0.append(html.P("Nada guardado nesta fase.", style=ESTILO_APOIO))
    else:
        bl0.extend(
            [
                _doc_resumo_campo_texto("Nome da funcionalidade", cab.get("nome_funcionalidade")),
                _doc_resumo_campo_texto("Descrição detalhada", cab.get("descricao_detalhada")),
                _doc_resumo_campo_texto("Restrições", cab.get("restricoes")),
                _doc_resumo_linhas_lista("Requisitos funcionais (RF)", rf),
                _doc_resumo_linhas_lista("Requisitos não funcionais (RNF)", rnf),
                _doc_resumo_linhas_lista("Regras de negócio", rg),
                _doc_resumo_linhas_lista("Critérios de aceitação", crit),
            ]
        )
    secoes.append(html.Div(bl0, style=wrap))

    pr = parse_prontidao_dev_conteudo(fd.get("prontidao_dev") or "")
    ch = pr.get("checklist") if isinstance(pr.get("checklist"), list) else []
    rot_ch = {o["value"]: o["label"].strip() for o in _PRONTIDAO_CHECKLIST_OPCOES}
    ch_txt = ", ".join(rot_ch.get(str(x), str(x)) for x in ch if str(x).strip())
    vazio_p = not any(
        [
            (pr.get("responsavel_desenvolvimento") or "").strip(),
            (pr.get("registrado_por") or "").strip(),
            (pr.get("data_prontidao") or "").strip(),
            (pr.get("observacoes_tecnicas") or "").strip(),
            ch_txt,
        ]
    )
    bl1 = [html.P(f"{KANBAN_COLUNAS[1]} — prontidão para desenvolvimento", style=tit)]
    if vazio_p:
        bl1.append(html.P("Nada guardado nesta fase.", style=ESTILO_APOIO))
    else:
        bl1.extend(
            [
                _doc_resumo_campo_texto("Responsável pelo desenvolvimento", pr.get("responsavel_desenvolvimento")),
                _doc_resumo_campo_texto("Registado por", pr.get("registrado_por")),
                _doc_resumo_campo_texto("Data da prontidão", pr.get("data_prontidao")),
                _doc_resumo_campo_texto("Observações técnicas", pr.get("observacoes_tecnicas")),
                _doc_resumo_campo_texto("Checklist", ch_txt or None),
            ]
        )
    secoes.append(html.Div(bl1, style=wrap))

    ed = parse_entrega_dev_conteudo(fd.get("entrega_dev") or "")
    vazio_e = not any(
        [
            (ed.get("nome_entrega") or "").strip(),
            (ed.get("descricao_desenvolvido") or "").strip(),
            (ed.get("alteracoes") or "").strip(),
            (ed.get("validacao_qa") or "").strip(),
            (ed.get("branch_referencia") or "").strip(),
            (ed.get("commit_referencia") or "").strip(),
            (ed.get("desenvolvedor") or "").strip(),
            (ed.get("data_entrega_teste") or "").strip(),
        ]
    )
    bl2 = [html.P(f"{KANBAN_COLUNAS[2]} — entrega de desenvolvimento", style=tit)]
    if vazio_e:
        bl2.append(html.P("Nada guardado nesta fase.", style=ESTILO_APOIO))
    else:
        bl2.extend(
            [
                _doc_resumo_campo_texto("Nome / correção", ed.get("nome_entrega")),
                _doc_resumo_campo_texto("O que foi desenvolvido", ed.get("descricao_desenvolvido")),
                _doc_resumo_campo_texto("O que foi alterado", ed.get("alteracoes")),
                _doc_resumo_campo_texto("O que validar (QA)", ed.get("validacao_qa")),
                _doc_resumo_campo_texto("Branch", ed.get("branch_referencia")),
                _doc_resumo_campo_texto("Commit", ed.get("commit_referencia")),
                _doc_resumo_campo_texto("Desenvolvedor", ed.get("desenvolvedor")),
                _doc_resumo_campo_texto("Data entrega para teste", ed.get("data_entrega_teste")),
            ]
        )
    secoes.append(html.Div(bl2, style=wrap))

    ct = parse_casos_teste_conteudo(fd.get("casos_teste") or "")
    casos = ct.get("casos") if isinstance(ct.get("casos"), list) else []


    def _caso_preenc(x: dict) -> bool:
        return any(
            str(x.get(k) or "").strip()
            for k in (
                "resumo",
                "passos",
                "resultado_esperado",
                "resultado_obtido",
                "executor",
                "data_execucao",
                "evidencia",
            )
        ) or str(x.get("status") or "").strip().upper() not in ("", "PENDENTE")

    casos_com_dados = [c for c in casos if isinstance(c, dict) and _caso_preenc(c)]
    bl3 = [html.P(f"{KANBAN_COLUNAS[3]} — casos de teste", style=tit)]
    if not casos_com_dados:
        bl3.append(html.P("Nada guardado nesta fase.", style=ESTILO_APOIO))
    else:
        for j, c in enumerate(casos_com_dados):
            bl3.append(html.P(f"Caso {j + 1}", style={"fontWeight": "600", "fontSize": "0.8125rem", "marginTop": f"{S}px"}))
            bl3.extend(
                [
                    _doc_resumo_campo_texto("Resumo", c.get("resumo")),
                    _doc_resumo_campo_texto("Passos", c.get("passos")),
                    _doc_resumo_campo_texto("Resultado esperado", c.get("resultado_esperado")),
                    _doc_resumo_campo_texto("Resultado obtido", c.get("resultado_obtido")),
                    _doc_resumo_campo_texto("Status", c.get("status")),
                    _doc_resumo_campo_texto("Executor", c.get("executor")),
                    _doc_resumo_campo_texto("Data de execução", c.get("data_execucao")),
                    _doc_resumo_campo_texto("Evidência", c.get("evidencia")),
                ]
            )
    secoes.append(html.Div(bl3, style=wrap))

    dep = parse_deploy_conteudo(fd.get("deploy") or "")
    vazio_d = not any(
        [
            (dep.get("versao_entregue") or "").strip(),
            (dep.get("ambiente") or "").strip(),
            (dep.get("data_deploy") or "").strip(),
            (dep.get("responsavel_deploy") or "").strip(),
            (dep.get("observacoes") or "").strip(),
        ]
    )
    bl4 = [html.P(f"{KANBAN_COLUNAS[4]} — deploy", style=tit)]
    if vazio_d:
        bl4.append(html.P("Nada guardado nesta fase.", style=ESTILO_APOIO))
    else:
        bl4.extend(
            [
                _doc_resumo_campo_texto("Versão entregue", dep.get("versao_entregue")),
                _doc_resumo_campo_texto("Ambiente", dep.get("ambiente")),
                _doc_resumo_campo_texto("Data do deploy", dep.get("data_deploy")),
                _doc_resumo_campo_texto("Responsável", dep.get("responsavel_deploy")),
                _doc_resumo_campo_texto("Observações", dep.get("observacoes")),
            ]
        )
    secoes.append(html.Div(bl4, style={**wrap, "borderBottom": "none", "marginBottom": 0, "paddingBottom": 0}))

    return html.Div(
        [
            html.P(
                "Resumo da documentação (BACKLOG → DEPLOY)",
                style={
                    "fontWeight": "700",
                    "fontSize": "1rem",
                    "color": CORES["text"],
                    "marginBottom": f"{S}px",
                    "paddingBottom": f"{S}px",
                    "borderBottom": f"2px solid {CORES['primary']}",
                },
            ),
            html.P(
                "Leitura do que já está gravado na base. Para alterar, use as abas de cada fase.",
                style={**ESTILO_APOIO, "marginBottom": f"{S * 2}px"},
            ),
            html.Div(
                secoes,
                style={
                    "padding": f"{S * 2}px",
                    "backgroundColor": "#f8fafc",
                    "borderRadius": f"{R}px",
                    "border": f"1px solid {CORES['border']}",
                },
            ),
        ],
        style={"marginBottom": f"{S * 2}px"},
    )


def _render_atividade_detalhe_conteudo(data: dict | None):
    if not data:
        return html.P("Carregue uma atividade a partir da lista, fila ou Kanban.", style={"color": CORES["text_muted"]})
    if data.get("parse_error"):
        return html.Div([
            html.P(data.get("message", "URL inválida."), style=ESTILO_ERRO),
            dcc.Link("← Voltar ao cadastro", href="/", style=ESTILO_NAV_LINK),
        ])
    aid = data.get("id")
    snap = data.get("snapshot") or {}
    if data.get("list_error"):
        return html.Div([
            html.P(f"Não foi possível carregar atividades: {data['list_error']}", style=ESTILO_ERRO),
            dcc.Link("← Tentar início", href="/", style=ESTILO_NAV_LINK),
        ])

    blocos = [
        html.Div([
            dcc.Link("← Atividades", href="/atividades", style={**ESTILO_NAV_LINK, "display": "inline-block", "marginRight": f"{S*2}px"}),
            dcc.Link("Fila", href="/fila", style={**ESTILO_NAV_LINK, "display": "inline-block", "marginRight": f"{S*2}px"}),
            dcc.Link("Kanban", href="/kanban", style={**ESTILO_NAV_LINK, "display": "inline-block", "marginRight": f"{S*2}px"}),
            dcc.Link("Lista esteira", href="/kanban-lista", style=ESTILO_NAV_LINK),
        ], style={"marginBottom": f"{S*3}px"}),
    ]

    if data.get("not_found_in_list") and not snap:
        blocos.append(html.Div(f"Requisito #{aid} não aparece em GET /api/v1/requisitos/atividades (pode estar fora do conjunto ou ID inválido).", style=ESTILO_ERRO))

    tipo = (snap.get("tipo_requisito") or "").upper()
    eixos = ("Criticidade × Severidade") if tipo == "BUG" else ("Esforço × Valor") if tipo in ("INCREMENTO", "FEATURE") else "—"
    col_k = status_atual_para_coluna_kanban(snap.get("status_atual")) if snap else "—"
    prox = KANBAN_NEXT.get(col_k, "—") if col_k in KANBAN_COLUNAS else "—"

    visao = data.get("visao_360")
    blocos.append(_atividade_bloco_wrap("1", "Identificação da atividade", [
        _atividade_kv("ID", aid),
        _atividade_kv("Título", snap.get("titulo")),
        _atividade_kv("Descrição", snap.get("descricao_requisito") or snap.get("descricao")),
        _atividade_kv("Tipo", snap.get("tipo_requisito")),
        _atividade_kv("Status atual", snap.get("status_atual")),
        _atividade_kv("Fase Kanban (mapeada)", col_k),
        _atividade_kv("Projeto", snap.get("nome_projeto")),
        _atividade_kv("Versão do projeto", snap.get("versao_projeto")),
        _atividade_kv("Módulo", snap.get("modulo_afetado")),
        _atividade_kv("Solicitante / perfil", snap.get("perfil_solicitante") or snap.get("usuario_avaliador")),
        _atividade_kv("Data principal (avaliação)", snap.get("data_avaliacao")),
        html.P(
            "Campos não listados (texto original, módulo, datas completas, etc.) não vêm em GET /api/v1/requisitos/atividades — aguardam visão 360 ou endpoint de detalhe.",
            style={**ESTILO_APOIO, "marginTop": f"{S*2}px", "marginBottom": 0},
        ),
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("identificacao",), "identificacao"),
    ]))

    blocos.append(_atividade_meta_endpoint("Visão 360 (GET …/demandas/{id}/visao-360)", data.get("visao_360_error")))

    blocos.append(_atividade_bloco_wrap("2", "Origem da demanda", [
        _atividade_kv("Texto original", snap.get("texto_original")),
        _atividade_kv("Contexto", snap.get("contexto_negocio")),
        _atividade_kv("Objetivo desejado", snap.get("objetivo_desejado")),
        _atividade_kv("Impacto", snap.get("impacto_percebido_usuario")),
        _atividade_kv("Frequência", snap.get("frequencia_ocorrencia")),
        _atividade_kv("Urgência", snap.get("urgencia_percebida")),
        _atividade_kv("Contorno", snap.get("ha_contorno")),
        _atividade_kv("Sistema / produto", snap.get("sistema_ou_produto")),
        _atividade_kv("Perfil solicitante", snap.get("perfil_solicitante")),
        html.P("Sem estes campos na lista resumida da API atual.", style=ESTILO_APOIO) if not isinstance(visao, dict) else None,
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("origem_demanda",), "origem"),
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("entrada",), "entrada"),
    ]))

    blocos.append(_atividade_bloco_wrap("3", "Estruturação da IA", [
        _atividade_kv("Título sugerido", snap.get("titulo")),
        _atividade_kv("Descrição estruturada", snap.get("descricao_requisito")),
        _atividade_kv("Tipo identificado", snap.get("tipo_requisito")),
        _atividade_kv("Objetivo", snap.get("objetivo")),
        _atividade_kv("Finalidade", snap.get("finalidade")),
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("estruturacao_ia",), "estruturacao_ia"),
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("requisito_estruturado",), "requisito"),
    ]))

    blocos.append(_atividade_bloco_wrap("4", "Avaliação e plotagem", [
        _atividade_kv("coordenada_x", snap.get("coordenada_x")),
        _atividade_kv("coordenada_y", snap.get("coordenada_y")),
        _atividade_kv("Eixos (conforme tipo)", eixos),
        _atividade_kv("Quadrante", "— (não exposto pelo endpoint atual de atividades)"),
        _atividade_kv("score (matriz)", snap.get("score")),
        _atividade_kv("score_base / bônus fila", "— (ver GET /api/v1/fila/bugs e /api/v1/fila/incrementos para itens na fila)"),
        _atividade_kv("Prioridade categórica", snap.get("prioridade_categorica")),
        html.P(
            "Perguntas e respostas da avaliação não são retornadas por GET /api/v1/requisitos/atividades.",
            style={**ESTILO_APOIO, "marginTop": f"{S}px"},
        ),
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("avaliacao",), "avaliacao"),
        _visao_subbloco(visao if isinstance(visao, dict) else None, ("respostas",), "respostas"),
    ]))

    fase_docs = data.get("documentacao_fase") if isinstance(data.get("documentacao_fase"), dict) else {}
    blocos.append(_atividade_bloco_wrap("5", "Situação operacional", [
        _atividade_kv("Fase atual (Kanban)", col_k),
        _atividade_kv("Próxima coluna sugerida", prox),
        *_render_situacao_documentacao_kanban(col_k, prox, fase_docs),
        html.Hr(style={"margin": f"{S*2}px 0", "border": "none", "borderTop": f"1px solid {CORES['border']}"}),
        html.P(
            "Gates operacionais do backend (quando existirem) — independente da documentação gravada acima:",
            style={"fontWeight": "600", "fontSize": "0.8125rem", "color": CORES["text_muted"], "marginBottom": f"{S}px"},
        ),
        _atividade_meta_endpoint("Gates (GET …/kanban/{id}/gates)", data.get("gates_error")),
        html.Div(_render_atividade_gates(data.get("gates")), style={"marginTop": f"{S*2}px"}),
    ]))
    doc_err = data.get("documentacao_fase_error")
    tabs_doc = dcc.Tabs(
        [
            dcc.Tab(
                label=lab,
                children=html.Div(
                    _atividade_form_doc_fase(cod, tit, trans, fase_docs.get(cod, "") or "", aid, fase_docs),
                    style={"padding": 0},
                ),
            )
            for cod, lab, tit, trans in _ATIVIDADE_DOC_FASES_UI
        ],
        style={"marginBottom": f"{S*2}px"},
    )
    blocos.append(_atividade_bloco_wrap("6", "Documentação por fase", [
        html.P(
            "Preencha cada aba e clique em «Guardar esta fase». Os textos ficam na base (PostgreSQL) e servem como registo para avançar no Kanban.",
            style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"},
        ),
        html.P(doc_err, style=ESTILO_ERRO) if doc_err else None,
        _render_resumo_documentacao_ate_deploy(fase_docs),
        tabs_doc,
    ]))

    blocos.append(_atividade_meta_endpoint("Auditoria (GET …/demandas/{id}/auditoria)", data.get("auditoria_error")))
    blocos.append(_atividade_bloco_wrap("7", "Auditoria", [
        html.P("Movimentações, tentativas bloqueadas e responsáveis — conforme payload da API.", style={**ESTILO_APOIO, "marginBottom": f"{S*2}px"}),
        _render_atividade_auditoria(data.get("auditoria")),
    ]))

    if isinstance(visao, dict) and data.get("visao_360_error") is None:
        try:
            raw = json.dumps(visao, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            raw = str(visao)
        if len(raw) > 120:
            blocos.append(html.Details([
                html.Summary("JSON completo — visão 360 (referência até mapeamento fino)", style={"cursor": "pointer", "fontSize": "0.875rem"}),
                html.Pre(raw[:8000] + ("…" if len(raw) > 8000 else ""), style={"fontSize": "0.72rem", "overflowX": "auto"}),
            ], style={"marginTop": f"{S*2}px"}))

    return html.Div([b for b in blocos if b is not None])


def _layout_kanban():
    col_style = {
        "flex": "1", "minWidth": "220px", "backgroundColor": CORES["surface"], "borderRadius": f"{R}px",
        "border": f"1px solid {CORES['border']}", "padding": f"{S*2}px",
    }
    cols = [html.Div([html.Div(id=f"kanban-col-{t}", style={"display": "flex", "flexDirection": "column", "gap": f"{S}px"})], style=col_style) for t in KANBAN_COLUNAS]
    return html.Div([
        html.Header([
            html.H1("Esteira Kanban de Requisitos", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text"]}),
            html.P(
                "Colunas BACKLOG → TO DO → DEVELOP → TEST → DEPLOY → DONE. «Avançar» exige documentação gravada da fase atual (Detalhe da atividade) e respeita WIP da Calibragem. Persistência via API.",
                style={"textAlign": "center", "color": CORES["text_muted"], "fontSize": "0.9375rem"},
            ),
        ], style={"marginBottom": f"{S*4}px"}),
        html.Div(id="kanban-msg", style={"marginBottom": f"{S*2}px", "fontSize": "0.8125rem"}),
        html.Div(
            dcc.Link("Ver todas as atividades da esteira em lista", href="/kanban-lista", style={"fontSize": "0.875rem", "color": CORES["primary"]}),
            style={"textAlign": "center", "marginBottom": f"{S*3}px"},
        ),
        html.Div(cols, style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "alignItems": "flex-start"}),
    ])


def _layout_kanban_lista():
    return html.Div([
        html.Header([
            html.H1("Atividades na esteira Kanban", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text"]}),
            html.P(
                "Lista única das mesmas atividades do quadro, ordenadas por fase (BACKLOG → … → DONE). "
                "Dados: GET /api/v1/requisitos/atividades.",
                style={"textAlign": "center", "color": CORES["text_muted"], "fontSize": "0.9375rem", "marginBottom": 0},
            ),
        ], style={"marginBottom": f"{S*4}px"}),
        html.Div([
            dcc.Link("← Quadro Kanban", href="/kanban", style={**ESTILO_NAV_LINK, "display": "inline-block", "marginRight": f"{S*2}px"}),
            dcc.Link("Atividades priorizadas", href="/atividades", style=ESTILO_NAV_LINK),
        ], style={"maxWidth": "1100px", "margin": f"0 auto {S*2}px", "padding": f"0 {S*3}px"}),
        html.Div(id="kanban-lista-conteudo", style={"maxWidth": "1100px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
    ])


def _layout_projetos():
    op_st = _OP_STATUS_PROJETO
    return html.Div([
        html.Header([
            html.H1("Projetos e versões", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700"}),
            html.P("Cadastro, evolução semântica, status e histórico.", style={"textAlign": "center", "color": CORES["text_muted"]}),
        ], style={"marginBottom": f"{S*4}px"}),
        html.Div([
            html.H3("Cadastrar projeto", style={"fontSize": "1.05rem"}),
            dcc.RadioItems(id="proj-tipo-origem", options=[{"label": "Novo (inicia em 1.0.0)", "value": "novo"}, {"label": "Já operacional (informar versão atual)", "value": "existente"}], value="novo", style={"marginBottom": f"{S*2}px"}),
            html.Div(id="proj-hint-versao-novo", children=html.P("Versão inicial será 1.0.0.", style=ESTILO_APOIO)),
            html.Div(id="proj-wrap-versao-existente", style=_HIDE, children=[
                html.Label("Versão atual (semver)", style=ESTILO_LABEL),
                dcc.Input(id="proj-versao-existente", type="text", placeholder="ex.: 2.4.0", style=ESTILO_INPUT),
            ]),
            html.Label("Nome do projeto", style=ESTILO_LABEL),
            dcc.Input(id="proj-nome", type="text", style=ESTILO_INPUT),
            html.Label("Descrição", style=ESTILO_LABEL),
            dcc.Textarea(id="proj-descricao", style={**ESTILO_INPUT, "minHeight": "64px"}),
            html.Label("Responsável", style=ESTILO_LABEL),
            dcc.Input(id="proj-responsavel", type="text", style=ESTILO_INPUT),
            html.Label("Status inicial", style=ESTILO_LABEL),
            dcc.Dropdown(id="proj-status-cadastro", options=op_st, value="ativo", clearable=False),
            html.Button("Salvar projeto", id="btn-salvar-projeto", n_clicks=0, style={**ESTILO_BOTAO, "marginTop": f"{S*2}px"}),
        ], style={**ESTILO_SECAO, "maxWidth": "640px", "margin": "0 auto"}),
        html.Div([
            html.H3("Evoluir versão", style={"fontSize": "1.05rem"}),
            html.Label("Projeto", style=ESTILO_LABEL),
            dcc.Dropdown(id="proj-evoluir-id", options=[], clearable=False),
            html.P(
                "Nível fixo: MAJOR (próxima versão X+1.0.0). Patch e minor não estão disponíveis neste fluxo.",
                style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": f"{S*2}px"},
            ),
            html.Label("Motivo (opcional)", style=ESTILO_LABEL),
            dcc.Input(id="proj-evoluir-motivo", type="text", style=ESTILO_INPUT),
            html.Label("Usuário responsável (opcional)", style=ESTILO_LABEL),
            dcc.Input(id="proj-evoluir-usuario", type="text", style=ESTILO_INPUT),
            html.Button("Aplicar evolução", id="btn-proj-evoluir", n_clicks=0, style=ESTILO_BOTAO),
        ], style={**ESTILO_SECAO, "maxWidth": "640px", "margin": f"{S*4}px auto 0"}),
        html.Div(id="proj-msg", style={"maxWidth": "640px", "margin": f"{S*2}px auto"}),
        html.Div([
            html.H3("Projetos cadastrados", style={"fontSize": "1.05rem"}),
            html.Div([
                html.Div([
                    html.Label("Filtro origem", style=ESTILO_LABEL),
                    dcc.Dropdown(id="proj-filtro-origem", options=[
                        {"label": "Todas", "value": ""}, {"label": "novo", "value": "novo"}, {"label": "existente", "value": "existente"},
                    ], value="", clearable=False),
                ], style={"flex": "1", "minWidth": "140px"}),
                html.Div([
                    html.Label("Filtro status", style=ESTILO_LABEL),
                    dcc.Dropdown(id="proj-filtro-status", options=[{"label": "Todos", "value": ""}] + op_st, value="", clearable=False),
                ], style={"flex": "1", "minWidth": "140px"}),
                html.Div([
                    html.Label("Busca nome", style=ESTILO_LABEL),
                    dcc.Input(id="proj-busca-nome", type="text", debounce=True, placeholder="nome...", style=ESTILO_INPUT),
                ], style={"flex": "2", "minWidth": "180px"}),
            ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px"}),
            html.Div(id="proj-tabela", style={"marginTop": f"{S*3}px", "overflowX": "auto"}),
        ], style={**ESTILO_SECAO, "maxWidth": "1000px", "margin": f"{S*4}px auto"}),
        html.Div([
            html.H3("Alterar status do projeto", style={"fontSize": "1.05rem"}),
            dcc.Dropdown(id="proj-alterar-status-id", options=[], placeholder="Projeto", style=ESTILO_INPUT),
            dcc.Dropdown(id="proj-alterar-status-novo", options=op_st, value="ativo", clearable=False),
            html.Button("Atualizar status", id="btn-proj-alterar-status", n_clicks=0, style=ESTILO_BOTAO),
        ], style={**ESTILO_SECAO, "maxWidth": "640px", "margin": f"{S*4}px auto {S*6}px"}),
    ])


def _nav_link(label, href):
    return dcc.Link(html.Div([html.Span(label)], style={"display": "flex", "alignItems": "center"}), href=href, style=ESTILO_NAV_LINK)


def _nav_link_sub(label, href):
    """Link secundário (indentado), ex.: lista da esteira logo abaixo do quadro Kanban."""
    st = {**ESTILO_NAV_LINK, "paddingLeft": f"{S*5}px", "fontSize": "0.875rem", "marginTop": f"-{S}px"}
    return dcc.Link(html.Div([html.Span(label)], style={"display": "flex", "alignItems": "center"}), href=href, style=st)


_sidebar_inner = html.Div([
    html.Div("Navegação", style={"fontSize": "0.75rem", "fontWeight": "700", "color": CORES["text_muted"], "textTransform": "uppercase", "letterSpacing": "0.05em", "marginBottom": f"{S*2}px", "paddingLeft": f"{S*3}px"}),
    _nav_link("Cadastro", "/"),
    _nav_link("Atividades priorizadas", "/atividades"),
    _nav_link("Esteira Kanban", "/kanban"),
    _nav_link_sub("Lista da esteira (tabela)", "/kanban-lista"),
    _nav_link("Projetos", "/projetos"),
    _nav_link("Fila", "/fila"),
    _nav_link("Calibragem", "/calibragem"),
    html.Hr(style={"margin": f"{S*3}px 0", "border": "none", "borderTop": f"1px solid {CORES['border']}"}),
    html.Div([
        html.P(f"Versão {version_info.__version__}", style={"fontSize": "0.75rem", "color": CORES["text_muted"], "margin": 0}),
        html.P(f"Release {version_info.format_release_date_br(version_info.RELEASE_DATE)}", style={"fontSize": "0.75rem", "color": CORES["text_muted"], "margin": f"{S//2}px 0 0 0"}),
        html.P("MAJOR / MINOR / PATCH — governança semântica.", style={"fontSize": "0.7rem", "color": CORES["text_muted"], "margin": f"{S}px 0 0 0", "lineHeight": "1.3"}),
    ], style={"paddingLeft": f"{S*2}px"}),
])


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="store-atividades"),
    dcc.Store(id="store-calibragem"),
    dcc.Store(id="store-kanban", data=[]),
    dcc.Store(id="store-kanban-docs"),
    dcc.Store(id="store-fila"),
    dcc.Store(id="store-atividade-detalhe"),
    dcc.Store(id="store-kanban-lista"),
    dcc.Store(id="store-sidebar-open", data=True),
    dcc.Store(id="store-proj-reload", data=0),
    html.Div([
        html.Div(id="sidebar-wrapper", children=_sidebar_inner, style=ESTILO_SIDEBAR),
        html.Div([
            html.Div(html.Button("☰", id="btn-toggle-sidebar", n_clicks=0, title="Mostrar/ocultar navegação", style={"border": "none", "background": "transparent", "cursor": "pointer", "fontSize": "1.25rem", "padding": 0}), style={"marginBottom": f"{S}px"}),
            html.Div(id="cadastro-wrapper", children=_layout_cadastro()),
            html.Div(id="atividades-wrapper", style=_HIDE, children=[
                html.Header([
                    html.H1("Atividades Priorizadas", style={"textAlign": "center", "fontSize": "1.75rem", "fontWeight": "700"}),
                    html.P("Matrizes de priorização e lista.", style={"textAlign": "center", "color": CORES["text_muted"]}),
                ], style={"marginBottom": f"{S*4}px"}),
                *_layout_atividades_corpo(),
            ]),
            html.Div(id="calibragem-wrapper", style=_HIDE, children=_layout_calibragem()),
            html.Div(id="kanban-wrapper", style=_HIDE, children=_layout_kanban()),
            html.Div(id="kanban-lista-wrapper", style=_HIDE, children=_layout_kanban_lista()),
            html.Div(id="projetos-wrapper", style=_HIDE, children=_layout_projetos()),
            html.Div(id="fila-wrapper", style=_HIDE, children=_layout_fila()),
            html.Div(id="atividade-wrapper", style=_HIDE, children=_layout_atividade_detalhe()),
        ], style=ESTILO_MAIN),
    ], style={"display": "flex", "flex": 1, "minHeight": 0, "alignItems": "stretch"}),
], style=ESTILO_APP)

_CALIB_INPUTS = [
    ("calib-vazao-bugs", "vazao", "bugs"),
    ("calib-vazao-incrementos", "vazao", "incrementos"),
    ("calib-env-intervalo", "envelhecimento", "intervalo_dias"),
    ("calib-env-limite", "envelhecimento", "limite_maximo"),
    ("calib-wip-todo", "wip", "TO_DO"),
    ("calib-wip-develop", "wip", "DEVELOP"),
    ("calib-wip-test", "wip", "TEST"),
    ("calib-wip-deploy", "wip", "DEPLOY"),
]


@app.callback(
    [
        Output("cadastro-wrapper", "style"),
        Output("atividades-wrapper", "style"),
        Output("calibragem-wrapper", "style"),
        Output("kanban-wrapper", "style"),
        Output("projetos-wrapper", "style"),
        Output("fila-wrapper", "style"),
        Output("atividade-wrapper", "style"),
        Output("kanban-lista-wrapper", "style"),
        Output("store-atividades", "data"),
        Output("store-calibragem", "data"),
        Output("store-kanban", "data"),
        Output("kanban-msg", "children"),
        Output("store-fila", "data"),
        Output("store-atividade-detalhe", "data"),
        Output("store-kanban-lista", "data"),
    ],
    Input("url", "pathname"),
    State("store-kanban", "data"),
)
def _router(pathname, _kanban_state):
    path = pathname or "/"
    aid = _parse_atividade_id_path(path)
    if aid is not None:
        payload = _montar_store_atividade_detalhe(aid)
        return _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _SHOW, _HIDE, no_update, no_update, no_update, no_update, no_update, payload, no_update
    if path.startswith("/atividade/"):
        bad = {"parse_error": True, "message": "ID de atividade inválido na URL. Use /atividade/<número>."}
        return _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _SHOW, _HIDE, no_update, no_update, no_update, no_update, no_update, bad, no_update
    if path == "/atividades":
        data, _e = api_listar_atividades()
        pl = data if data is not None else []
        return _HIDE, _SHOW, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, pl, no_update, no_update, no_update, no_update, no_update, no_update
    if path == "/calibragem":
        try:
            cfg = get_config_fila()
        except Exception:
            cfg = {}
        return _HIDE, _HIDE, _SHOW, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, no_update, cfg, no_update, no_update, no_update, no_update, no_update
    if path == "/kanban":
        data, _e = api_listar_atividades()
        items = data if data is not None else []
        k_items = []
        for it in items:
            st = status_atual_para_coluna_kanban(it.get("status_atual"))
            k_items.append({**it, "status_kanban": st, "last_next_clicks": 0, "last_prev_clicks": 0})
        return _HIDE, _HIDE, _HIDE, _SHOW, _HIDE, _HIDE, _HIDE, _HIDE, no_update, no_update, k_items, "", no_update, no_update, no_update
    if path == "/kanban-lista":
        data, err = api_listar_atividades()
        if err:
            lista_payload = {"items": [], "error": err}
        else:
            enriched = []
            for it in data or []:
                col = status_atual_para_coluna_kanban(it.get("status_atual"))
                enriched.append({**it, "coluna_kanban": col})

            def _sort_key(x):
                ck = x.get("coluna_kanban") or "BACKLOG"
                try:
                    idx = KANBAN_COLUNAS.index(ck)
                except ValueError:
                    idx = 99
                return (idx, (x.get("titulo") or "").lower())

            enriched.sort(key=_sort_key)
            lista_payload = {"items": enriched, "error": None}
        return _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _SHOW, no_update, no_update, no_update, no_update, no_update, no_update, lista_payload
    if path == "/projetos":
        return _HIDE, _HIDE, _HIDE, _HIDE, _SHOW, _HIDE, _HIDE, _HIDE, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    if path == "/fila":
        fila_data, err = api_obter_fila_duas()
        if err:
            fila_payload = {"bugs": None, "features": None, "incrementos": None, "error": err}
        else:
            fd = fila_data or {}
            features = fd.get("features")
            incrementos = fd.get("incrementos")
            if not isinstance(features, list):
                features = incrementos if isinstance(incrementos, list) else []
            fila_payload = {
                "bugs": fd.get("bugs") if isinstance(fd.get("bugs"), list) else [],
                "features": features,
                "incrementos": incrementos if isinstance(incrementos, list) else features,
                "error": None,
            }
        return _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _SHOW, _HIDE, _HIDE, no_update, no_update, no_update, no_update, fila_payload, no_update, no_update
    return _SHOW, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, _HIDE, no_update, no_update, no_update, no_update, no_update, no_update, no_update


def _fila_tabela_head():
    return html.Tr([
        html.Th("Pos.", style=ESTILO_TABELA), html.Th("ID", style=ESTILO_TABELA), html.Th("Título", style=ESTILO_TABELA),
        html.Th("Tipo", style=ESTILO_TABELA), html.Th("Prioridade", style=ESTILO_TABELA), html.Th("Status", style=ESTILO_TABELA),
        html.Th("Score final", style=ESTILO_TABELA), html.Th("Faixa", style=ESTILO_TABELA), html.Th("Dias parado", style=ESTILO_TABELA),
        html.Th("Detalhe", style=ESTILO_TABELA),
    ])


def _fila_tabela_body(items):
    body = []
    for i, it in enumerate(items, start=1):
        _iid = it.get("id")
        body.append(html.Tr([
            html.Td(i, style=ESTILO_TABELA),
            html.Td(_iid, style=ESTILO_TABELA),
            html.Td((it.get("titulo") or "")[:56], style=ESTILO_TABELA),
            html.Td(it.get("tipo_requisito"), style=ESTILO_TABELA),
            html.Td(it.get("prioridade_categorica"), style=ESTILO_TABELA),
            html.Td(it.get("status_atual"), style=ESTILO_TABELA),
            html.Td(it.get("score_final"), style=ESTILO_TABELA),
            html.Td(it.get("faixa"), style=ESTILO_TABELA),
            html.Td(it.get("dias_parado"), style=ESTILO_TABELA),
            html.Td(dcc.Link("Abrir", href=f"/atividade/{_iid}", style={"color": CORES["primary"], "fontSize": "0.8125rem"}), style=ESTILO_TABELA),
        ]))
    return body


def _render_fila_secao(titulo: str, items: list):
    head = _fila_tabela_head()
    body = _fila_tabela_body(items)
    return html.Div([
        html.H2(titulo, style={"fontSize": "1.125rem", "fontWeight": "600", "color": CORES["text"], "marginBottom": f"{S}px", "marginTop": 0}),
        html.P(f"Total: {len(items)}", style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S*2}px"}),
        html.Table([html.Thead(head), html.Tbody(body)], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.875rem"}),
    ], style={**ESTILO_SECAO, "marginBottom": f"{S*4}px"})


def _render_fila_conteudo(payload):
    if payload is None:
        return html.P("Use o link Fila no menu para carregar a priorização da API.", style={"color": CORES["text_muted"], "fontSize": "0.9375rem"})
    err = payload.get("error")
    if err:
        return html.Div(err, style=ESTILO_ERRO)
    bugs = payload.get("bugs")
    features = payload.get("features")
    if not isinstance(features, list):
        features = payload.get("incrementos")
    if bugs is None or features is None:
        items_legado = payload.get("items")
        if items_legado is not None:
            return _render_fila_secao("Fila (legado)", items_legado)
        return html.Div("Resposta inválida da API.", style=ESTILO_ERRO)
    if len(bugs) == 0 and len(features) == 0:
        return html.Div([
            html.P("Nenhum item elegível na fila no momento.", style={"color": CORES["text_muted"], "fontSize": "0.9375rem"}),
            html.P("Isso pode ocorrer se não houver atividades para priorizar ou se os filtros da API estiverem vazios.", style={**ESTILO_APOIO, "marginTop": f"{S}px"}),
        ], style=ESTILO_SECAO)
    blocos = []
    blocos.append(_render_fila_secao("Fila de bugs", bugs))
    blocos.append(_render_fila_secao("Fila de features", features))
    return html.Div(blocos)


def _render_kanban_lista_conteudo(data):
    if data is None:
        return html.P("Use o menu «Lista da esteira» para carregar as atividades.", style={"color": CORES["text_muted"], "fontSize": "0.9375rem"})
    err = data.get("error")
    if err:
        return html.Div(err, style=ESTILO_ERRO)
    items = data.get("items") or []
    contagem_por_fase = {c: 0 for c in KANBAN_COLUNAS}
    for it in items:
        ck = it.get("coluna_kanban")
        if ck in contagem_por_fase:
            contagem_por_fase[ck] += 1
    chips = html.Div([
        html.Span(
            [html.Strong(f"{c}: "), str(contagem_por_fase[c])],
            style={
                "display": "inline-block",
                "marginRight": f"{S*3}px",
                "marginBottom": f"{S}px",
                "padding": f"{S}px {S*2}px",
                "backgroundColor": "#f1f5f9",
                "borderRadius": f"{R}px",
                "fontSize": "0.8125rem",
            },
        )
        for c in KANBAN_COLUNAS
    ], style={"marginBottom": f"{S*3}px", "flexWrap": "wrap"})
    if not items:
        return html.Div([
            chips,
            html.P("Nenhuma atividade na esteira (lista vazia da API).", style=ESTILO_APOIO),
        ], style=ESTILO_SECAO)
    head = html.Tr([
        html.Th("Fase (Kanban)", style=ESTILO_TABELA),
        html.Th("Status (API)", style=ESTILO_TABELA),
        html.Th("ID", style=ESTILO_TABELA),
        html.Th("Título", style=ESTILO_TABELA),
        html.Th("Tipo", style=ESTILO_TABELA),
        html.Th("Prioridade", style=ESTILO_TABELA),
        html.Th("Score", style=ESTILO_TABELA),
        html.Th("Projeto", style=ESTILO_TABELA),
        html.Th("Detalhe", style=ESTILO_TABELA),
    ])
    body = []
    for it in items:
        _iid = it.get("id")
        body.append(html.Tr([
            html.Td(it.get("coluna_kanban") or "—", style=ESTILO_TABELA),
            html.Td(it.get("status_atual") or "—", style=ESTILO_TABELA),
            html.Td(_iid, style=ESTILO_TABELA),
            html.Td((it.get("titulo") or "")[:52], style=ESTILO_TABELA),
            html.Td(it.get("tipo_requisito"), style=ESTILO_TABELA),
            html.Td(it.get("prioridade_categorica"), style=ESTILO_TABELA),
            html.Td(it.get("score"), style=ESTILO_TABELA),
            html.Td((it.get("nome_projeto") or "")[:28] or "—", style=ESTILO_TABELA),
            html.Td(dcc.Link("Abrir", href=f"/atividade/{_iid}", style={"color": CORES["primary"], "fontSize": "0.8125rem"}), style=ESTILO_TABELA),
        ]))
    return html.Div([
        html.P(f"Total na esteira: {len(items)}", style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S*2}px"}),
        chips,
        html.Div([html.Table([html.Thead(head), html.Tbody(body)], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.875rem"})], style={"overflowX": "auto"}),
    ], style=ESTILO_SECAO)


@app.callback(Output("fila-conteudo", "children"), Input("store-fila", "data"))
def _render_fila_view(data):
    return _render_fila_conteudo(data)


@app.callback(Output("atividade-detalhe-conteudo", "children"), Input("store-atividade-detalhe", "data"))
def _render_atividade_detalhe_view(data):
    return _render_atividade_detalhe_conteudo(data)


@app.callback(
    Output("store-atividade-detalhe", "data", allow_duplicate=True),
    Input("btn-atividade-atualizar-doc-store", "n_clicks"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def _atividade_atualizar_doc_store_desde_api(n_clicks, pathname):
    if not n_clicks:
        return no_update
    aid = _parse_atividade_id_path(pathname or "")
    if aid is None:
        return no_update
    return _montar_store_atividade_detalhe(aid)


def _render_doc_backlog_gate_children(nome, desc, restr, vrf, vrnf, vrg, vcrit):
    falta = []
    if not (nome or "").strip():
        falta.append("Nome da funcionalidade")
    if not (desc or "").strip():
        falta.append("Descrição detalhada")
    if not (restr or "").strip():
        falta.append("Restrições (ou «Nenhuma»)")
    if not _doc_lista_tem_item_preenchido(vrf):
        falta.append("Pelo menos um requisito funcional (RF)")
    if not _doc_lista_tem_item_preenchido(vrnf):
        falta.append("Pelo menos um requisito não funcional (RNF)")
    if not _doc_lista_tem_item_preenchido(vrg):
        falta.append("Pelo menos uma regra de negócio")
    if not _doc_lista_tem_item_preenchido(vcrit):
        falta.append("Pelo menos um critério de aceitação")
    box = {"borderRadius": f"{R}px", "padding": f"{S * 2}px", "marginBottom": f"{S * 2}px", "border": f"1px solid {CORES['border']}"}
    if not falta:
        return html.Div(
            [
                html.P("Gate BACKLOG → TO DO: liberado", style={"fontWeight": "700", "color": CORES["success"], "marginBottom": f"{S}px"}),
                html.P(
                    "Pacote mínimo de formalização preenchido (revise antes de avançar no Kanban).",
                    style={**ESTILO_APOIO, "marginBottom": 0},
                ),
            ],
            style={**box, "backgroundColor": "#f0fdf4", "borderColor": "#86efac"},
        )
    return html.Div(
        [
            html.P("Gate BACKLOG → TO DO: bloqueado", style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px"}),
            html.P("Ainda falta:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px", "color": CORES["text"]}),
            html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
            html.P(
                "Sem este pacote a API não aceita avançar o cartão na esteira.",
                style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": 0},
            ),
        ],
        style={**box, "backgroundColor": "#fffbeb", "borderColor": "#fcd34d"},
    )


def _render_prontidao_gate_children(responsavel, registrado, data_pront, checklist_vals, documentacao_fase=None):
    falta = []
    if not (responsavel or "").strip():
        falta.append("Responsável pelo desenvolvimento")
    if not (registrado or "").strip():
        falta.append("Registado por")
    if not data_pront:
        falta.append("Data da prontidão")
    sel = set(checklist_vals or [])
    resp_txt = (responsavel or "").strip()
    rotulos = {o["value"]: o["label"].strip() for o in _PRONTIDAO_CHECKLIST_OPCOES}
    for k in _PRONTIDAO_CHECKLIST_VALORES:
        if k in sel:
            continue
        if k == "responsavel_definido" and resp_txt:
            continue
        if k == "criterios_existem" and _doc_requisito_criterios_ok(documentacao_fase):
            continue
        falta.append(rotulos.get(k, k))
    box = {"borderRadius": f"{R}px", "padding": f"{S * 2}px", "marginBottom": f"{S * 2}px", "border": f"1px solid {CORES['border']}"}
    if not falta:
        return html.Div(
            [
                html.P("Gate TO DO → DEVELOP: liberado", style={"fontWeight": "700", "color": CORES["success"], "marginBottom": f"{S}px"}),
                html.P(
                    "Prontidão mínima registada no formulário (guarde para persistir na base).",
                    style={**ESTILO_APOIO, "marginBottom": 0},
                ),
            ],
            style={**box, "backgroundColor": "#f0fdf4", "borderColor": "#86efac"},
        )
    return html.Div(
        [
            html.P("Gate TO DO → DEVELOP: bloqueado", style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px"}),
            html.P("Ainda falta:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px", "color": CORES["text"]}),
            html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
            html.P(
                "Sem este pacote a API não aceita avançar o cartão na esteira.",
                style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": 0},
            ),
        ],
        style={**box, "backgroundColor": "#fffbeb", "borderColor": "#fcd34d"},
    )


def _render_entrega_dev_gate_children(nome, desc_dev, alter, valid, branch, commit, dev, data_ent):
    checks = [
        ((nome or "").strip(), "Nome da funcionalidade / correção"),
        ((desc_dev or "").strip(), "O que foi desenvolvido"),
        ((alter or "").strip(), "O que foi alterado"),
        ((valid or "").strip(), "O que deve ser validado (QA)"),
        ((branch or "").strip(), "Branch de referência"),
        ((commit or "").strip(), "Commit de referência"),
        ((dev or "").strip(), "Desenvolvedor (quem entregou)"),
        (bool(data_ent), "Data de entrega para teste"),
    ]
    falta = [label for ok, label in checks if not ok]
    box = {"borderRadius": f"{R}px", "padding": f"{S * 2}px", "marginBottom": f"{S * 2}px", "border": f"1px solid {CORES['border']}"}
    if not falta:
        return html.Div(
            [
                html.P("Gate DEVELOP → TEST: liberado", style={"fontWeight": "700", "color": CORES["success"], "marginBottom": f"{S}px"}),
                html.P(
                    "Entrega mínima descrita para o QA (guarde para persistir na base).",
                    style={**ESTILO_APOIO, "marginBottom": 0},
                ),
            ],
            style={**box, "backgroundColor": "#f0fdf4", "borderColor": "#86efac"},
        )
    return html.Div(
        [
            html.P("Gate DEVELOP → TEST: bloqueado", style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px"}),
            html.P("Ainda falta:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px", "color": CORES["text"]}),
            html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
            html.P(
                "Sem este pacote a API não aceita avançar o cartão na esteira.",
                style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": 0},
            ),
        ],
        style={**box, "backgroundColor": "#fffbeb", "borderColor": "#fcd34d"},
    )


def _render_deploy_gate_children(versao, ambiente, data_dep, responsavel):
    falta = []
    if not (versao or "").strip():
        falta.append("Versão entregue")
    if not (ambiente or "").strip():
        falta.append("Ambiente (ex.: produção, homologação, staging)")
    if not data_dep:
        falta.append("Data do deploy")
    if not (responsavel or "").strip():
        falta.append("Responsável pelo deploy")
    box = {"borderRadius": f"{R}px", "padding": f"{S * 2}px", "marginBottom": f"{S * 2}px", "border": f"1px solid {CORES['border']}"}
    if not falta:
        return html.Div(
            [
                html.P("Gate DEPLOY → DONE: liberado", style={"fontWeight": "700", "color": CORES["success"], "marginBottom": f"{S}px"}),
                html.P(
                    "Registo mínimo de implantação preenchido (guarde para persistir na base).",
                    style={**ESTILO_APOIO, "marginBottom": 0},
                ),
            ],
            style={**box, "backgroundColor": "#f0fdf4", "borderColor": "#86efac"},
        )
    return html.Div(
        [
            html.P("Gate DEPLOY → DONE: bloqueado", style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px"}),
            html.P("Ainda falta:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px", "color": CORES["text"]}),
            html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
            html.P(
                "Sem este pacote a API não aceita avançar o cartão na esteira.",
                style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": 0},
            ),
        ],
        style={**box, "backgroundColor": "#fffbeb", "borderColor": "#fcd34d"},
    )


def _all_idx(lst, i: int) -> str:
    if not lst or i >= len(lst):
        return ""
    v = lst[i]
    if v is None:
        return ""
    return str(v)


def _casos_teste_list_from_all_states(r, pas, esp, obt, sts, exe, dts, evi):
    lists = [r or [], pas or [], esp or [], obt or [], sts or [], exe or [], dts or [], evi or []]
    n = max((len(x) for x in lists), default=0)
    out = []
    for i in range(n):
        st = _all_idx(sts, i).strip().upper()
        if st not in ("APROVADO", "REPROVADO", "PENDENTE"):
            st = "PENDENTE"
        dt = _all_idx(dts, i).strip()
        out.append(
            {
                "resumo": _all_idx(r, i).strip(),
                "passos": _all_idx(pas, i).strip(),
                "resultado_esperado": _all_idx(esp, i).strip(),
                "resultado_obtido": _all_idx(obt, i).strip(),
                "status": st,
                "executor": _all_idx(exe, i).strip(),
                "data_execucao": dt,
                "evidencia": _all_idx(evi, i).strip(),
            }
        )
    return out


_DOC_FASE_LABEL_ABA: dict[str, str] = {c: lab for c, lab, _, _ in _ATIVIDADE_DOC_FASES_UI}


def _render_situacao_documentacao_kanban(col_k: str, prox: str, fase_docs: dict | None) -> list:
    """Painel da secção 5: liberação documental para a próxima coluna, com base no JSON gravado."""
    fd = fase_docs if isinstance(fase_docs, dict) else {}
    box_ok = {
        "borderRadius": f"{R}px",
        "padding": f"{S * 2}px",
        "marginTop": f"{S}px",
        "border": "1px solid #86efac",
        "backgroundColor": "#f0fdf4",
    }
    box_bloq = {
        "borderRadius": f"{R}px",
        "padding": f"{S * 2}px",
        "marginTop": f"{S}px",
        "border": "1px solid #fcd34d",
        "backgroundColor": "#fffbeb",
    }
    out: list = [
        html.P(
            "Próxima baia — requisitos documentais (dados gravados)",
            style={
                "fontWeight": "700",
                "fontSize": "0.95rem",
                "marginTop": f"{S * 2}px",
                "marginBottom": f"{S // 2}px",
                "color": CORES["text"],
            },
        ),
        html.P(
            "As caixas dentro de cada aba atualizam-se enquanto edita; este resumo segue o que está na base. "
            "Após «Guardar esta fase», o resumo abaixo atualiza automaticamente; use o botão para reler tudo da API se precisar.",
            style={**ESTILO_APOIO, "fontSize": "0.8125rem", "marginBottom": f"{S}px"},
        ),
        html.Button(
            "Atualizar documentação da API",
            id="btn-atividade-atualizar-doc-store",
            n_clicks=0,
            style={**ESTILO_BOTAO, "fontSize": "0.8125rem", "padding": f"{S}px {S * 2}px", "backgroundColor": CORES["surface"], "color": CORES["primary"], "border": f"1px solid {CORES['primary']}"},
        ),
    ]
    if col_k == "DONE":
        out.append(
            html.Div(
                [
                    html.P(
                        "Última coluna da esteira — não há «próxima baia» no Kanban.",
                        style={"fontWeight": "600", "marginBottom": f"{S}px", "color": CORES["text"], "fontSize": "0.875rem"},
                    ),
                    html.P(
                        "O encerramento na aba DONE é opcional (lições aprendidas, comunicação).",
                        style={**ESTILO_APOIO, "marginBottom": 0, "fontSize": "0.8125rem"},
                    ),
                ],
                style={**box_ok, "marginTop": f"{S * 2}px"},
            )
        )
        return out
    if col_k not in _COLUNA_PARA_DOC_GATE:
        out.append(
            html.P(
                "Não foi possível mapear a coluna Kanban — sem avaliação documental automática.",
                style={**ESTILO_APOIO, "fontSize": "0.8125rem"},
            )
        )
        return out
    cod, rotulo = _COLUNA_PARA_DOC_GATE[col_k]
    raw = fd.get(cod) or ""
    extra_linhas: list = []
    if cod == "doc_requisito":
        ok, falta = _eval_fase_docs_doc_requisito_gate(raw)
    elif cod == "prontidao_dev":
        ok, falta = _eval_fase_docs_prontidao_gate(raw, fd)
    elif cod == "entrega_dev":
        ok, falta = _eval_fase_docs_entrega_gate(raw)
    elif cod == "deploy":
        ok, falta = _eval_fase_docs_deploy_gate(raw)
    else:
        ok, falta, n_casos, aprov = _eval_fase_docs_casos_teste_gate(raw)
        extra_linhas = [
            html.P(f"Casos registados: {n_casos}", style={"fontSize": "0.8125rem", "marginBottom": f"{S // 2}px"}),
            html.P(
                f"Aprovados com evidência completa: {aprov}",
                style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "marginBottom": f"{S}px"},
            ),
        ]
    if ok:
        out.append(
            html.Div(
                extra_linhas
                + [
                    html.P(
                        f"Gate {rotulo}: liberado (documentação gravada).",
                        style={"fontWeight": "700", "color": CORES["success"], "marginBottom": f"{S}px", "fontSize": "0.9rem"},
                    ),
                    html.P(
                        f"Pode considerar-se pronto, do ponto de vista documental, para avançar o cartão para «{prox}». "
                        "O movimento real no quadro continua a depender da API, WIP e regras do projeto.",
                        style={**ESTILO_APOIO, "marginBottom": 0, "fontSize": "0.8125rem"},
                    ),
                ],
                style=box_ok,
            )
        )
    else:
        out.append(
            html.Div(
                extra_linhas
                + [
                    html.P(
                        f"Gate {rotulo}: bloqueado — falta completar a documentação desta fase.",
                        style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px", "fontSize": "0.9rem"},
                    ),
                    html.P("Ainda falta:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px", "color": CORES["text"]}),
                    html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
                    html.P(
                        f"Aba «{_DOC_FASE_LABEL_ABA.get(cod, cod)}» — use «Guardar esta fase» quando terminar.",
                        style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": 0, "fontSize": "0.8125rem"},
                    ),
                ],
                style=box_bloq,
            )
        )
    return out


def _render_casos_teste_gate_children(r, pas, esp, obt, sts, exe, dts, evi):
    n = max(
        len(r or []),
        len(pas or []),
        len(esp or []),
        len(obt or []),
        len(sts or []),
        len(exe or []),
        len(dts or []),
        len(evi or []),
    )
    aprov_ok = 0
    for i in range(n):
        if _caso_linha_aprovada_completa(
            _all_idx(r, i),
            _all_idx(pas, i),
            _all_idx(esp, i),
            _all_idx(obt, i),
            _all_idx(sts, i),
            _all_idx(exe, i),
            _all_idx(dts, i),
            _all_idx(evi, i),
        ):
            aprov_ok += 1
    box = {"borderRadius": f"{R}px", "padding": f"{S * 2}px", "marginBottom": f"{S * 2}px", "border": f"1px solid {CORES['border']}"}
    resumo_linhas = [
        html.P(f"Casos registados: {n}", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px"}),
        html.P(
            f"Aprovados com evidência completa: {aprov_ok}",
            style={"fontSize": "0.875rem", "color": CORES["text_muted"], "marginBottom": f"{S}px"},
        ),
    ]
    if n == 0:
        return html.Div(
            resumo_linhas
            + [
                html.P("Gate TEST → DEPLOY: bloqueado", style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px"}),
                html.P("Adicione pelo menos um caso de teste e preencha os campos.", style={**ESTILO_APOIO, "marginBottom": 0}),
            ],
            style={**box, "backgroundColor": "#fffbeb", "borderColor": "#fcd34d"},
        )
    if aprov_ok >= 1:
        return html.Div(
            resumo_linhas
            + [
                html.P("Gate TEST → DEPLOY: liberado", style={"fontWeight": "700", "color": CORES["success"], "marginBottom": f"{S}px"}),
                html.P(
                    "Existe pelo menos um caso APROVADO com registo completo (guarde para persistir na base).",
                    style={**ESTILO_APOIO, "marginBottom": 0},
                ),
            ],
            style={**box, "backgroundColor": "#f0fdf4", "borderColor": "#86efac"},
        )
    falta = [
        "Pelo menos um caso com status APROVADO",
        "Todos os campos obrigatórios preenchidos (resumo, passos, esperado, obtido, executor, data)",
        "Evidência ou observação do teste (campo Evidência)",
    ]
    return html.Div(
        resumo_linhas
        + [
            html.P("Gate TEST → DEPLOY: bloqueado", style={"fontWeight": "700", "color": "#b45309", "marginBottom": f"{S}px"}),
            html.P("Para liberar:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px"}),
            html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
            html.P(
                "Sem este pacote a API não aceita avançar o cartão na esteira.",
                style={**ESTILO_APOIO, "marginTop": f"{S}px", "marginBottom": 0},
            ),
        ],
        style={**box, "backgroundColor": "#fffbeb", "borderColor": "#fcd34d"},
    )


def _atividade_casos_teste_rows(items):
    if not items:
        items = [caso_teste_vazio()]
    ta = {**ESTILO_INPUT, "minHeight": "72px", "width": "100%", "boxSizing": "border-box"}
    inp = {**ESTILO_INPUT, "width": "100%", "boxSizing": "border-box"}
    cartoes = []
    for i, c in enumerate(items):
        if not isinstance(c, dict):
            c = caso_teste_vazio()
        st = (c.get("status") or "PENDENTE").strip().upper()
        if st not in ("APROVADO", "REPROVADO", "PENDENTE"):
            st = "PENDENTE"
        data_iso = (c.get("data_execucao") or "").strip() or None
        cartoes.append(
            html.Div(
                [
                    html.P(f"Caso de teste {i + 1}", style={"fontWeight": "600", "fontSize": "0.9rem", "marginBottom": f"{S}px"}),
                    html.Label("Resumo", style=ESTILO_LABEL),
                    dcc.Input(id={"type": "atividade-caso-resumo", "index": i}, value=c.get("resumo") or "", type="text", style=inp),
                    html.Label("Passos de execução", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.Textarea(id={"type": "atividade-caso-passos", "index": i}, value=c.get("passos") or "", style=ta),
                    html.Label("Resultado esperado", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.Textarea(id={"type": "atividade-caso-esperado", "index": i}, value=c.get("resultado_esperado") or "", style=ta),
                    html.Label("Resultado obtido", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.Textarea(id={"type": "atividade-caso-obtido", "index": i}, value=c.get("resultado_obtido") or "", style=ta),
                    html.Label("Status", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.Dropdown(
                        id={"type": "atividade-caso-status", "index": i},
                        options=_CASOS_TESTE_STATUS_OPTS,
                        value=st,
                        clearable=False,
                        style={"width": "100%"},
                    ),
                    html.Label("Executor (quem testou)", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.Input(id={"type": "atividade-caso-executor", "index": i}, value=c.get("executor") or "", type="text", style=inp),
                    html.Label("Data de execução", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.DatePickerSingle(
                        id={"type": "atividade-caso-data", "index": i},
                        date=data_iso,
                        display_format="DD/MM/YYYY",
                        first_day_of_week=1,
                        style={"width": "100%"},
                    ),
                    html.Label("Evidência / observação (links, anexos, notas)", style={**ESTILO_LABEL, "marginTop": f"{S}px"}),
                    dcc.Textarea(id={"type": "atividade-caso-evidencia", "index": i}, value=c.get("evidencia") or "", style=ta),
                ],
                style={
                    "border": f"1px solid {CORES['border']}",
                    "borderRadius": f"{R}px",
                    "padding": f"{S * 2}px",
                    "marginBottom": f"{S * 2}px",
                    "backgroundColor": "#fafafa",
                },
            )
        )
    return html.Div(cartoes)


def _doc_requisito_rows(items, row_type: str):
    if not isinstance(items, list) or len(items) == 0:
        items = [""]
    ta_row = {**ESTILO_INPUT, "minHeight": "80px", "width": "100%", "boxSizing": "border-box"}
    blocos = []
    for i, v in enumerate(items):
        blocos.append(
            html.Div(
                [
                    html.Span(
                        f"{i + 1}.",
                        style={
                            "color": CORES["text_muted"],
                            "marginRight": f"{S}px",
                            "fontSize": "0.8125rem",
                            "minWidth": "1.5em",
                            "paddingTop": f"{S}px",
                        },
                    ),
                    dcc.Textarea(
                        id={"type": row_type, "index": i},
                        value=str(v) if v is not None else "",
                        style=ta_row,
                    ),
                ],
                style={"display": "flex", "gap": f"{S}px", "alignItems": "flex-start", "marginBottom": f"{S * 1.25}px"},
            )
        )
    return html.Div(blocos)


def _doc_requisito_add_row(n_clicks, store_data, vals):
    if not n_clicks:
        return no_update
    prev: list[str] = []
    if vals is not None and isinstance(vals, list):
        prev = ["" if v is None else str(v) for v in vals]
    elif isinstance(store_data, list):
        prev = ["" if x is None else str(x) for x in store_data]
    if not prev:
        prev = [""]
    return prev + [""]


@app.callback(Output("atividade-doc-rf-rows", "children"), Input("atividade-doc-store-rf", "data"))
def _doc_rf_rows_render(items):
    return _doc_requisito_rows(items, "atividade-rf-row")


@app.callback(
    Output("atividade-doc-store-rf", "data"),
    Input("atividade-doc-btn-add-rf", "n_clicks"),
    State("atividade-doc-store-rf", "data"),
    State({"type": "atividade-rf-row", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def _doc_rf_add(n, st, vals):
    return _doc_requisito_add_row(n, st, vals)


@app.callback(Output("atividade-doc-rnf-rows", "children"), Input("atividade-doc-store-rnf", "data"))
def _doc_rnf_rows_render(items):
    return _doc_requisito_rows(items, "atividade-rnf-row")


@app.callback(
    Output("atividade-doc-store-rnf", "data"),
    Input("atividade-doc-btn-add-rnf", "n_clicks"),
    State("atividade-doc-store-rnf", "data"),
    State({"type": "atividade-rnf-row", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def _doc_rnf_add(n, st, vals):
    return _doc_requisito_add_row(n, st, vals)


@app.callback(Output("atividade-doc-regras-rows", "children"), Input("atividade-doc-store-regras", "data"))
def _doc_regras_rows_render(items):
    return _doc_requisito_rows(items, "atividade-regras-row")


@app.callback(
    Output("atividade-doc-store-regras", "data"),
    Input("atividade-doc-btn-add-regras", "n_clicks"),
    State("atividade-doc-store-regras", "data"),
    State({"type": "atividade-regras-row", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def _doc_regras_add(n, st, vals):
    return _doc_requisito_add_row(n, st, vals)


@app.callback(Output("atividade-doc-criterios-rows", "children"), Input("atividade-doc-store-criterios", "data"))
def _doc_criterios_rows_render(items):
    return _doc_requisito_rows(items, "atividade-criterios-row")


@app.callback(
    Output("atividade-doc-store-criterios", "data"),
    Input("atividade-doc-btn-add-criterios", "n_clicks"),
    State("atividade-doc-store-criterios", "data"),
    State({"type": "atividade-criterios-row", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def _doc_criterios_add(n, st, vals):
    return _doc_requisito_add_row(n, st, vals)


@app.callback(
    Output("atividade-doc-gate-backlog", "children"),
    Input("atividade-doc-nome-funcionalidade", "value"),
    Input("atividade-doc-descricao-detalhada", "value"),
    Input("atividade-doc-restricoes", "value"),
    Input({"type": "atividade-rf-row", "index": ALL}, "value"),
    Input({"type": "atividade-rnf-row", "index": ALL}, "value"),
    Input({"type": "atividade-regras-row", "index": ALL}, "value"),
    Input({"type": "atividade-criterios-row", "index": ALL}, "value"),
)
def _atividade_doc_gate_backlog(nome, desc, restr, vrf, vrnf, vrg, vcrit):
    return _render_doc_backlog_gate_children(nome, desc, restr, vrf, vrnf, vrg, vcrit)


@app.callback(
    Output("atividade-doc-gate-prontidao", "children"),
    Input("atividade-prontidao-responsavel", "value"),
    Input("atividade-prontidao-registrado", "value"),
    Input("atividade-prontidao-data", "date"),
    Input("atividade-prontidao-checklist", "value"),
    Input("store-atividade-detalhe", "data"),
)
def _atividade_doc_gate_prontidao(resp, reg, dt, ch, store_data):
    fd = store_data.get("documentacao_fase") if isinstance(store_data, dict) else None
    return _render_prontidao_gate_children(resp, reg, dt, ch, fd)


@app.callback(
    [
        Output("atividade-doc-msg-prontidao", "children"),
        Output("store-atividade-detalhe", "data", allow_duplicate=True),
    ],
    Input("atividade-doc-btn-prontidao", "n_clicks"),
    State("atividade-prontidao-responsavel", "value"),
    State("atividade-prontidao-registrado", "value"),
    State("atividade-prontidao-data", "date"),
    State("atividade-prontidao-observacoes", "value"),
    State("atividade-prontidao-checklist", "value"),
    State("store-atividade-detalhe", "data"),
    prevent_initial_call=True,
)
def _salvar_doc_prontidao(n_clicks, resp, reg, dt, obs, ch, store_data):
    if not n_clicks:
        return no_update, no_update
    if not store_data or store_data.get("parse_error"):
        return html.Span("Sem atividade carregada.", style=ESTILO_ERRO), no_update
    aid = store_data.get("id")
    if aid is None:
        return html.Span("ID inválido.", style=ESTILO_ERRO), no_update
    payload = {
        "responsavel_desenvolvimento": resp or "",
        "registrado_por": reg or "",
        "data_prontidao": dt or "",
        "observacoes_tecnicas": obs or "",
        "checklist": list(ch) if isinstance(ch, list) else [],
    }
    body = serialize_prontidao_dev_conteudo(payload, int(aid))
    _r, err = api_salvar_documentacao_fase(int(aid), "prontidao_dev", body)
    if err:
        return html.Span(err, style=ESTILO_ERRO), no_update
    return html.Span("Gravado no banco de dados.", style=ESTILO_SUCESSO), _store_merge_documentacao_fase(store_data, "prontidao_dev", body)


@app.callback(
    Output("atividade-doc-gate-entrega", "children"),
    Input("atividade-entrega-nome", "value"),
    Input("atividade-entrega-desenvolvido", "value"),
    Input("atividade-entrega-alteracoes", "value"),
    Input("atividade-entrega-validacao", "value"),
    Input("atividade-entrega-branch", "value"),
    Input("atividade-entrega-commit", "value"),
    Input("atividade-entrega-desenvolvedor", "value"),
    Input("atividade-entrega-data", "date"),
)
def _atividade_doc_gate_entrega(nome, ddev, alt, val, br, cm, dev, dt):
    return _render_entrega_dev_gate_children(nome, ddev, alt, val, br, cm, dev, dt)


@app.callback(
    Output("atividade-doc-msg-entrega-dev", "children"),
    Input("atividade-doc-btn-entrega-dev", "n_clicks"),
    State("atividade-entrega-nome", "value"),
    State("atividade-entrega-desenvolvido", "value"),
    State("atividade-entrega-alteracoes", "value"),
    State("atividade-entrega-validacao", "value"),
    State("atividade-entrega-branch", "value"),
    State("atividade-entrega-commit", "value"),
    State("atividade-entrega-desenvolvedor", "value"),
    State("atividade-entrega-data", "date"),
    State("store-atividade-detalhe", "data"),
    prevent_initial_call=True,
)
def _salvar_doc_entrega_dev(n_clicks, nome, ddev, alt, val, br, cm, dev, dt, store_data):
    if not n_clicks:
        return no_update
    if not store_data or store_data.get("parse_error"):
        return html.Span("Sem atividade carregada.", style=ESTILO_ERRO)
    aid = store_data.get("id")
    if aid is None:
        return html.Span("ID inválido.", style=ESTILO_ERRO)
    payload = {
        "nome_entrega": nome or "",
        "descricao_desenvolvido": ddev or "",
        "alteracoes": alt or "",
        "validacao_qa": val or "",
        "branch_referencia": br or "",
        "commit_referencia": cm or "",
        "desenvolvedor": dev or "",
        "data_entrega_teste": dt or "",
    }
    body = serialize_entrega_dev_conteudo(payload, int(aid))
    _r, err = api_salvar_documentacao_fase(int(aid), "entrega_dev", body)
    if err:
        return html.Span(err, style=ESTILO_ERRO)
    return html.Span("Gravado no banco de dados.", style=ESTILO_SUCESSO)


@app.callback(Output("atividade-doc-casos-teste-rows", "children"), Input("atividade-doc-store-casos-teste", "data"))
def _casos_teste_rows_render(items):
    return _atividade_casos_teste_rows(items if isinstance(items, list) else None)


@app.callback(
    Output("atividade-doc-store-casos-teste", "data"),
    Input("atividade-doc-btn-add-caso-teste", "n_clicks"),
    State("atividade-doc-store-casos-teste", "data"),
    State({"type": "atividade-caso-resumo", "index": ALL}, "value"),
    State({"type": "atividade-caso-passos", "index": ALL}, "value"),
    State({"type": "atividade-caso-esperado", "index": ALL}, "value"),
    State({"type": "atividade-caso-obtido", "index": ALL}, "value"),
    State({"type": "atividade-caso-status", "index": ALL}, "value"),
    State({"type": "atividade-caso-executor", "index": ALL}, "value"),
    State({"type": "atividade-caso-data", "index": ALL}, "date"),
    State({"type": "atividade-caso-evidencia", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def _casos_teste_add_row(
    n_clicks, _st, r, pas, esp, obt, sts, exe, dts, evi,
):
    if not n_clicks:
        return no_update
    merged = _casos_teste_list_from_all_states(r, pas, esp, obt, sts, exe, dts, evi)
    merged.append(caso_teste_vazio())
    return merged


@app.callback(
    Output("atividade-doc-gate-casos-teste", "children"),
    Input({"type": "atividade-caso-resumo", "index": ALL}, "value"),
    Input({"type": "atividade-caso-passos", "index": ALL}, "value"),
    Input({"type": "atividade-caso-esperado", "index": ALL}, "value"),
    Input({"type": "atividade-caso-obtido", "index": ALL}, "value"),
    Input({"type": "atividade-caso-status", "index": ALL}, "value"),
    Input({"type": "atividade-caso-executor", "index": ALL}, "value"),
    Input({"type": "atividade-caso-data", "index": ALL}, "date"),
    Input({"type": "atividade-caso-evidencia", "index": ALL}, "value"),
)
def _atividade_doc_gate_casos_teste(r, pas, esp, obt, sts, exe, dts, evi):
    return _render_casos_teste_gate_children(r, pas, esp, obt, sts, exe, dts, evi)


@app.callback(
    [
        Output("atividade-doc-msg-casos-teste", "children"),
        Output("store-atividade-detalhe", "data", allow_duplicate=True),
    ],
    Input("atividade-doc-btn-casos-teste", "n_clicks"),
    State({"type": "atividade-caso-resumo", "index": ALL}, "value"),
    State({"type": "atividade-caso-passos", "index": ALL}, "value"),
    State({"type": "atividade-caso-esperado", "index": ALL}, "value"),
    State({"type": "atividade-caso-obtido", "index": ALL}, "value"),
    State({"type": "atividade-caso-status", "index": ALL}, "value"),
    State({"type": "atividade-caso-executor", "index": ALL}, "value"),
    State({"type": "atividade-caso-data", "index": ALL}, "date"),
    State({"type": "atividade-caso-evidencia", "index": ALL}, "value"),
    State("store-atividade-detalhe", "data"),
    prevent_initial_call=True,
)
def _salvar_doc_casos_teste(n_clicks, r, pas, esp, obt, sts, exe, dts, evi, store_data):
    if not n_clicks:
        return no_update, no_update
    if not store_data or store_data.get("parse_error"):
        return html.Span("Sem atividade carregada.", style=ESTILO_ERRO), no_update
    aid = store_data.get("id")
    if aid is None:
        return html.Span("ID inválido.", style=ESTILO_ERRO), no_update
    casos = _casos_teste_list_from_all_states(r, pas, esp, obt, sts, exe, dts, evi)
    body = serialize_casos_teste_conteudo({"casos": casos}, int(aid))
    _r, err = api_salvar_documentacao_fase(int(aid), "casos_teste", body)
    if err:
        return html.Span(err, style=ESTILO_ERRO), no_update
    return html.Span("Gravado no banco de dados.", style=ESTILO_SUCESSO), _store_merge_documentacao_fase(store_data, "casos_teste", body)


@app.callback(
    Output("atividade-doc-gate-deploy", "children"),
    Input("atividade-deploy-versao", "value"),
    Input("atividade-deploy-ambiente", "value"),
    Input("atividade-deploy-data", "date"),
    Input("atividade-deploy-responsavel", "value"),
)
def _atividade_doc_gate_deploy(versao, ambiente, dt, resp):
    return _render_deploy_gate_children(versao, ambiente, dt, resp)


@app.callback(
    [
        Output("atividade-doc-msg-deploy", "children"),
        Output("store-atividade-detalhe", "data", allow_duplicate=True),
    ],
    Input("atividade-doc-btn-deploy", "n_clicks"),
    State("atividade-deploy-versao", "value"),
    State("atividade-deploy-ambiente", "value"),
    State("atividade-deploy-data", "date"),
    State("atividade-deploy-responsavel", "value"),
    State("atividade-deploy-observacoes", "value"),
    State("store-atividade-detalhe", "data"),
    prevent_initial_call=True,
)
def _salvar_doc_deploy(n_clicks, versao, ambiente, dt, resp, obs, store_data):
    if not n_clicks:
        return no_update, no_update
    if not store_data or store_data.get("parse_error"):
        return html.Span("Sem atividade carregada.", style=ESTILO_ERRO), no_update
    aid = store_data.get("id")
    if aid is None:
        return html.Span("ID inválido.", style=ESTILO_ERRO), no_update
    payload = {
        "versao_entregue": versao or "",
        "ambiente": ambiente or "",
        "data_deploy": dt or "",
        "responsavel_deploy": resp or "",
        "observacoes": obs or "",
    }
    body = serialize_deploy_conteudo(payload, int(aid))
    _r, err = api_salvar_documentacao_fase(int(aid), "deploy", body)
    if err:
        return html.Span(err, style=ESTILO_ERRO), no_update
    return html.Span("Gravado no banco de dados.", style=ESTILO_SUCESSO), _store_merge_documentacao_fase(store_data, "deploy", body)


@app.callback(
    [
        Output("atividade-doc-msg-requisito-tres-campos", "children"),
        Output("store-atividade-detalhe", "data", allow_duplicate=True),
    ],
    Input("atividade-doc-btn-requisito-tres-campos", "n_clicks"),
    State("atividade-doc-nome-funcionalidade", "value"),
    State("atividade-doc-descricao-detalhada", "value"),
    State("atividade-doc-restricoes", "value"),
    State({"type": "atividade-rf-row", "index": ALL}, "value"),
    State({"type": "atividade-rnf-row", "index": ALL}, "value"),
    State({"type": "atividade-regras-row", "index": ALL}, "value"),
    State({"type": "atividade-criterios-row", "index": ALL}, "value"),
    State("store-atividade-detalhe", "data"),
    prevent_initial_call=True,
)
def _salvar_doc_requisito_tres_campos(n_clicks, nome, desc, restr, vals_rf, vals_rnf, vals_reg, vals_crit, store_data):
    if not n_clicks:
        return no_update, no_update
    if not store_data or store_data.get("parse_error"):
        return html.Span("Sem atividade carregada.", style=ESTILO_ERRO), no_update
    aid = store_data.get("id")
    if aid is None:
        return html.Span("ID inválido.", style=ESTILO_ERRO), no_update
    header = {
        "nome_funcionalidade": nome or "",
        "descricao_detalhada": desc or "",
        "restricoes": restr or "",
    }
    payload = serialize_doc_requisito_completo(
        header,
        vals_rf or [],
        vals_rnf or [],
        vals_reg or [],
        vals_crit or [],
    )
    _r, err = api_salvar_documentacao_fase(int(aid), "doc_requisito", payload)
    if err:
        return html.Span(err, style=ESTILO_ERRO), no_update
    return html.Span("Gravado no banco de dados.", style=ESTILO_SUCESSO), _store_merge_documentacao_fase(store_data, "doc_requisito", payload)


@app.callback(
    Output({"type": "atividade-doc-msg", "fase": MATCH}, "children"),
    Input({"type": "atividade-doc-btn", "fase": MATCH}, "n_clicks"),
    State({"type": "atividade-doc-ta", "fase": MATCH}, "value"),
    State("store-atividade-detalhe", "data"),
    prevent_initial_call=True,
)
def _salvar_documentacao_fase_atividade(n_clicks, texto, store_data):
    # Não adicionar Output("store-atividade-detalhe") aqui: Dash exige o mesmo MATCH em todos
    # os outputs do callback; o merge do store fica só nos saves de formulário estruturado.
    if not n_clicks:
        return no_update
    if not store_data or store_data.get("parse_error"):
        return html.Span("Sem atividade carregada.", style=ESTILO_ERRO)
    aid = store_data.get("id")
    if aid is None:
        return html.Span("ID inválido.", style=ESTILO_ERRO)
    triggered = callback_context.triggered_id
    if not isinstance(triggered, dict) or triggered.get("type") != "atividade-doc-btn":
        return no_update
    fase = triggered.get("fase")
    if not fase or fase in ("doc_requisito", "prontidao_dev", "entrega_dev", "casos_teste", "deploy"):
        return no_update
    corpo = texto or ""
    _r, err = api_salvar_documentacao_fase(int(aid), str(fase), corpo)
    if err:
        return html.Span(err, style=ESTILO_ERRO)
    return html.Span("Gravado no banco de dados.", style=ESTILO_SUCESSO)


@app.callback(Output("kanban-lista-conteudo", "children"), Input("store-kanban-lista", "data"))
def _render_kanban_lista_view(data):
    return _render_kanban_lista_conteudo(data)


@app.callback(Output("store-sidebar-open", "data"), Input("btn-toggle-sidebar", "n_clicks"), State("store-sidebar-open", "data"), prevent_initial_call=True)
def _toggle_sidebar(_n, is_open):
    return not bool(is_open)


@app.callback(Output("sidebar-wrapper", "style"), Input("store-sidebar-open", "data"))
def _apply_sidebar_visibility(is_open):
    b = ESTILO_SIDEBAR.copy()
    if not is_open:
        b["display"] = "none"
    return b


@app.callback(
    [Output("calib-vazao-incrementos", "value"), Output("calib-vazao-bugs", "value")],
    [Input("store-calibragem", "data"), Input("calib-vazao-bugs", "value")],
)
def _calibragem_vazao(store_data, bugs_value):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update
    trig = ctx.triggered[0]["prop_id"]
    if trig == "store-calibragem.data":
        if not store_data or not isinstance(store_data, dict):
            return no_update, no_update
        vz = store_data.get("vazao") or {}
        return vz.get("incrementos"), vz.get("bugs")
    if trig == "calib-vazao-bugs.value":
        if bugs_value is None or str(bugs_value).strip() == "":
            return no_update, no_update
        try:
            b = max(0, min(100, float(bugs_value)))
        except (TypeError, ValueError):
            return no_update, no_update
        return round(100 - b, 2), b
    return no_update, no_update


_WIP_DEFAULTS = {"TO_DO": 5, "DEVELOP": 2, "TEST": 2, "DEPLOY": 1}


@app.callback(
    [
        Output("msg-calibragem", "children"),
        Output("store-calibragem", "data", allow_duplicate=True),
    ],
    Input("btn-salvar-calibragem", "n_clicks"),
    [State(a, "value") for a, _s, _k in _CALIB_INPUTS],
    prevent_initial_call=True,
)
def _calibragem_salvar(n, *vals):
    if not n:
        return no_update, no_update
    cfg = {"vazao": {}, "envelhecimento": {}, "wip": {}}
    for (id_, sec, key), v in zip(_CALIB_INPUTS, vals):
        if sec not in cfg:
            continue
        if v is not None and str(v).strip() != "":
            try:
                cfg[sec][key] = float(v)
            except (ValueError, TypeError):
                cfg[sec][key] = v
    if "bugs" in cfg.get("vazao", {}):
        try:
            b = float(cfg["vazao"]["bugs"])
            b = max(0, min(100, b))
            cfg["vazao"]["bugs"] = b
            cfg["vazao"]["incrementos"] = round(100 - b, 2)
        except (KeyError, ValueError, TypeError):
            pass
    # Sempre persistir WIP com valores numéricos (evita cfg["wip"]={} e merge apagar limites).
    for (_id, sec, key), v in zip(_CALIB_INPUTS, vals):
        if sec != "wip":
            continue
        d = _WIP_DEFAULTS[key]
        if v is None or (isinstance(v, str) and str(v).strip() == ""):
            cfg["wip"][key] = float(d)
        else:
            try:
                cfg["wip"][key] = float(max(0, int(float(v))))
            except (TypeError, ValueError):
                cfg["wip"][key] = float(d)
    try:
        save_config_fila(cfg)
    except Exception as e:
        return html.Div(f"Erro ao salvar: {e}", style=ESTILO_ERRO), no_update
    try:
        fresh = get_config_fila()
    except Exception:
        fresh = no_update
    return html.Div("Configuração salva (inclui WIP do Kanban).", style=ESTILO_SUCESSO), fresh


@app.callback(
    [Output("calib-wip-todo", "value"), Output("calib-wip-develop", "value"), Output("calib-wip-test", "value"), Output("calib-wip-deploy", "value")],
    [Input("wip-todo-dec", "n_clicks"), Input("wip-todo-inc", "n_clicks"), Input("wip-develop-dec", "n_clicks"), Input("wip-develop-inc", "n_clicks"),
     Input("wip-test-dec", "n_clicks"), Input("wip-test-inc", "n_clicks"), Input("wip-deploy-dec", "n_clicks"), Input("wip-deploy-inc", "n_clicks")],
    [State("calib-wip-todo", "value"), State("calib-wip-develop", "value"), State("calib-wip-test", "value"), State("calib-wip-deploy", "value")],
    prevent_initial_call=True,
)
def _wip_ajustar(*args):
    ctx = callback_context
    if not ctx.triggered:
        return args[-4:]
    tid = ctx.triggered[0]["prop_id"].split(".")[0]
    def nrm(v):
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 0
    todo, dev, tes, dep = nrm(args[-4]), nrm(args[-3]), nrm(args[-2]), nrm(args[-1])
    if tid == "wip-todo-dec":
        todo = max(0, todo - 1)
    elif tid == "wip-todo-inc":
        todo += 1
    elif tid == "wip-develop-dec":
        dev = max(0, dev - 1)
    elif tid == "wip-develop-inc":
        dev += 1
    elif tid == "wip-test-dec":
        tes = max(0, tes - 1)
    elif tid == "wip-test-inc":
        tes += 1
    elif tid == "wip-deploy-dec":
        dep = max(0, dep - 1)
    elif tid == "wip-deploy-inc":
        dep += 1
    return todo, dev, tes, dep


@app.callback(
    [Output("calib-wip-todo", "value", allow_duplicate=True), Output("calib-wip-develop", "value", allow_duplicate=True),
     Output("calib-wip-test", "value", allow_duplicate=True), Output("calib-wip-deploy", "value", allow_duplicate=True)],
    Input("store-calibragem", "data"),
    prevent_initial_call=True,
)
def _hidrate_wip(store_data):
    if not store_data or not isinstance(store_data, dict):
        return no_update, no_update, no_update, no_update
    w = store_data.get("wip") or {}

    def g(key, d):
        v = w.get(key)
        return int(v) if v is not None and str(v).strip() != "" else d

    return g("TO_DO", 5), g("DEVELOP", 2), g("TEST", 2), g("DEPLOY", 1)


def _wip_limits():
    try:
        cfg = get_config_fila()
    except Exception:
        cfg = {}
    wip = cfg.get("wip") or {}
    def lim(k):
        try:
            v = int(wip.get(k))
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None
    return {"BACKLOG": None, "TO DO": lim("TO_DO"), "DEVELOP": lim("DEVELOP"), "TEST": lim("TEST"), "DEPLOY": lim("DEPLOY"), "DONE": None}


@app.callback(Output("store-kanban-docs", "data"), Input("store-kanban", "data"))
def _kanban_carregar_documentacao_por_cartao(items):
    """Carrega documentação gravada de cada requisito no quadro (para gate visual e coerência)."""
    if not items:
        return {}
    out: dict[str, dict] = {}
    for it in items:
        aid = it.get("id")
        if aid is None:
            continue
        try:
            i = int(aid)
        except (TypeError, ValueError):
            continue
        sk = str(i)
        docs, _err = api_obter_documentacao_fase(i)
        out[sk] = docs if isinstance(docs, dict) else {}
    return out


@app.callback(
    [Output(f"kanban-col-{c}", "children") for c in KANBAN_COLUNAS],
    [Input("store-kanban", "data"), Input("store-kanban-docs", "data")],
)
def _render_kanban(store_data, docs_data):
    wl = _wip_limits()
    if not store_data:
        store_data = []
    by_col = {c: [] for c in KANBAN_COLUNAS}
    for it in store_data:
        by_col[_status_item_para_coluna_kanban(it)].append(it)
    out = []
    for col in KANBAN_COLUNAS:
        itens = by_col[col]
        lim = wl.get(col)
        cnt = len(itens)
        tit = f"{col} ({cnt}/{lim})" if lim else f"{col} ({cnt})"
        hs = {"fontWeight": "600", "fontSize": "0.9375rem", "marginBottom": f"{S}px", "color": CORES["text"]}
        if lim and cnt >= lim:
            hs.update({"backgroundColor": "#fee2e2", "borderRadius": f"{R}px", "padding": f"{S}px {S*2}px", "border": f"1px solid {CORES['error']}", "color": CORES["error"]})
        cards = [html.Div(tit, style=hs)]
        idx = KANBAN_COLUNAS.index(col)
        for it in itens:
            iid = it.get("id")
            pode_v = idx > 0
            col_k = _status_item_para_coluna_kanban(it)
            docs_one: dict = {}
            if isinstance(docs_data, dict):
                docs_one = docs_data.get(str(iid)) or {}
            # docs_data None = ainda a carregar; não desactivar «Avançar» até haver dados (validação forte no clique).
            gate_ok = True
            if isinstance(docs_data, dict):
                gate_ok, _fal = _gate_documental_para_avancar_de_coluna(col_k, docs_one)
            pode_a = idx < len(KANBAN_COLUNAS) - 1 and gate_ok
            np = (it.get("nome_projeto") or "").strip()
            vp = (it.get("versao_projeto") or "").strip()
            linha_proj = []
            if np or vp:
                rot = " · ".join(p for p in (np, vp) if p)
                linha_proj = [html.Div(rot, style={"fontSize": "0.75rem", "color": CORES["text_muted"], "marginBottom": f"{S//2}px"})]
            gate_linha = []
            if isinstance(docs_data, dict) and idx < len(KANBAN_COLUNAS) - 1 and not gate_ok:
                gate_linha = [
                    html.Div(
                        "Gate documental: bloqueado — preencha e guarde a aba desta fase em Detalhe da atividade.",
                        style={"fontSize": "0.75rem", "color": "#b45309", "marginBottom": f"{S}px", "lineHeight": "1.35"},
                    )
                ]
            cards.append(html.Div([
                html.Div(str(it.get("titulo", "—")), style={"fontWeight": "600"}),
                html.Div(f"Tipo: {(it.get('tipo_requisito') or '').upper()}", style={"fontSize": "0.8125rem", "color": CORES["text_muted"]}),
                html.Div(f"Prioridade: {it.get('prioridade_categorica', '')}", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "marginBottom": f"{S}px"}),
                *linha_proj,
                *gate_linha,
                html.Div([
                    html.Button("← Voltar", id={"type": "kanban-move-prev", "id": iid}, n_clicks=0, disabled=not pode_v, style={**ESTILO_BOTAO, "padding": f"{S}px {S*2}px", "fontSize": "0.8125rem", "backgroundColor": CORES["text_muted"] if pode_v else "#e5e7eb"}),
                    html.Button("Avançar →", id={"type": "kanban-move-next", "id": iid}, n_clicks=0, disabled=not pode_a, style={**ESTILO_BOTAO, "padding": f"{S}px {S*2}px", "fontSize": "0.8125rem", "backgroundColor": CORES["primary"] if pode_a else "#e5e7eb"}),
                ], style={"display": "flex", "gap": f"{S}px", "flexWrap": "wrap", "alignItems": "center"}),
                dcc.Link("Detalhe da atividade", href=f"/atividade/{iid}", style={"fontSize": "0.75rem", "color": CORES["primary"], "marginTop": f"{S}px", "display": "inline-block"}),
            ], style={"padding": f"{S*2}px", "border": f"1px solid {CORES['border']}", "borderRadius": f"{R}px", "marginBottom": f"{S}px", "backgroundColor": CORES["surface"]}))
        if not itens:
            cards.append(html.Div("Nenhuma atividade nesta coluna.", style={"fontSize": "0.8125rem", "color": CORES["text_muted"]}))
        out.append(cards)
    return out


@app.callback(
    [Output("store-kanban", "data", allow_duplicate=True), Output("kanban-msg", "children", allow_duplicate=True)],
    Input({"type": "kanban-move-next", "id": ALL}, "n_clicks"),
    Input({"type": "kanban-move-prev", "id": ALL}, "n_clicks"),
    State("store-kanban", "data"),
    prevent_initial_call=True,
)
def _mover_kanban(_nc, _pc, data):
    ctx = callback_context
    if not ctx.triggered or not data:
        return no_update, no_update
    tid = ctx.triggered_id
    if not isinstance(tid, dict):
        return no_update, no_update
    mtype = tid.get("type")
    iid = tid.get("id")
    if iid is None or mtype not in ("kanban-move-next", "kanban-move-prev"):
        return no_update, no_update
    item = next((x for x in data if int(x.get("id", -1)) == int(iid)), None)
    if not item:
        return no_update, no_update
    cur = _status_item_para_coluna_kanban(item)
    if mtype == "kanban-move-next":
        dest = KANBAN_NEXT.get(cur)
    else:
        dest = KANBAN_PREV.get(cur)
    if not dest:
        return no_update, html.Div("Não é possível mover o cartão nesta direção.", style=ESTILO_ERRO)
    wl = _wip_limits()
    lim = wl.get(dest)
    if lim is not None:
        n_dest = sum(1 for x in data if _status_item_para_coluna_kanban(x) == dest and int(x.get("id", -1)) != int(iid))
        if n_dest + 1 > lim:
            aviso = html.Div(
                f'Coluna "{dest}" está no limite WIP ({lim}). Libere uma vaga ou ajuste os limites na Calibragem.',
                style={**ESTILO_ERRO, "color": "#c2410c"},
            )
            return no_update, aviso
    if mtype == "kanban-move-next":
        docs_live, _e = api_obter_documentacao_fase(int(iid))
        fd = docs_live if isinstance(docs_live, dict) else {}
        ok_gate, falta = _gate_documental_para_avancar_de_coluna(cur, fd)
        if not ok_gate:
            prox = KANBAN_NEXT.get(cur, "—")
            bloco = html.Div(
                [
                    html.P(
                        f'Não é possível avançar para «{prox}» (bloqueio documental — fase atual: {cur}).',
                        style={"fontWeight": "600", "marginBottom": f"{S}px", "color": "#b45309"},
                    ),
                    html.P("Complete e use «Guardar esta fase» em Detalhe da atividade. Falta:", style={"fontSize": "0.875rem", "marginBottom": f"{S // 2}px"}),
                    html.Ul([html.Li(x, style={"fontSize": "0.875rem"}) for x in falta]),
                    dcc.Link(
                        f"Abrir requisito #{iid}",
                        href=f"/atividade/{iid}",
                        style={"fontSize": "0.875rem", "color": CORES["primary"], "display": "inline-block", "marginTop": f"{S}px"},
                    ),
                ],
                style={"padding": f"{S}px 0"},
            )
            return no_update, bloco
    api_st = coluna_para_status_api(dest)
    _res, err = api_atualizar_status_requisito(int(iid), api_st)
    if err:
        return no_update, html.Div(err, style=ESTILO_ERRO)
    new = []
    for it in data:
        if int(it.get("id", -1)) == int(iid):
            new.append({**it, "status_kanban": dest, "status_atual": api_st})
        else:
            new.append(it)
    tit = (item.get("titulo") or "").strip()
    if len(tit) > 70:
        tit = tit[:67] + "…"
    extra = f" — {tit}" if tit else ""
    ok = html.Div(f'Requisito #{iid} movido para "{dest}".{extra}', style=ESTILO_SUCESSO)
    return new, ok


@app.callback([Output("proj-hint-versao-novo", "style"), Output("proj-wrap-versao-existente", "style")], Input("proj-tipo-origem", "value"))
def _proj_toggle_origem(tipo):
    if tipo == "existente":
        return _HIDE, {**_SHOW, "marginBottom": f"{S*2}px"}
    return _SHOW, _HIDE


def _opts_projetos(rows):
    if not rows:
        return []
    return [{"label": f"#{r.get('id_projeto')} — {r.get('nome_projeto', '')}", "value": r.get("id_projeto")} for r in rows]


def _montar_payload_criar_projeto(tipo, nome, desc, resp, st, ver):
    return {
        "nome_projeto": (nome or "").strip(),
        "descricao": (desc or "").strip() or None,
        "responsavel": (resp or "").strip() or None,
        "tipo_origem": tipo or "novo",
        "versao_atual": (ver or "").strip() if tipo == "existente" else None,
        "status_projeto": st or "ativo",
    }


def _id_projeto_dropdown_val(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


@app.callback(
    [Output("cadastro-id-projeto", "options"), Output("cadastro-id-projeto", "value", allow_duplicate=True), Output("store-cad-proj-selecionar", "data")],
    [Input("url", "pathname"), Input("store-proj-reload", "data")],
    State("store-cad-proj-selecionar", "data"),
    prevent_initial_call="initial_duplicate",
)
def _cadastro_fill_projetos(pathname, _bump_proj, sel_id):
    if (pathname or "") != "/":
        return no_update, no_update, no_update
    rows, err = api_listar_projetos()
    opts = _opts_projetos(rows) if rows and not err else []
    if sel_id is not None:
        try:
            vid = int(sel_id)
        except (TypeError, ValueError):
            vid = None
        if vid is not None:
            return opts, vid, None
    return opts, no_update, no_update


@app.callback(
    Output("cad-proj-form-wrap", "style"),
    Input("btn-cadastro-novo-projeto", "n_clicks"),
    State("cad-proj-form-wrap", "style"),
    prevent_initial_call=True,
)
def _cadastro_toggle_form_projeto(n, style_atual):
    if not n:
        return no_update
    st = style_atual or _HIDE
    if st.get("display") == "none":
        return {**_SHOW, "marginTop": f"{S*3}px", "padding": f"{S*3}px", "borderRadius": f"{R}px", "border": f"1px dashed {CORES['border']}", "backgroundColor": "#f8fafc"}
    return {**_HIDE, "marginTop": f"{S*3}px"}


@app.callback(
    [Output("cad-proj-hint-versao-novo", "style"), Output("cad-proj-wrap-versao-existente", "style")],
    Input("cad-proj-tipo-origem", "value"),
)
def _cadastro_toggle_versao_projeto(tipo):
    if tipo == "existente":
        return _HIDE, {**_SHOW, "marginBottom": f"{S*2}px"}
    return _SHOW, _HIDE


@app.callback(
    [
        Output("msg-cadastro-projeto", "children"),
        Output("store-proj-reload", "data", allow_duplicate=True),
        Output("store-cad-proj-selecionar", "data", allow_duplicate=True),
        Output("cad-proj-form-wrap", "style", allow_duplicate=True),
    ],
    Input("btn-cadastro-salvar-projeto", "n_clicks"),
    State("store-proj-reload", "data"),
    State("cad-proj-tipo-origem", "value"),
    State("cad-proj-nome", "value"),
    State("cad-proj-descricao", "value"),
    State("cad-proj-responsavel", "value"),
    State("cad-proj-status-cadastro", "value"),
    State("cad-proj-versao-existente", "value"),
    prevent_initial_call=True,
)
def _cadastro_salvar_projeto(n, bump, tipo, nome, desc, resp, st, ver):
    if not n:
        return no_update, no_update, no_update, no_update
    if not (nome or "").strip():
        return html.Div("Nome do projeto é obrigatório.", style=ESTILO_ERRO), no_update, no_update, no_update
    payload = _montar_payload_criar_projeto(tipo, nome, desc, resp, st, ver)
    resultado, err = api_criar_projeto(payload)
    if err:
        return html.Div(err, style=ESTILO_ERRO), no_update, no_update, no_update
    pid = (resultado or {}).get("id_projeto")
    nome_salvo = (resultado or {}).get("nome_projeto") or payload["nome_projeto"]
    versao = (resultado or {}).get("versao_atual") or "1.0.0"
    msg = html.Div([
        html.P("Projeto criado com sucesso.", style={**ESTILO_SUCESSO, "margin": 0}),
        html.P(f"Projeto vinculado à demanda atual: #{pid} — {nome_salvo} (versão {versao}).", style={**ESTILO_SUCESSO, "margin": f"{S//2}px 0 0 0", "fontSize": "0.8125rem"}),
    ])
    return (
        msg,
        (bump or 0) + 1,
        pid,
        {**_HIDE, "marginTop": f"{S*3}px"},
    )


@app.callback(
    [Output("proj-evoluir-id", "options"), Output("proj-alterar-status-id", "options")],
    Input("url", "pathname"), Input("store-proj-reload", "data"),
)
def _proj_fill_dropdowns(pathname, _b):
    if (pathname or "") != "/projetos":
        return no_update, no_update
    rows, err = api_listar_projetos()
    if err or rows is None:
        return [], []
    o = _opts_projetos(rows)
    return o, o


def _render_tabela_projetos(rows):
    if not rows:
        return html.P("Nenhum projeto listado.", style={"color": CORES["text_muted"]})
    head = html.Tr([html.Th(x, style=ESTILO_TABELA) for x in ("ID", "Nome", "Tipo", "Versão", "Status", "Resp.")])
    body = []
    for r in rows:
        body.append(html.Tr([
            html.Td(r.get("id_projeto"), style=ESTILO_TABELA),
            html.Td((r.get("nome_projeto") or "")[:60], style=ESTILO_TABELA),
            html.Td(r.get("tipo_origem"), style=ESTILO_TABELA),
            html.Td(r.get("versao_atual"), style=ESTILO_TABELA),
            html.Td(r.get("status_projeto"), style=ESTILO_TABELA),
            html.Td((r.get("responsavel") or "")[:40], style=ESTILO_TABELA),
        ]))
    return html.Table([html.Thead(head), html.Tbody(body)], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.875rem"})


def _proj_tabela_children(fo, fs, q):
    rows, err = api_listar_projetos(tipo_origem=fo or None, status=fs or None, q=q or None)
    if err:
        return html.Div(err, style=ESTILO_ERRO)
    return _render_tabela_projetos(rows or [])


@app.callback(Output("proj-tabela", "children"), Input("proj-filtro-origem", "value"), Input("proj-filtro-status", "value"), Input("proj-busca-nome", "value"), Input("store-proj-reload", "data"))
def _proj_tabela(fo, fs, q, _b):
    return _proj_tabela_children(fo, fs, q)


@app.callback(
    Output("proj-msg", "children"),
    Output("store-proj-reload", "data"),
    Output("proj-tabela", "children", allow_duplicate=True),
    Input("btn-salvar-projeto", "n_clicks"),
    State("store-proj-reload", "data"),
    State("proj-tipo-origem", "value"), State("proj-nome", "value"), State("proj-descricao", "value"), State("proj-responsavel", "value"),
    State("proj-status-cadastro", "value"), State("proj-versao-existente", "value"),
    State("proj-filtro-origem", "value"), State("proj-filtro-status", "value"), State("proj-busca-nome", "value"),
    prevent_initial_call=True,
)
def _proj_salvar(n, bump, tipo, nome, desc, resp, st, ver, fo, fs, q):
    if not n:
        return no_update, no_update, no_update
    if not (nome or "").strip():
        return html.Div("Nome obrigatório.", style=ESTILO_ERRO), no_update, no_update
    payload = _montar_payload_criar_projeto(tipo, nome, desc, resp, st, ver)
    _r, err = api_criar_projeto(payload)
    if err:
        return html.Div(err, style=ESTILO_ERRO), no_update, no_update
    return (
        html.Div("Projeto salvo.", style=ESTILO_SUCESSO),
        (bump or 0) + 1,
        _proj_tabela_children(fo, fs, q),
    )


@app.callback(
    Output("proj-msg", "children", allow_duplicate=True),
    Output("store-proj-reload", "data", allow_duplicate=True),
    Output("proj-tabela", "children", allow_duplicate=True),
    Input("btn-proj-evoluir", "n_clicks"),
    State("store-proj-reload", "data"),
    State("proj-evoluir-id", "value"),
    State("proj-evoluir-motivo", "value"),
    State("proj-evoluir-usuario", "value"),
    State("proj-filtro-origem", "value"),
    State("proj-filtro-status", "value"),
    State("proj-busca-nome", "value"),
    prevent_initial_call=True,
)
def _proj_evoluir(n, bump, pid, mot, usr, fo, fs, q):
    if not n or not pid:
        return no_update, no_update, no_update
    pid_i = _id_projeto_dropdown_val(pid)
    if pid_i is None:
        return no_update, no_update, no_update
    _r, err = api_evoluir_projeto(pid_i, "major", motivo=mot, usuario_responsavel=usr)
    if err:
        return html.Div(err, style=ESTILO_ERRO), no_update, no_update
    return (
        html.Div("Versão evoluída (MAJOR).", style=ESTILO_SUCESSO),
        (bump or 0) + 1,
        _proj_tabela_children(fo, fs, q),
    )


@app.callback(
    Output("proj-msg", "children", allow_duplicate=True),
    Output("store-proj-reload", "data", allow_duplicate=True),
    Output("proj-tabela", "children", allow_duplicate=True),
    Input("btn-proj-alterar-status", "n_clicks"),
    State("store-proj-reload", "data"),
    State("proj-alterar-status-id", "value"),
    State("proj-alterar-status-novo", "value"),
    State("proj-filtro-origem", "value"),
    State("proj-filtro-status", "value"),
    State("proj-busca-nome", "value"),
    prevent_initial_call=True,
)
def _proj_alterar_st(n, bump, pid, st, fo, fs, q):
    if not n:
        return no_update, no_update, no_update
    pid_i = _id_projeto_dropdown_val(pid)
    if pid_i is None:
        return html.Div("Selecione um projeto.", style=ESTILO_ERRO), no_update, no_update
    st_norm = (st or "").strip().lower()
    if st_norm not in ("ativo", "arquivado", "descontinuado"):
        return html.Div("Selecione um status válido.", style=ESTILO_ERRO), no_update, no_update
    _r, err = api_patch_status_projeto(pid_i, st_norm)
    if err:
        return html.Div(err, style=ESTILO_ERRO), no_update, no_update
    return (
        html.Div("Status atualizado.", style=ESTILO_SUCESSO),
        (bump or 0) + 1,
        _proj_tabela_children(fo, fs, q),
    )


def _normalizar_status_fluxo(st: str | None) -> str:
    if st is None or str(st).strip() == "":
        return ""
    u = unicodedata.normalize("NFKD", str(st).strip())
    u = "".join(c for c in u if not unicodedata.combining(c))
    u = u.upper().replace(" ", "_")
    while "__" in u:
        u = u.replace("__", "_")
    return u.strip("_")


def _status_concluido(st: str | None) -> bool:
    n = _normalizar_status_fluxo(st)
    return n in ("CONCLUIDO", "DONE")


def _status_coincide_filtro(status_item: str | None, filtro_valor: str) -> bool:
    n = _normalizar_status_fluxo(status_item)
    f = _normalizar_status_fluxo(filtro_valor)
    if not f:
        return True
    if n == f:
        return True
    if f == "DEVELOP" and n in ("EM_DESENVOLVIMENTO", "DEVELOP"):
        return True
    if f == "TO_DO" and n in ("TO_DO", "TODO"):
        return True
    return False


def _filtrar_visualizacao_atividades(data: list) -> list:
    return [a for a in data if not _status_concluido(a.get("status_atual") or "")]


def _atividades_aplicar_filtros_ui(data: list, f_tipo: str | None, f_status: str | None, f_busca: str | None) -> list:
    base = list(data)
    fs = f_status if f_status is not None else ""
    if fs == "__all__":
        pool = base
    elif fs == "" or fs is None:
        pool = _filtrar_visualizacao_atividades(base)
    else:
        pool = [a for a in base if _status_coincide_filtro(a.get("status_atual"), fs)]
    ft = (f_tipo or "").strip().upper()
    if ft == "BUG":
        pool = [a for a in pool if (a.get("tipo_requisito") or "").upper() == "BUG"]
    elif ft == "INCREMENTO":
        pool = [a for a in pool if (a.get("tipo_requisito") or "").upper() in ("INCREMENTO", "FEATURE")]
    q = (f_busca or "").strip().lower()
    if q:
        pool = [
            a for a in pool
            if q in (a.get("titulo") or "").lower() or q in str(a.get("id", "")).lower()
        ]
    return pool


@app.callback(
    [Output("atividades-resumo", "children"), Output("atividades-grafico-bugs", "children"), Output("atividades-grafico-incrementos", "children"), Output("atividades-tabela", "children")],
    Input("store-atividades", "data"),
    Input("ativ-filtro-tipo", "value"),
    Input("ativ-filtro-status", "value"),
    Input("ativ-filtro-busca", "value"),
)
def _render_atividades(data, f_tipo, f_status, f_busca):
    if not data:
        e = html.Div("Nenhuma atividade carregada.", style={"color": CORES["text_muted"]})
        return e, e, e, e
    viz = _atividades_aplicar_filtros_ui(data, f_tipo, f_status, f_busca)
    bugs_v = [a for a in viz if (a.get("tipo_requisito") or "").upper() == "BUG"]
    inc_v = [a for a in viz if (a.get("tipo_requisito") or "").upper() in ("INCREMENTO", "FEATURE")]
    concl = sum(1 for a in data if _status_concluido(a.get("status_atual") or ""))
    cards = html.Div([
        html.Div([html.Div(str(len(bugs_v)), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["bug"]}), html.Div("Bugs", style={"fontSize": "0.875rem", "color": CORES["text_muted"]})], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
        html.Div([html.Div(str(len(inc_v)), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["feature"]}), html.Div("Incrementos", style={"fontSize": "0.875rem", "color": CORES["text_muted"]})], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
        html.Div([html.Div(str(concl), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["success"]}), html.Div("Concluídas", style={"fontSize": "0.875rem", "color": CORES["text_muted"]})], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
        html.Div([html.Div(str(len(viz)), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text_muted"]}), html.Div("Pendentes (visão)", style={"fontSize": "0.875rem", "color": CORES["text_muted"]})], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "justifyContent": "center"})

    def _scat(tipo, tit_x, tit_y):
        itens = bugs_v if tipo == "BUG" else inc_v
        if not itens:
            return html.Div(f"Nenhum {tipo.lower()} na seleção atual (ajuste os filtros).", style={"color": CORES["text_muted"]})
        xs = [a.get("coordenada_x", 0) for a in itens]
        ys = [a.get("coordenada_y", 0) for a in itens]
        fig = go.Figure(data=[go.Scatter(x=xs, y=ys, mode="markers", text=[a.get("titulo", "") for a in itens], hoverinfo="text", marker=dict(size=12, color=CORES["bug"] if tipo == "BUG" else CORES["feature"]))])
        # Margem nos eixos (escala lógica 0–5) para bolinhas em 0 ou 5 não colarem no limite do gráfico.
        _eixo_matriz = dict(
            range=[-0.35, 5.35],
            tickmode="array",
            tickvals=[0, 1, 2, 3, 4, 5],
            zeroline=True,
            autorange=False,
            constrain="domain",
        )
        fig.update_layout(
            title=f"Matriz de {tipo}s",
            xaxis_title=tit_x,
            yaxis_title=tit_y,
            margin=dict(l=60, r=40, t=50, b=50),
            height=400,
            template="plotly_white",
            xaxis={**_eixo_matriz},
            yaxis={**_eixo_matriz},
        )
        return dcc.Graph(figure=fig)
    gb, gi = _scat("BUG", "Criticidade", "Severidade"), _scat("INCREMENTO", "Esforço", "Valor")
    rows = [html.Tr([
        html.Td(a.get("id"), style=ESTILO_TABELA),
        html.Td((a.get("titulo", "") or "")[:50], style=ESTILO_TABELA),
        html.Td(a.get("tipo_requisito"), style=ESTILO_TABELA),
        html.Td((a.get("nome_projeto") or "")[:40] or "—", style=ESTILO_TABELA),
        html.Td((a.get("versao_projeto") or "")[:16] or "—", style=ESTILO_TABELA),
        html.Td(a.get("coordenada_x"), style=ESTILO_TABELA), html.Td(a.get("coordenada_y"), style=ESTILO_TABELA),
        html.Td(a.get("score"), style=ESTILO_TABELA), html.Td(a.get("prioridade_categorica"), style=ESTILO_TABELA), html.Td(a.get("status_atual"), style=ESTILO_TABELA),
        html.Td(dcc.Link("Abrir", href=f"/atividade/{a.get('id')}", style={"color": CORES["primary"], "fontSize": "0.8125rem"}), style=ESTILO_TABELA),
    ]) for a in viz]
    tab_bits = [html.H3("Lista de atividades", style={"fontSize": "1.125rem"})]
    if not viz:
        tab_bits.append(html.P("Nenhuma atividade corresponde aos filtros.", style={"color": CORES["text_muted"], "fontSize": "0.875rem"}))
    else:
        tab_bits.append(html.Table([html.Thead(html.Tr([html.Th(h, style=ESTILO_TABELA) for h in (
            "ID", "Título", "Tipo", "Projeto", "Versão", "X", "Y", "Score", "Prioridade", "Status", "Detalhe",
        )])), html.Tbody(rows)]))
    tab = html.Div(tab_bits, style=ESTILO_SECAO)
    return cards, gb, gi, tab


@app.callback(
    [Output("store-analise", "data"), Output("msg-analise", "children"), Output("secao2-container", "children"), Output("secao3-container", "children")],
    Input("btn-analisar", "n_clicks"),
    [State("texto_original", "value"), State("tipo_informado_usuario", "value"), State("modulo_afetado", "value"), State("contexto_negocio", "value"),
     State("objetivo_desejado", "value"), State("impacto_percebido_usuario", "value"), State("frequencia_ocorrencia", "value"), State("urgencia_percebida", "value"),
     State("ha_contorno", "value"), State("sistema_ou_produto", "value"), State("cadastro-id-projeto", "value"), State("perfil_solicitante", "value")],
    prevent_initial_call=True,
)
def on_analisar(_n, texto, tipo, modulo, contexto, objetivo, impacto, freq, urg, contorno, sistema, id_projeto_dd, perfil):
    if not texto or not str(texto).strip():
        return None, html.Div("Preencha o texto original.", style=ESTILO_ERRO), "", ""
    ip = _id_projeto_dropdown_val(id_projeto_dd)
    if ip is None:
        return None, html.Div("Selecione um projeto ou use «+ Adicionar novo projeto» abaixo do campo.", style=ESTILO_ERRO), "", ""
    hc = (contorno or "").strip() or None
    payload = {"texto_original": str(texto).strip(), "tipo_informado_usuario": tipo or "NAO_SEI", "modulo_afetado": modulo or None, "contexto_negocio": contexto or None,
               "objetivo_desejado": objetivo or None, "impacto_percebido_usuario": impacto or None, "frequencia_ocorrencia": freq or None, "urgencia_percebida": urg or None,
               "ha_contorno": hc, "sistema_ou_produto": sistema or None, "perfil_solicitante": perfil or None}
    payload = {k: v for k, v in payload.items() if v not in (None, "")}
    data, err = api_analisar(payload)
    if err:
        return None, html.Div(err, style=ESTILO_ERRO), "", ""
    ps = (perfil or "").strip() or None
    cad = {"perfil_solicitante": ps, "modulo_afetado": modulo, "contexto_negocio": contexto, "objetivo_desejado": objetivo, "sistema_ou_produto": sistema, "texto_original": str(texto).strip(), "id_projeto": ip}
    full = {**data, "cadastro": cad}
    return full, html.Div("Estruturação com IA concluída.", style=ESTILO_SUCESSO), _render_secao2(data), _render_secao3(data)


def _render_secao2(data: dict):
    t = (data.get("tipo_requisito") or "").upper().strip()
    tl = "Bug" if t == "BUG" else "Incremento" if "INCREMENTO" in t or t == "FEATURE" else "—"
    tc = CORES["bug"] if t == "BUG" else CORES["feature"] if "INCREMENTO" in t or t == "FEATURE" else CORES["text_muted"]
    return html.Div(className="animate-fade-in", style=ESTILO_SECAO, children=[
        html.Div([
            html.Span("2", style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "fontSize": "0.875rem", "marginRight": f"{S*2}px"}),
            html.H2("Demanda estruturada pela IA", style={"margin": 0, "fontSize": "1.25rem", "fontWeight": "700"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"}),
        html.Div([html.Span("Classificação: ", style={"fontSize": "0.9375rem"}), html.Span(tl, style={"backgroundColor": tc, "color": "#fff", "padding": "4px 12px", "borderRadius": "6px", "fontWeight": "600"})], style={"marginBottom": f"{S*3}px", "padding": f"{S*2}px", "background": "#f8fafc", "borderRadius": f"{R}px"}),
        html.Div([
            html.Div([html.Strong("Título: "), data.get("titulo_requisito", "—")]),
            html.Div([html.Strong("Descrição: "), data.get("descricao_requisito", "—")]),
            html.Div([html.Strong("Objetivo: "), data.get("objetivo", "—")]),
            html.Div([html.Strong("Finalidade: "), data.get("finalidade", "—")]),
        ], style={"background": "#f8fafc", "padding": f"{S*3}px", "borderRadius": f"{R}px"}),
    ])


def _render_secao3(data: dict):
    perg = data.get("perguntas_avaliacao") or []
    if not perg:
        return html.Div()
    itens = [html.Div([
        html.Label("Responsável pela avaliação", style=ESTILO_LABEL),
        dcc.Input(id="usuario_avaliador", type="text", placeholder="Nome", style=ESTILO_INPUT),
    ], style={**ESTILO_CAMPO, "marginBottom": f"{S*3}px"})]
    for i, p in enumerate(perg):
        op = p.get("opcoes_resposta") or []
        opts = [{"label": f"{o.get('rotulo', '')} ({o.get('valor', '')})", "value": o.get("valor")} for o in op if o.get("valor") is not None]
        itens.append(html.Div([
            html.P([html.Strong(f"P{i+1} "), p.get("texto", ""), html.Span(f" [{p.get('dimensao', '')}]", style={"color": CORES["text_muted"], "fontSize": "0.8125rem"})]),
            dcc.RadioItems(id={"type": "resposta", "index": i}, options=opts, value=None, inline=True),
        ], style={"marginBottom": f"{S*3}px", "padding": f"{S*3}px", "border": f"1px solid {CORES['border']}", "borderRadius": f"{R}px"}))
    itens.append(html.Div([html.Button("Salvar avaliação e posicionar na matriz", id="btn-calcular", n_clicks=0, style=ESTILO_BOTAO, className="dash-button"), html.Div(id="output-calculo", style={"marginTop": f"{S*2}px"})]))
    return html.Div(className="animate-fade-in", style=ESTILO_SECAO, children=[
        html.Div([
            html.Span("3", style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "marginRight": f"{S*2}px"}),
            html.H2("Avaliação da prioridade", style={"margin": 0, "fontSize": "1.25rem", "fontWeight": "700"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"}),
        html.Div(id="container-perguntas", children=itens),
    ])


@app.callback(
    [Output("output-calculo", "children"), Output("confirm-salvo", "displayed", allow_duplicate=True)],
    Input("btn-calcular", "n_clicks"),
    State("store-analise", "data"), State("usuario_avaliador", "value"), State({"type": "resposta", "index": ALL}, "value"),
    State("perfil_solicitante", "value"), State("cadastro-id-projeto", "value"),
    prevent_initial_call=True,
)
def on_calcular(_n, data, usuario_avaliador, respostas, perfil_dd, id_projeto_dd):
    if not data:
        return html.Div("Nenhum resultado da estruturação com IA carregado.", style=ESTILO_ERRO), False
    if not (usuario_avaliador or "").strip():
        return html.Div("Informe o responsável pela avaliação.", style=ESTILO_ERRO), False
    perg = data.get("perguntas_avaliacao") or []
    pr = []
    for i, p in enumerate(perg):
        val = respostas[i] if i < len(respostas) else None
        if val is None:
            return html.Div("Responda todas as perguntas.", style=ESTILO_ERRO), False
        pr.append({"id_pergunta": p.get("id_pergunta", i + 1), "texto": p.get("texto", ""), "dimensao": p.get("dimensao", ""), "valor_resposta": val})
    ip = _id_projeto_dropdown_val(id_projeto_dd)
    if ip is None:
        return html.Div("Selecione um projeto ou use «+ Adicionar novo projeto» antes de salvar.", style=ESTILO_ERRO), False
    ps = (perfil_dd or "").strip()
    perfil_eff = ps if ps else None
    cad = {**(data.get("cadastro") or {}), "perfil_solicitante": perfil_eff, "id_projeto": ip}
    payload_final = {
        "id_requisito_ou_titulo": data.get("titulo_requisito", ""), "tipo_requisito": data.get("tipo_requisito", ""),
        "texto_original": cad.get("texto_original", ""), "descricao_requisito": data.get("descricao_requisito", ""),
        "objetivo": data.get("objetivo", ""), "finalidade": data.get("finalidade", ""), "usuario_avaliador": str(usuario_avaliador).strip(),
        "perfil_avaliador": perfil_eff, "respostas": pr, "cadastro": cad,
    }
    _r, err = api_salvar(payload_final)
    if err:
        return html.Div([html.P(err, style=ESTILO_ERRO), html.Pre(json.dumps({k: v for k, v in payload_final.items() if k != "cadastro"}, indent=2, ensure_ascii=False))]), False
    usr = str(usuario_avaliador).strip()
    evo, err_evo = api_evoluir_projeto(
        ip,
        "patch",
        motivo="Demanda priorizada registrada na matriz",
        usuario_responsavel=usr or None,
    )
    if err_evo:
        return html.Div([
            html.P("Dados salvos no banco.", style=ESTILO_SUCESSO),
            html.P(f"A versão do projeto não foi atualizada automaticamente: {err_evo}", style=ESTILO_ERRO),
        ]), True
    nv = (evo or {}).get("versao_atual")
    if nv:
        return html.Div(
            f"Salvo. Versão do projeto atualizada automaticamente para {nv} (patch).",
            style=ESTILO_SUCESSO,
        ), True
    return html.Div("Salvo.", style=ESTILO_SUCESSO), True


@app.callback(
    [
        Output("texto_original", "value"),
        Output("tipo_informado_usuario", "value"),
        Output("modulo_afetado", "value"),
        Output("contexto_negocio", "value"),
        Output("objetivo_desejado", "value"),
        Output("impacto_percebido_usuario", "value"),
        Output("frequencia_ocorrencia", "value"),
        Output("urgencia_percebida", "value"),
        Output("ha_contorno", "value"),
        Output("sistema_ou_produto", "value"),
        Output("perfil_solicitante", "value"),
        Output("confirm-salvo", "displayed", allow_duplicate=True),
        Output("store-analise", "data", allow_duplicate=True),
        Output("msg-analise", "children", allow_duplicate=True),
        Output("secao2-container", "children", allow_duplicate=True),
        Output("secao3-container", "children", allow_duplicate=True),
        Output("cadastro-id-projeto", "value"),
    ],
    Input("confirm-salvo", "submit_n_clicks"),
    prevent_initial_call=True,
)
def _form_reset_apos_salvar(_n):
    z = ("", "NAO_SEI", "", "", "", "", "", "", "", "", "")
    return list(z) + [False, None, "", "", "", None]


@app.callback(
    Output("perfil_solicitante", "options"),
    Input("store-perfil-solicitante-extra", "data"),
)
def _perfil_solicitante_opcoes_merge(extra):
    extra = extra or []
    if not isinstance(extra, list):
        extra = []
    limpos = []
    for x in extra:
        if not isinstance(x, dict):
            continue
        v = (x.get("value") or "").strip() if isinstance(x.get("value"), str) else x.get("value")
        if not v:
            continue
        v = str(v).strip()
        limpos.append({"label": x.get("label") or v, "value": v})
    return PERFIL_SOLICITANTE_OPCOES_BASE + limpos


@app.callback(
    Output("store-perfil-solicitante-extra", "data"),
    Output("cadastro-perfil-solicitante-novo", "value"),
    Output("perfil_solicitante", "value", allow_duplicate=True),
    Output("msg-perfil-solicitante-adicionar", "children"),
    Input("btn-adicionar-perfil-solicitante", "n_clicks"),
    State("cadastro-perfil-solicitante-novo", "value"),
    State("store-perfil-solicitante-extra", "data"),
    prevent_initial_call=True,
)
def _adicionar_perfil_solicitante_sessao(_n_clicks, texto, extra):
    extra = list(extra or [])
    if not isinstance(extra, list):
        extra = []
    label = (texto or "").strip()
    if not label:
        return no_update, "", no_update, html.Span("Digite um nome para o solicitante.", style=ESTILO_ERRO)
    slug = _slug_perfil_solicitante(label)
    if not slug:
        return no_update, "", no_update, html.Span("Use letras ou números no nome.", style=ESTILO_ERRO)
    vals_base = {
        str(o.get("value", "")).strip()
        for o in PERFIL_SOLICITANTE_OPCOES_BASE
        if o.get("value") is not None and str(o.get("value")).strip()
    }
    vals_extra = {
        str(o.get("value", "")).strip()
        for o in extra
        if isinstance(o, dict) and o.get("value") and str(o.get("value")).strip()
    }
    if slug in vals_base or slug in vals_extra:
        return (
            no_update,
            "",
            no_update,
            html.Span("Esse perfil já está na lista.", style={"color": CORES["text_muted"], "fontSize": "0.8125rem"}),
        )
    novo = {"label": label, "value": slug}
    return extra + [novo], "", slug, html.Span(f"«{label}» adicionado e selecionado.", style=ESTILO_SUCESSO)


if __name__ == "__main__":
    import os
    _port = int(os.environ.get("PORT", "8051"))
    app.run(debug=True, port=_port)
