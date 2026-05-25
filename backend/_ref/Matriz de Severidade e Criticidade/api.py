"""
API REST — Matriz de Priorização
Documentação Swagger em /docs
"""
import json
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
import google.generativeai as genai

from config import GEMINI_API_KEY
from prompts import montar_prompt_analise
from db.avaliacao_repo import salvar_avaliacao_completa, listar_atividades_priorizadas

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI(
    title="API Matriz de Priorização",
    description="API para análise de requisitos e priorização",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class OpcaoRespostaLikert(BaseModel):
    """Opção de resposta na escala Likert (1 a 5)."""

    rotulo: str = Field(..., description="Rótulo da opção")
    valor: int = Field(..., description="Valor numérico (1 a 5)")


class PerguntaAvaliacao(BaseModel):
    """Pergunta de avaliação com escala Likert contextual."""

    id_pergunta: int = Field(..., description="Identificador da pergunta")
    texto: str = Field(..., description="Texto da pergunta")
    dimensao: str = Field(..., description="CRITICIDADE, SEVERIDADE, ESFORCO ou VALOR")
    opcoes_resposta: list[OpcaoRespostaLikert] = Field(
        ...,
        description="5 opções Likert (rotulo, valor 1 a 5) contextualizadas à pergunta",
    )


class AnaliseRequisitoRequest(BaseModel):
    """Corpo da requisição para análise de requisito com contexto enriquecido."""

    texto_original: Optional[str] = Field(default=None, description="Descrição livre do problema ou melhoria")
    tipo_informado_usuario: Optional[str] = Field(
        default="NAO_SEI",
        description="O que o usuário acha que é: BUG, INCREMENTO ou NAO_SEI",
    )
    modulo_afetado: Optional[str] = Field(default=None, description="Parte do sistema envolvida (ex: checkout, autenticação)")
    contexto_negocio: Optional[str] = Field(default=None, description="Para que serve aquela parte no negócio")
    objetivo_desejado: Optional[str] = Field(default=None, description="O que deveria acontecer")
    impacto_percebido_usuario: Optional[str] = Field(default=None, description="Impacto percebido (opcional)")
    frequencia_ocorrencia: Optional[str] = Field(default=None, description="sempre, às vezes, raramente, não sei (opcional)")
    urgencia_percebida: Optional[str] = Field(default=None, description="baixa, média, alta, crítica (opcional)")
    ha_contorno: Optional[bool] = Field(default=None, description="Existe workaround? (opcional)")
    sistema_ou_produto: Optional[str] = Field(default=None, description="Produto/sistema ao qual pertence (opcional)")
    perfil_solicitante: Optional[str] = Field(default=None, description="usuário final, analista, gestor, desenvolvedor, suporte (opcional)")
    texto: Optional[str] = Field(default=None, description="(Compatibilidade) Alias para texto_original")

    @model_validator(mode="before")
    @classmethod
    def texto_ou_texto_original(cls, data):
        if isinstance(data, dict):
            t = data.get("texto_original") or data.get("texto") or ""
            data["texto_original"] = t.strip() if isinstance(t, str) else ""
        return data


class AnaliseRequisitoResponse(BaseModel):
    """Resposta estruturada da análise feita pela IA."""

    texto_original: str = Field(..., description="Texto enviado pelo usuário")
    titulo_requisito: str = Field(..., description="Título sugerido")
    descricao_requisito: str = Field(..., description="Descrição refinada")
    tipo_requisito: str = Field(..., description="BUG ou INCREMENTO")
    objetivo: str = Field(..., description="Objetivo do requisito")
    finalidade: str = Field(..., description="Finalidade do requisito")
    perguntas_avaliacao: list[PerguntaAvaliacao] = Field(
        ...,
        description="Perguntas com dimensão, eixo e coordenada para cálculo da matriz",
    )


@app.get("/")
def root():
    """Raiz da API."""
    return {"mensagem": "API Matriz de Priorização", "docs": "/docs"}


def _extrair_json(texto: str) -> dict | None:
    """Extrai JSON do texto retornado pela IA (pode vir com markdown)."""
    texto = texto.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", texto)
    if match:
        texto = match.group(1)
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return None


@app.post(
    "/api/v1/requisitos/analise",
    response_model=AnaliseRequisitoResponse,
    summary="Analisar requisito com IA",
    description="Envia um requisito em linguagem natural para análise da IA (Gemini).",
)
def analisar_requisito(req: AnaliseRequisitoRequest):
    """
    Analisa o requisito e retorna requisito estruturado e perguntas de avaliação
    com vínculo explícito (dimensao, eixo_matriz, coordenada_relacionada).
    """
    texto = (req.texto_original or req.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="O campo texto_original não pode ser vazio")

    try:
        payload = {
            "texto_original": texto,
            "tipo_informado_usuario": req.tipo_informado_usuario or "NAO_SEI",
            "modulo_afetado": req.modulo_afetado,
            "contexto_negocio": req.contexto_negocio,
            "objetivo_desejado": req.objetivo_desejado,
            "impacto_percebido_usuario": req.impacto_percebido_usuario,
            "frequencia_ocorrencia": req.frequencia_ocorrencia,
            "urgencia_percebida": req.urgencia_percebida,
            "ha_contorno": req.ha_contorno,
            "sistema_ou_produto": req.sistema_ou_produto,
            "perfil_solicitante": req.perfil_solicitante,
        }
        prompt = montar_prompt_analise(payload)
        config = {"response_mime_type": "application/json"}
        response = model.generate_content(prompt, generation_config=config)
        data = _extrair_json(response.text)

        if not data:
            raise HTTPException(
                status_code=502,
                detail="A IA não retornou JSON válido. Resposta: " + response.text[:500],
            )

        # Aceita snake_case ou camelCase
        titulo = data.get("titulo_requisito") or data.get("tituloRequisito", "")
        descricao = data.get("descricao_requisito") or data.get("descricaoRequisito", "")
        tipo = (data.get("tipo_requisito") or data.get("tipoRequisito", "INCREMENTO")).upper()
        objetivo = data.get("objetivo", "")
        finalidade = data.get("finalidade", "")
        raw_perguntas = data.get("perguntas_avaliacao") or data.get("perguntasAvaliacao", [])

        ESCALA_LIKERT_PADRAO = [
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
                raw_opcoes = ESCALA_LIKERT_PADRAO
            opcoes = [
                OpcaoRespostaLikert(rotulo=str(o.get("rotulo", "")), valor=int(o.get("valor", 0)))
                for o in raw_opcoes[:5]
            ]
            perguntas.append(
                PerguntaAvaliacao(
                    id_pergunta=int(p.get("id_pergunta", 0)),
                    texto=str(p.get("texto", "")),
                    dimensao=str(p.get("dimensao", "")).upper(),
                    opcoes_resposta=opcoes,
                )
            )

        return AnaliseRequisitoResponse(
            texto_original=texto,
            titulo_requisito=titulo,
            descricao_requisito=descricao,
            tipo_requisito=tipo,
            objetivo=objetivo,
            finalidade=finalidade,
            perguntas_avaliacao=perguntas,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro na IA: {str(e)}")


class RespostaAvaliacaoPayload(BaseModel):
    """Uma resposta da avaliação Likert."""
    id_pergunta: int
    texto: str = ""
    dimensao: str = ""
    valor_resposta: int


class SalvarAvaliacaoRequest(BaseModel):
    """Corpo para salvar avaliação completa no banco."""
    id_requisito_ou_titulo: str = Field(..., description="Título do requisito")
    tipo_requisito: str = Field(..., description="BUG ou INCREMENTO")
    texto_original: str = Field(default="", description="Texto original do cadastro")
    descricao_requisito: str = Field(default="", description="Descrição refinada pela IA")
    objetivo: str = Field(default="", description="Objetivo")
    finalidade: str = Field(default="", description="Finalidade")
    usuario_avaliador: str = Field(..., description="Nome de quem marcou as respostas")
    perfil_avaliador: Optional[str] = Field(default=None, description="Perfil de quem avaliou")
    respostas: list[RespostaAvaliacaoPayload] = Field(..., description="Respostas às perguntas")
    cadastro: Optional[dict] = Field(default=None, description="Dados do cadastro inicial")


class AtividadePriorizada(BaseModel):
    """Item da lista de atividades para visualização nos gráficos."""
    id: int
    titulo: str = ""
    tipo_requisito: str = Field(..., description="BUG ou INCREMENTO")
    coordenada_x: float = Field(..., description="Criticidade (bugs) ou Esforço (incrementos)")
    coordenada_y: float = Field(..., description="Severidade (bugs) ou Valor (incrementos)")
    score: float = Field(..., description="coordenada_x * coordenada_y")
    prioridade_categorica: str = Field(..., description="ALTA, MEDIA ou BAIXA")
    status_atual: str = Field(default="AVALIADO", description="Status no fluxo (ex.: AVALIADO, EM_DESENVOLVIMENTO)")


@app.get(
    "/api/v1/requisitos/atividades",
    response_model=list[AtividadePriorizada],
    summary="Listar atividades priorizadas",
    description="Retorna todas as atividades já avaliadas com coordenadas para os gráficos (bugs e incrementos).",
)
def listar_atividades():
    """Lista atividades com coordenadas para matriz de bugs (Criticidade x Severidade) e de incrementos (Esforço x Valor)."""
    try:
        return listar_atividades_priorizadas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar atividades: {str(e)}")


@app.post(
    "/api/v1/requisitos/salvar-avaliacao",
    summary="Salvar avaliação no banco",
    description="Persiste entrada bruta, requisito estruturado, avaliação e respostas, incluindo quem avaliou.",
)
def salvar_avaliacao(req: SalvarAvaliacaoRequest):
    """
    Salva todos os dados da avaliação no banco: cadastro, requisito estruturado,
    avaliação (com usuário avaliador) e cada resposta às perguntas.
    """
    try:
        cadastro = req.cadastro or {}
        respostas = [{"id_pergunta": r.id_pergunta, "texto": r.texto, "dimensao": r.dimensao, "valor_resposta": r.valor_resposta} for r in req.respostas]
        resultado = salvar_avaliacao_completa(
            texto_original=req.texto_original,
            titulo_requisito=req.id_requisito_ou_titulo,
            descricao_requisito=req.descricao_requisito,
            tipo_requisito=(req.tipo_requisito or "INCREMENTO").upper(),
            objetivo=req.objetivo,
            finalidade=req.finalidade,
            usuario_avaliador=req.usuario_avaliador,
            perfil_avaliador=req.perfil_avaliador,
            respostas=respostas,
            cadastro=cadastro,
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
