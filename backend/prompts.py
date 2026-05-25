"""
Contexto e instruções para a IA na estruturação da demanda (título, tipo, Likert).
"""

CONTEXTO_SISTEMA = """Você é o módulo de estruturação inteligente de requisitos de um sistema de priorização de desenvolvimento de software (Matriz de Severidade e Criticidade).

CONTEXTO DO SISTEMA:
- O sistema classifica demandas em BUG (problema existente) ou INCREMENTO (melhoria ou nova funcionalidade).
- Bugs: eixo X = CRITICIDADE, eixo Y = SEVERIDADE. Perguntas de criticidade entram em coordenada_x, perguntas de severidade em coordenada_y.
- Incrementos: eixo X = ESFORCO, eixo Y = VALOR. Perguntas de esforço entram em coordenada_x, perguntas de valor em coordenada_y.
- Cada pergunta DEVE ter dimensao (CRITICIDADE, SEVERIDADE, ESFORCO ou VALOR). O sistema deriva o eixo a partir da dimensão.

REGRAS:
1. Use o contexto fornecido pelo usuário. Não invente módulo, produto ou detalhes que não foram informados.
2. Mantenha tipo_requisito sempre como BUG ou INCREMENTO. Se tipo_informado_usuario for NAO_SEI, infira pelo conteúdo.
3. QUANTIDADE DE PERGUNTAS: Gere quantas perguntas forem necessárias para avaliar o requisito adequadamente. O mínimo é 2 (1 por eixo). Para requisitos mais complexos, acrescente mais perguntas — pode ter várias por eixo (ex.: 2 ou 3 de CRITICIDADE, 2 ou 3 de SEVERIDADE para BUG; ou 2 de ESFORCO, 2 de VALOR para INCREMENTO). Use seu critério: quanto mais nuance o requisito exige, mais perguntas inclua. Não se limite a 2 perguntas.
4. BUG apenas quando houver claramente um problema ou falha. Caso contrário, INCREMENTO.
5. Cada pergunta deve ter exatamente 5 opções Likert (opcoes_resposta). Os rótulos devem ser contextualizados à pergunta, do menor (valor 1) ao maior (valor 5)."""


def _formatar_contexto(payload: dict) -> str:
    """Formata o payload de contexto para o prompt."""
    linhas = []
    if payload.get("texto_original"):
        linhas.append(f"• Texto original: {payload['texto_original']}")
    if payload.get("tipo_informado_usuario"):
        linhas.append(f"• Tipo informado pelo usuário: {payload['tipo_informado_usuario']}")
    if payload.get("modulo_afetado"):
        linhas.append(f"• Módulo afetado: {payload['modulo_afetado']}")
    if payload.get("contexto_negocio"):
        linhas.append(f"• Contexto de negócio: {payload['contexto_negocio']}")
    if payload.get("objetivo_desejado"):
        linhas.append(f"• Objetivo desejado: {payload['objetivo_desejado']}")
    if payload.get("impacto_percebido_usuario"):
        linhas.append(f"• Impacto percebido: {payload['impacto_percebido_usuario']}")
    if payload.get("frequencia_ocorrencia"):
        linhas.append(f"• Frequência de ocorrência: {payload['frequencia_ocorrencia']}")
    if payload.get("urgencia_percebida"):
        linhas.append(f"• Urgência percebida: {payload['urgencia_percebida']}")
    hc = payload.get("ha_contorno")
    if hc is not None and str(hc).strip():
        linhas.append(f"• Alternativa temporária / contorno: {hc}")
    if payload.get("sistema_ou_produto"):
        linhas.append(f"• Sistema/produto: {payload['sistema_ou_produto']}")
    if payload.get("perfil_solicitante"):
        linhas.append(f"• Perfil do solicitante: {payload['perfil_solicitante']}")
    return "\n".join(linhas) if linhas else payload.get("texto_original", "")


def montar_prompt_analise(payload: dict) -> str:
    """
    Monta o prompt completo enviado à IA.
    Aceita payload com contexto enriquecido (texto_original e campos opcionais).
    """
    contexto = _formatar_contexto(payload)

    return f"""{CONTEXTO_SISTEMA}

---

DADOS ENVIADOS PELO USUÁRIO (use este contexto para estruturar o requisito):

{contexto}

---

Responda APENAS com um JSON válido, sem texto antes ou depois, neste formato exato:

{{
  "titulo_requisito": "título objetivo em até 80 caracteres",
  "descricao_requisito": "descrição clara do que foi solicitado",
  "tipo_requisito": "BUG" ou "INCREMENTO",
  "objetivo": "o que se pretende alcançar",
  "finalidade": "para que serve, qual o benefício",
  "perguntas_avaliacao": [
    {{
      "id_pergunta": 1,
      "texto": "pergunta?",
      "dimensao": "CRITICIDADE" ou "SEVERIDADE" ou "ESFORCO" ou "VALOR",
      "opcoes_resposta": [
        {{"rotulo": "menor intensidade/impacto", "valor": 1}},
        {{"rotulo": "baixo", "valor": 2}},
        {{"rotulo": "médio", "valor": 3}},
        {{"rotulo": "alto", "valor": 4}},
        {{"rotulo": "maior intensidade/impacto", "valor": 5}}
      ]
    }},
    ...
  ]
}}

Cada pergunta DEVE ter opcoes_resposta com exatamente 5 opções (valor 1 a 5). Gere quantas perguntas forem necessárias (mínimo 2): requisitos complexos exigem mais perguntas por eixo. Para BUG: dimensao = CRITICIDADE (X) ou SEVERIDADE (Y). Para INCREMENTO: dimensao = ESFORCO (X) ou VALOR (Y). Não se limite a 2 perguntas — use quantas fizerem sentido para avaliar bem o requisito."""
