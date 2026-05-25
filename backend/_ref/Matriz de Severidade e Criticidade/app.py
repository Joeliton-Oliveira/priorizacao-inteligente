"""
Front-end Dash — Priorização Inteligente de Requisitos
Fluxo: cadastro → análise pela IA → respostas Likert → persistência.
Página de visualização: Atividades priorizadas (gráficos de bugs e incrementos).
"""
import json
from dash import Dash, dcc, html, Input, Output, State, ALL, clientside_callback, no_update, callback_context
import plotly.graph_objs as go

from services.api_client import analisar_requisito as api_analisar, salvar_avaliacao as api_salvar, listar_atividades as api_listar_atividades

# Modelo padrão de JSON — mesmos pontos do formulário. Chaves _label_* são só referência (ignoradas ao aplicar).
MODELO_JSON_PADRAO = """{
  "_label_texto_original": "Descrição inicial da demanda — Explique o problema ou a melhoria do jeito que você pensou. Ex.: Quando o cliente tenta finalizar a compra, o botão não responde...",
  "texto_original": "",
  "_label_tipo": "Tipo da demanda — BUG, INCREMENTO ou NAO_SEI (Não sei informar)",
  "tipo_informado_usuario": "NAO_SEI",
  "_label_modulo": "Área do sistema envolvida — Ex.: checkout",
  "modulo_afetado": "",
  "_label_contexto": "Importância dessa área para o negócio",
  "contexto_negocio": "",
  "_label_objetivo": "Resultado esperado — O que deveria acontecer corretamente?",
  "objetivo_desejado": "",
  "_label_impacto": "Impacto percebido da demanda",
  "impacto_percebido_usuario": "",
  "_label_frequencia": "Com que frequência isso acontece? — sempre, as_vezes, raramente, nao_sei ou vazio",
  "frequencia_ocorrencia": "",
  "_label_urgencia": "Qual a urgência? — baixa, media, alta, critica ou vazio",
  "urgencia_percebida": "",
  "_label_contorno": "Existe alguma alternativa temporária? — true, false ou null",
  "ha_contorno": null,
  "_label_sistema": "Sistema ou produto relacionado",
  "sistema_ou_produto": "",
  "_label_perfil": "Quem está solicitando? — usuario_final, analista, gestor, desenvolvedor, suporte ou vazio",
  "perfil_solicitante": ""
}"""

# Design system
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
R = 10  # border-radius
S = 8   # espaçamento base (px)

ESTILO_APP = {
    "fontFamily": '"Inter", "Segoe UI", system-ui, sans-serif',
    "backgroundColor": CORES["bg"],
    "minHeight": "100vh",
    "padding": f"{S*4}px 0",
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
ESTILO_SUCESSO = {"color": CORES["success"], "marginTop": f"{S}px", "fontSize": "0.875rem"}
ESTILO_TABELA = {"padding": f"{S}px {S*2}px", "border": f"1px solid {CORES['border']}", "textAlign": "left"}

app = Dash(__name__, title="Priorização Inteligente de Requisitos")
app.config.suppress_callback_exceptions = True


def _bloco_area_json():
    """Bloco da área 'Preencher via JSON': orientação, referência dos campos, textarea, botões e mensagem."""
    ref_campos = [
        ("texto_original", "Descrição inicial da demanda"),
        ("tipo_informado_usuario", "Tipo da demanda (BUG, INCREMENTO, NAO_SEI)"),
        ("modulo_afetado", "Área do sistema envolvida"),
        ("contexto_negocio", "Importância dessa área para o negócio"),
        ("objetivo_desejado", "Resultado esperado"),
        ("impacto_percebido_usuario", "Impacto percebido da demanda"),
        ("frequencia_ocorrencia", "Com que frequência? (sempre, as_vezes, raramente, nao_sei ou \"\")"),
        ("urgencia_percebida", "Qual a urgência? (baixa, media, alta, critica ou \"\")"),
        ("ha_contorno", "Existe alternativa temporária? (true, false ou null)"),
        ("sistema_ou_produto", "Sistema ou produto relacionado"),
        ("perfil_solicitante", "Quem está solicitando? (usuario_final, analista, gestor, etc. ou \"\")"),
    ]
    return html.Div([
        html.P(
            "Preencha o JSON com os mesmos pontos do formulário e clique em \"Aplicar JSON\" para preencher os campos. Não envia para a API.",
            style={"fontSize": "14px", "color": CORES["text_muted"], "marginBottom": f"{S}px"},
        ),
        html.Details([
            html.Summary("Referência: chave JSON → campo do formulário", style={"fontSize": "13px", "fontWeight": "600", "color": CORES["text"], "cursor": "pointer"}),
            html.Ul(
                [html.Li([html.Code(k, style={"fontSize": "12px"}), f" → {label}"], style={"fontSize": "12px", "color": CORES["text_muted"], "marginBottom": f"{S//2}px"}) for k, label in ref_campos],
                style={"marginTop": f"{S}px", "marginBottom": f"{S*2}px", "paddingLeft": f"{S*3}px"},
            ),
        ], style={"marginBottom": f"{S*2}px"}),
        dcc.Textarea(
            id="textarea-json",
            value=MODELO_JSON_PADRAO,
            style={"width": "100%", "minHeight": "200px", "fontFamily": "monospace", "fontSize": "13px"},
            placeholder="JSON do formulário",
        ),
        html.Div([
            html.Button("Copiar modelo JSON", id="btn-copiar-json", n_clicks=0, style={**ESTILO_BOTAO, "backgroundColor": CORES["text_muted"]}),
            html.Button("Aplicar JSON", id="btn-aplicar-json", n_clicks=0, style=ESTILO_BOTAO),
            html.Button("Limpar JSON", id="btn-limpar-json", n_clicks=0, style={**ESTILO_BOTAO, "backgroundColor": CORES["text_muted"]}),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "marginTop": f"{S*2}px"}),
        html.Div(id="msg-json", style={"marginTop": f"{S}px", "fontSize": "14px"}),
    ], style={"marginTop": f"{S*3}px", "padding": f"{S*2}px", "border": f"1px solid {CORES['border']}", "borderRadius": "8px", "backgroundColor": "#fafafa"})


# Seção 1 — Cadastro inicial
layout_secao1 = html.Div([
    html.Div([
        html.Span("1", style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "fontSize": "0.875rem", "marginRight": f"{S*2}px"}),
        html.H2("Identificação da Demanda", style={"margin": 0, "fontSize": "1.25rem", "fontWeight": "700", "color": CORES["text"]}),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"}),
    html.Div([
        html.Label("Descrição inicial da demanda", style=ESTILO_LABEL),
        html.Span("Explique o problema ou a melhoria do jeito que você pensou.", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
        dcc.Textarea(id="texto_original", placeholder="Ex.: Quando o cliente tenta finalizar a compra, o botão não responde...", style={**ESTILO_INPUT, "minHeight": "100px", "resize": "vertical"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Tipo da demanda", style=ESTILO_LABEL),
        html.Span("Como você classifica essa demanda?", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
        dcc.Dropdown(id="tipo_informado_usuario", options=[
            {"label": "Bug", "value": "BUG"},
            {"label": "Melhoria / nova funcionalidade", "value": "INCREMENTO"},
            {"label": "Não sei informar", "value": "NAO_SEI"},
        ], value="NAO_SEI", clearable=False),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Área do sistema envolvida", style=ESTILO_LABEL),
        dcc.Input(id="modulo_afetado", type="text", placeholder="Ex.: checkout", style=ESTILO_INPUT),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Importância dessa área para o negócio", style=ESTILO_LABEL),
        html.Span("Explique por que essa parte é importante para a operação ou para o negócio.", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
        dcc.Textarea(id="contexto_negocio", placeholder="Explique por que essa parte é importante para a operação ou para o negócio.", style={**ESTILO_INPUT, "minHeight": "72px"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Resultado esperado", style=ESTILO_LABEL),
        html.Span("O que deveria acontecer corretamente?", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
        dcc.Textarea(id="objetivo_desejado", placeholder="O que deveria acontecer corretamente?", style={**ESTILO_INPUT, "minHeight": "72px"}),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Impacto percebido da demanda", style=ESTILO_LABEL),
        html.Span("Descreva o impacto percebido, se houver.", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
        dcc.Input(id="impacto_percebido_usuario", type="text", placeholder="Descreva o impacto percebido, se houver.", style=ESTILO_INPUT),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Com que frequência isso acontece?", style=ESTILO_LABEL),
        dcc.Dropdown(
            id="frequencia_ocorrencia",
            options=[
                {"label": "Selecione", "value": ""},
                {"label": "Sempre", "value": "sempre"},
                {"label": "Com frequência", "value": "as_vezes"},
                {"label": "Raramente", "value": "raramente"},
                {"label": "Não sei informar", "value": "nao_sei"},
            ],
            value="",
            clearable=True,
        ),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Qual a urgência dessa demanda?", style=ESTILO_LABEL),
        dcc.Dropdown(
            id="urgencia_percebida",
            options=[
                {"label": "Selecione", "value": ""},
                {"label": "Baixa", "value": "baixa"},
                {"label": "Média", "value": "media"},
                {"label": "Alta", "value": "alta"},
                {"label": "Crítica", "value": "critica"},
            ],
            value="",
            clearable=True,
        ),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Existe alguma alternativa temporária?", style=ESTILO_LABEL),
        dcc.Dropdown(
            id="ha_contorno",
            options=[
                {"label": "Selecione", "value": None},
                {"label": "Sim", "value": True},
                {"label": "Não", "value": False},
            ],
            value=None,
            clearable=True,
        ),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Sistema ou produto relacionado", style=ESTILO_LABEL),
        html.Span("Informe o sistema ou produto, se desejar.", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
        dcc.Input(id="sistema_ou_produto", type="text", placeholder="Informe o sistema ou produto, se desejar.", style=ESTILO_INPUT),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Label("Quem está solicitando essa demanda?", style=ESTILO_LABEL),
        dcc.Dropdown(
            id="perfil_solicitante",
            options=[
                {"label": "Selecione", "value": ""},
                {"label": "Usuário final", "value": "usuario_final"},
                {"label": "Analista", "value": "analista"},
                {"label": "Gestor", "value": "gestor"},
                {"label": "Desenvolvedor", "value": "desenvolvedor"},
                {"label": "Suporte", "value": "suporte"},
            ],
            value="",
            clearable=True,
        ),
    ], style=ESTILO_CAMPO),
    html.Div([
        html.Button("Analisar e estruturar com IA", id="btn-analisar", n_clicks=0, style=ESTILO_BOTAO, className="dash-button"),
        html.Button("Preencher via JSON", id="btn-preencher-json", n_clicks=0, style={**ESTILO_BOTAO, "backgroundColor": CORES["text_muted"], "marginLeft": f"{S*2}px"}),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "marginTop": f"{S*2}px"}),
    html.Div(id="msg-analise"),
    html.Div(id="area-json-container"),
    html.Div(id="feedback-copiar", style={"marginTop": f"{S}px", "fontSize": "14px", "color": CORES["success"], "minHeight": "1.5em"}),
],
    style=ESTILO_SECAO,
)


def _layout_cadastro():
    """Layout da página de cadastro e avaliação."""
    return html.Div([
        html.Header([
            html.H1("Priorização Inteligente de Requisitos", style={
                "textAlign": "center", "marginBottom": f"{S*2}px", "fontSize": "1.75rem",
                "fontWeight": "700", "color": CORES["text"],
            }),
            html.P("Descreva a demanda, analise com IA e avalie para definir a prioridade.", style={
                "textAlign": "center", "color": CORES["text_muted"], "margin": 0, "fontSize": "0.9375rem",
            }),
            html.Div([
                dcc.Link("Atividades priorizadas", href="/atividades", style={"fontSize": "0.9375rem", "color": CORES["primary"]}),
            ], style={"textAlign": "center", "marginTop": f"{S}px"}),
        ], style={"marginBottom": f"{S*5}px"}),
        html.Div([layout_secao1], style={"maxWidth": "720px", "margin": "0 auto", "padding": f"0 {S*3}px"}),
        dcc.Store(id="store-analise"),
        dcc.Store(id="store-json-modelo", data=MODELO_JSON_PADRAO),
        html.Div(id="secao2-container", style={"maxWidth": "720px", "margin": "0 auto", "padding": f"0 {S*3}px"}),
        html.Div(id="secao3-container", style={"maxWidth": "720px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
        dcc.ConfirmDialog(id="confirm-salvo", message="Dados persistidos no banco de dados.", submit_n_clicks=0),
    ])


def _layout_atividades_corpo():
    """Corpo da página de atividades (resumo, gráficos, tabela) — IDs para callback."""
    return [
        html.Div(id="atividades-resumo", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px", "marginBottom": f"{S*4}px"}),
        html.Div(id="atividades-grafico-bugs", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px", "marginBottom": f"{S*4}px"}),
        html.Div(id="atividades-grafico-incrementos", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px", "marginBottom": f"{S*4}px"}),
        html.Div(id="atividades-tabela", style={"maxWidth": "900px", "margin": "0 auto", "padding": f"0 {S*3}px {S*5}px"}),
    ]


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="store-atividades"),
    html.Div(id="cadastro-wrapper", children=_layout_cadastro()),
    html.Div(
        id="atividades-wrapper",
        style={"display": "none"},
        children=[
            html.Header([
                html.Div([dcc.Link("← Voltar ao cadastro", href="/", style={"fontSize": "0.9375rem", "color": CORES["primary"]})], style={"marginBottom": f"{S*2}px"}),
                html.H1("Atividades Priorizadas", style={
                    "textAlign": "center", "marginBottom": f"{S*2}px", "fontSize": "1.75rem",
                    "fontWeight": "700", "color": CORES["text"],
                }),
                html.P("Visualização das atividades já avaliadas nas matrizes de priorização.", style={
                    "textAlign": "center", "color": CORES["text_muted"], "margin": 0, "fontSize": "0.9375rem",
                }),
            ], style={"marginBottom": f"{S*4}px"}),
            *_layout_atividades_corpo(),
        ],
    ),
], style=ESTILO_APP)


@app.callback(
    [
        Output("cadastro-wrapper", "style"),
        Output("atividades-wrapper", "style"),
        Output("store-atividades", "data"),
    ],
    Input("url", "pathname"),
)
def _router(pathname):
    if pathname == "/atividades":
        data, err = api_listar_atividades()
        payload = data if data is not None else []
        return {"display": "none"}, {"display": "block"}, payload
    return {"display": "block"}, {"display": "none"}, no_update


@app.callback(
    [
        Output("atividades-resumo", "children"),
        Output("atividades-grafico-bugs", "children"),
        Output("atividades-grafico-incrementos", "children"),
        Output("atividades-tabela", "children"),
    ],
    Input("store-atividades", "data"),
)
def _render_atividades(data):
    if not data:
        empty = html.Div("Nenhuma atividade carregada.", style={"color": CORES["text_muted"], "padding": f"{S*3}px"})
        return empty, empty, empty, empty
    bugs = [a for a in data if (a.get("tipo_requisito") or "").upper() == "BUG"]
    incrementos = [a for a in data if (a.get("tipo_requisito") or "").upper() == "INCREMENTO"]
    concluidas = sum(1 for a in data if (a.get("status_atual") or "").upper() in ("CONCLUIDO", "EM_DESENVOLVIMENTO", "AVALIADO"))
    pendentes = max(0, len(data) - concluidas)

    cards = html.Div([
        html.Div([
            html.Div(str(len(bugs)), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["bug"]}),
            html.Div("Bugs", style={"fontSize": "0.875rem", "color": CORES["text_muted"]}),
        ], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
        html.Div([
            html.Div(str(len(incrementos)), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["feature"]}),
            html.Div("Incrementos", style={"fontSize": "0.875rem", "color": CORES["text_muted"]}),
        ], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
        html.Div([
            html.Div(str(concluidas), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["success"]}),
            html.Div("Concluídas", style={"fontSize": "0.875rem", "color": CORES["text_muted"]}),
        ], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
        html.Div([
            html.Div(str(pendentes), style={"fontSize": "1.75rem", "fontWeight": "700", "color": CORES["text_muted"]}),
            html.Div("Pendentes", style={"fontSize": "0.875rem", "color": CORES["text_muted"]}),
        ], style={**ESTILO_SECAO, "flex": "1", "minWidth": "140px", "textAlign": "center"}),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": f"{S*2}px", "justifyContent": "center"})

    def _scatter(tipo, eixo_x, eixo_y, titulo_x, titulo_y):
        itens = bugs if tipo == "BUG" else incrementos
        if not itens:
            return html.Div(f"Nenhum {tipo.lower()} avaliado.", style={"color": CORES["text_muted"], "padding": f"{S*3}px"})
        xs = [a.get("coordenada_x", 0) for a in itens]
        ys = [a.get("coordenada_y", 0) for a in itens]
        textos = [
            f"Título: {a.get('titulo', '')}<br>Tipo: {a.get('tipo_requisito', '')}<br>{titulo_x}: {a.get('coordenada_x')}<br>{titulo_y}: {a.get('coordenada_y')}<br>Score: {a.get('score')}<br>Prioridade: {a.get('prioridade_categorica')}<br>Status: {a.get('status_atual')}"
            for a in itens
        ]
        fig = go.Figure(data=[go.Scatter(
            x=xs, y=ys, mode="markers", text=[a.get("titulo", "") for a in itens],
            hovertext=textos, hoverinfo="text", marker=dict(size=12, color=CORES["bug"] if tipo == "BUG" else CORES["feature"]),
        )])
        fig.update_layout(
            title=f"Matriz de {tipo}s",
            xaxis_title=titulo_x, yaxis_title=titulo_y,
            margin=dict(l=60, r=40, t=50, b=50), height=400, template="plotly_white",
        )
        return dcc.Graph(figure=fig, config={"displayModeBar": True})

    grafico_bugs = _scatter("BUG", "Criticidade", "Severidade", "Criticidade", "Severidade")
    grafico_incrementos = _scatter("INCREMENTO", "Esforço", "Valor", "Esforço", "Valor")

    rows = [
        html.Tr([
            html.Td(a.get("id"), style=ESTILO_TABELA),
            html.Td(a.get("titulo", "")[:50] + ("..." if len(a.get("titulo", "")) > 50 else ""), style=ESTILO_TABELA),
            html.Td(a.get("tipo_requisito", ""), style=ESTILO_TABELA),
            html.Td(a.get("coordenada_x"), style=ESTILO_TABELA),
            html.Td(a.get("coordenada_y"), style=ESTILO_TABELA),
            html.Td(a.get("score"), style=ESTILO_TABELA),
            html.Td(a.get("prioridade_categorica", ""), style=ESTILO_TABELA),
            html.Td(a.get("status_atual", ""), style=ESTILO_TABELA),
        ])
        for a in data
    ]
    tabela = html.Div([
        html.H3("Lista de atividades", style={"fontSize": "1.125rem", "marginBottom": f"{S*2}px", "color": CORES["text"]}),
        html.Table([
            html.Thead(html.Tr([
                html.Th("ID", style=ESTILO_TABELA), html.Th("Título", style=ESTILO_TABELA), html.Th("Tipo", style=ESTILO_TABELA),
                html.Th("X", style=ESTILO_TABELA), html.Th("Y", style=ESTILO_TABELA), html.Th("Score", style=ESTILO_TABELA),
                html.Th("Prioridade", style=ESTILO_TABELA), html.Th("Status", style=ESTILO_TABELA),
            ])),
            html.Tbody(rows),
        ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.875rem"}),
    ], style={**ESTILO_SECAO})

    return cards, grafico_bugs, grafico_incrementos, tabela


@app.callback(
    [Output("store-analise", "data"), Output("msg-analise", "children"), Output("secao2-container", "children"), Output("secao3-container", "children")],
    Input("btn-analisar", "n_clicks"),
    [
        State("texto_original", "value"),
        State("tipo_informado_usuario", "value"),
        State("modulo_afetado", "value"),
        State("contexto_negocio", "value"),
        State("objetivo_desejado", "value"),
        State("impacto_percebido_usuario", "value"),
        State("frequencia_ocorrencia", "value"),
        State("urgencia_percebida", "value"),
        State("ha_contorno", "value"),
        State("sistema_ou_produto", "value"),
        State("perfil_solicitante", "value"),
    ],
    prevent_initial_call=True,
)
def on_analisar(n_clicks, texto, tipo, modulo, contexto, objetivo, impacto, frequencia, urgencia, contorno, sistema, perfil):
    if not texto or not str(texto).strip():
        return None, html.Div("Preencha o texto original.", style=ESTILO_ERRO), "", ""

    payload = {
        "texto_original": str(texto).strip(),
        "tipo_informado_usuario": tipo or "NAO_SEI",
        "modulo_afetado": modulo or None,
        "contexto_negocio": contexto or None,
        "objetivo_desejado": objetivo or None,
        "impacto_percebido_usuario": impacto or None,
        "frequencia_ocorrencia": frequencia or None,
        "urgencia_percebida": urgencia or None,
        "ha_contorno": contorno,
        "sistema_ou_produto": sistema or None,
        "perfil_solicitante": perfil or None,
    }
    payload = {k: v for k, v in payload.items() if v is not None and v != ""}

    data, erro = api_analisar(payload)
    if erro:
        return None, html.Div(erro, style=ESTILO_ERRO), "", ""

    cadastro = {
        "perfil_solicitante": perfil,
        "modulo_afetado": modulo,
        "contexto_negocio": contexto,
        "objetivo_desejado": objetivo,
        "sistema_ou_produto": sistema,
        "texto_original": str(texto).strip(),
    }
    data_completo = {**data, "cadastro": cadastro}
    secao2 = _render_secao2(data)
    secao3 = _render_secao3(data)
    return data_completo, html.Div("Análise concluída.", style=ESTILO_SUCESSO), secao2, secao3


@app.callback(
    Output("area-json-container", "children"),
    Input("btn-preencher-json", "n_clicks"),
    prevent_initial_call=True,
)
def _toggle_area_json(n_clicks):
    if n_clicks and n_clicks > 0:
        return _bloco_area_json()
    return None


def _valor_ha_contorno(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        if v.lower() in ("true", "1", "sim", "s"):
            return True
        if v.lower() in ("false", "0", "não", "nao", "n"):
            return False
    return None


def _aplicar_json_valores(valor_textarea):
    """Parse do textarea e retorno (11 valores, msg_json) ou (None*11, html_erro)."""
    raw = (valor_textarea or "").strip()
    if not raw:
        return None, html.Div("Digite ou cole um JSON.", style=ESTILO_ERRO)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, html.Div(f"JSON inválido: {e.msg}. Corrija e tente novamente.", style=ESTILO_ERRO)
    if not isinstance(data, dict):
        return None, html.Div("O JSON deve ser um objeto.", style=ESTILO_ERRO)
    texto = data.get("texto_original") or ""
    tipo = data.get("tipo_informado_usuario") or "NAO_SEI"
    modulo = data.get("modulo_afetado") or ""
    contexto = data.get("contexto_negocio") or ""
    objetivo = data.get("objetivo_desejado") or ""
    impacto = data.get("impacto_percebido_usuario") or ""
    frequencia = data.get("frequencia_ocorrencia") or ""
    urgencia = data.get("urgencia_percebida") or ""
    contorno = _valor_ha_contorno(data.get("ha_contorno"))
    sistema = data.get("sistema_ou_produto") or ""
    perfil = data.get("perfil_solicitante") or ""
    vals = (texto, tipo, modulo, contexto, objetivo, impacto, frequencia, urgencia, contorno, sistema, perfil)
    return vals, html.Div("JSON aplicado. Campos preenchidos.", style=ESTILO_SUCESSO)


@app.callback(
    Output("textarea-json", "value", allow_duplicate=True),
    Input("btn-limpar-json", "n_clicks"),
    prevent_initial_call=True,
)
def _limpar_json(n_clicks):
    if n_clicks and n_clicks > 0:
        return MODELO_JSON_PADRAO
    return None


clientside_callback(
    """
    function(n_clicks, model) {
        if (n_clicks && model) {
            try {
                navigator.clipboard.writeText(model);
                return "Copiado!";
            } catch (e) {
                return "Erro ao copiar.";
            }
        }
        return window.dash_clientside && window.dash_clientside.no_update !== undefined
            ? window.dash_clientside.no_update
            : undefined;
    }
    """,
    Output("feedback-copiar", "children"),
    Input("btn-copiar-json", "n_clicks"),
    State("store-json-modelo", "data"),
)


def _render_secao2(data: dict):
    t = (data.get("tipo_requisito") or "").upper().strip()
    tipo_label = "Bug" if t == "BUG" else "Incremento" if "INCREMENTO" in t or t == "FEATURE" else "—"
    tipo_cor = CORES["bug"] if t == "BUG" else CORES["feature"] if "INCREMENTO" in t or t == "FEATURE" else CORES["text_muted"]
    return html.Div(className="animate-fade-in", style=ESTILO_SECAO, children=[
        html.Div([
            html.Span("2", style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "fontSize": "0.875rem", "marginRight": f"{S*2}px"}),
            html.H2("Demanda estruturada pela IA", style={"margin": 0, "fontSize": "1.25rem", "fontWeight": "700", "color": CORES["text"]}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"}),
        html.Div([
            html.Span("Classificação: ", style={"fontSize": "0.9375rem", "color": CORES["text"]}),
            html.Span(tipo_label, style={"backgroundColor": tipo_cor, "color": "#fff", "padding": "4px 12px", "borderRadius": "6px", "fontSize": "0.9375rem", "fontWeight": "600"}),
        ], style={"marginBottom": f"{S*3}px", "padding": f"{S*2}px", "background": "#f8fafc", "borderLeft": f"4px solid {tipo_cor}", "borderRadius": f"{R}px", "border": f"1px solid {CORES['border']}"}),
        html.Div([
            html.Div([html.Strong("Título do requisito: ", style={"color": CORES["text_muted"], "fontWeight": "600"}), data.get("titulo_requisito", "—")], style={"marginBottom": f"{S}px", "lineHeight": "1.5"}),
            html.Div([html.Strong("Descrição estruturada: ", style={"color": CORES["text_muted"], "fontWeight": "600"}), data.get("descricao_requisito", "—")], style={"marginBottom": f"{S}px", "lineHeight": "1.5"}),
            html.Div([html.Strong("Objetivo do requisito: ", style={"color": CORES["text_muted"], "fontWeight": "600"}), data.get("objetivo", "—")], style={"marginBottom": f"{S}px", "lineHeight": "1.5"}),
            html.Div([html.Strong("Finalidade da demanda: ", style={"color": CORES["text_muted"], "fontWeight": "600"}), data.get("finalidade", "—")], style={"lineHeight": "1.5"}),
        ], style={"background": "#f8fafc", "padding": f"{S*3}px", "borderRadius": f"{R}px", "border": f"1px solid {CORES['border']}"}),
    ])


def _render_secao3(data: dict):
    perguntas = data.get("perguntas_avaliacao") or []
    if not perguntas:
        return html.Div()

    itens = [
        html.Div([
            html.Label("Responsável pela avaliação", style=ESTILO_LABEL),
            html.Span("Esse nome será usado para registrar quem respondeu à avaliação.", style={"fontSize": "0.8125rem", "color": CORES["text_muted"], "display": "block", "marginBottom": f"{S//2}px"}),
            dcc.Input(id="usuario_avaliador", type="text", placeholder="Nome do responsável pela avaliação", style=ESTILO_INPUT),
        ], style={**ESTILO_CAMPO, "marginBottom": f"{S*3}px"}),
    ]
    for i, p in enumerate(perguntas):
        opcoes = p.get("opcoes_resposta") or []
        opts = [{"label": f"{o.get('rotulo', '')} ({o.get('valor', '')})", "value": o.get("valor")} for o in opcoes if o.get("valor") is not None]
        itens.append(
            html.Div([
                html.P([
                    html.Strong(f"P{i+1}", style={"color": CORES["primary"], "marginRight": "6px"}),
                    p.get("texto", ""),
                    html.Span(f" [{p.get('dimensao', '')}]", style={"color": CORES["text_muted"], "fontSize": "0.8125rem"}),
                ], style={"marginBottom": f"{S}px", "lineHeight": "1.5"}),
                dcc.RadioItems(
                    id={"type": "resposta", "index": i},
                    options=opts,
                    value=None,
                    inline=True,
                    style={"marginBottom": f"{S}px"},
                ),
            ], style={"marginBottom": f"{S*3}px", "padding": f"{S*3}px", "border": f"1px solid {CORES['border']}", "borderRadius": f"{R}px", "background": "#fafbfc"})
        )

    itens.append(
        html.Div([
            html.Button("Salvar avaliação e posicionar na matriz", id="btn-calcular", n_clicks=0, style=ESTILO_BOTAO, className="dash-button"),
            html.Div(id="output-calculo", style={"marginTop": f"{S*2}px"}),
        ])
    )

    return html.Div(className="animate-fade-in", style=ESTILO_SECAO, children=[
        html.Div([
            html.Span("3", style={"display": "inline-flex", "alignItems": "center", "justifyContent": "center", "width": "28px", "height": "28px", "backgroundColor": CORES["primary"], "color": "#fff", "borderRadius": "50%", "fontWeight": "700", "fontSize": "0.875rem", "marginRight": f"{S*2}px"}),
            html.H2("Avaliação da prioridade", style={"margin": 0, "fontSize": "1.25rem", "fontWeight": "700", "color": CORES["text"]}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": f"{S*3}px"}),
        html.Div(id="container-perguntas", children=itens),
    ])


@app.callback(
    [Output("output-calculo", "children"), Output("confirm-salvo", "displayed", allow_duplicate=True)],
    Input("btn-calcular", "n_clicks"),
    State("store-analise", "data"),
    State("usuario_avaliador", "value"),
    State({"type": "resposta", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def on_calcular(n_clicks, data, usuario_avaliador, respostas):
    if not data:
        return html.Div("Nenhuma análise carregada.", style=ESTILO_ERRO), False

    if not usuario_avaliador or not str(usuario_avaliador).strip():
        return html.Div("Informe o responsável pela avaliação.", style=ESTILO_ERRO), False

    perguntas = data.get("perguntas_avaliacao") or []
    payload_respostas = []
    for i, p in enumerate(perguntas):
        val = respostas[i] if i < len(respostas) else None
        if val is None:
            return html.Div("Responda todas as perguntas antes de calcular.", style=ESTILO_ERRO), False
        payload_respostas.append({
            "id_pergunta": p.get("id_pergunta", i + 1),
            "texto": p.get("texto", ""),
            "dimensao": p.get("dimensao", ""),
            "valor_resposta": val,
        })

    payload_final = {
        "id_requisito_ou_titulo": data.get("titulo_requisito", ""),
        "tipo_requisito": data.get("tipo_requisito", ""),
        "texto_original": data.get("cadastro", {}).get("texto_original", ""),
        "descricao_requisito": data.get("descricao_requisito", ""),
        "objetivo": data.get("objetivo", ""),
        "finalidade": data.get("finalidade", ""),
        "usuario_avaliador": str(usuario_avaliador).strip(),
        "perfil_avaliador": data.get("cadastro", {}).get("perfil_solicitante"),
        "respostas": payload_respostas,
        "cadastro": data.get("cadastro", {}),
    }

    resultado, erro = api_salvar(payload_final)
    if erro:
        return html.Div([
            html.P(erro, style=ESTILO_ERRO),
            html.P("Payload gerado (não salvo):", style=ESTILO_LABEL),
            html.Pre(json.dumps({k: v for k, v in payload_final.items() if k != "cadastro"}, indent=2, ensure_ascii=False), style={"background": "#f8fafc", "padding": f"{S*2}px", "borderRadius": f"{R}px", "overflow": "auto", "fontSize": "0.8125rem", "border": f"1px solid {CORES['border']}"}),
        ]), False

    return "", True


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
        Output("msg-json", "children"),
        Output("confirm-salvo", "displayed", allow_duplicate=True),
        Output("store-analise", "data", allow_duplicate=True),
        Output("msg-analise", "children", allow_duplicate=True),
        Output("secao2-container", "children", allow_duplicate=True),
        Output("secao3-container", "children", allow_duplicate=True),
    ],
    [
        Input("btn-aplicar-json", "n_clicks"),
        Input("confirm-salvo", "submit_n_clicks"),
    ],
    State("textarea-json", "value"),
    prevent_initial_call=True,
)
def _form_update_or_reset(n_aplicar, n_confirm, valor_textarea):
    ctx = callback_context
    if not ctx.triggered:
        return [no_update] * 17
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "btn-aplicar-json":
        vals, msg = _aplicar_json_valores(valor_textarea)
        if vals is None:
            return [no_update] * 11 + [msg] + [no_update] * 5
        return list(vals) + [msg] + [no_update] * 5
    if trigger_id == "confirm-salvo":
        reset = (
            "",
            "NAO_SEI",
            "",
            "",
            "",
            "",
            "",
            "",
            None,
            "",
            "",
        )
        return list(reset) + [no_update] + [False, None, "", "", ""]
    return [no_update] * 17


if __name__ == "__main__":
    app.run(debug=True, port=8051)
