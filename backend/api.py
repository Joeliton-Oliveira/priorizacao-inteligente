"""
API REST — Matriz de Priorização
Documentação Swagger em /docs
"""
import os
from typing import Any, Literal, Optional
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from domain.exceptions import DomainError
from version import __version__ as APP_VERSION, RELEASE_DATE, parse_semver
from services import analise_ia_service
from services import avaliacao_service
from services import config_fila_service
from services import demanda_consulta_service
from services import documentacao_service
from services import fila_service
from services import kanban_status_service
from services import projetos_service

# Ordem dos grupos no Swagger / ReDoc (fluxo de negócio → operação).
OPENAPI_TAGS = [
    {
        "name": "Meta / Sistema",
        "description": "Saúde da API, identificação do serviço e metadados de release (fora do fluxo principal de negócio).",
    },
    {
        "name": "Projetos",
        "description": "Ciclo de vida de projetos: cadastro, listagem, status operacional, versão semântica e histórico.",
    },
    {
        "name": "Requisitos - Estruturação com IA e avaliação",
        "description": "Entrada da demanda, estruturação com IA (Gemini), persistência da avaliação Likert e listagem para a matriz de priorização.",
    },
    {
        "name": "Requisitos - Documentação por fase",
        "description": "Evidências documentais por fase (base dos gates de avanço no Kanban). Leitura e gravação por `fase_codigo`.",
    },
    {
        "name": "Kanban e Gates",
        "description": "Estado no fluxo operacional: alteração de status da atividade e consulta de gates documentais para avançar de coluna.",
    },
    {
        "name": "Fila de priorização",
        "description": "Ordenação operacional das atividades avaliadas (quadrante, distância ao canto ideal, vazão).",
    },
    {
        "name": "Calibragem",
        "description": "Leitura e persistência da configuração da fila e dos limites WIP usados no produto.",
    },
    {
        "name": "Demandas - Consulta consolidada",
        "description": "Visão 360 e auditoria para detalhar uma atividade sem depender de múltiplas telas e chamadas dispersas.",
    },
]

app = FastAPI(
    title="API Matriz de Priorização",
    description=(
        "API para estruturação da demanda com IA, matriz de severidade/criticidade, documentação por fase, "
        "Kanban com gates e fila de priorização. Os endpoints estão agrupados por domínio no Swagger."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=OPENAPI_TAGS,
)


@app.exception_handler(DomainError)
async def _domain_error_handler(_request, exc: DomainError):
    return JSONResponse(
        status_code=getattr(type(exc), "status_http", 500),
        content={"detail": exc.message},
    )


class OpcaoRespostaLikert(BaseModel):
    """Opção de resposta na escala Likert (1 a 5)."""

    rotulo: str = Field(..., description="Rótulo da opção")
    valor: int = Field(..., description="Valor numérico (1 a 5)")


class AppStatusResponse(BaseModel):
    """Metadados de release expostos para integração e health checks."""

    app_version: str = Field(..., description="Versão semântica (MAJOR.MINOR.PATCH)")
    release_date: str = Field(..., description="Data de release ISO (YYYY-MM-DD)")


class CriarProjetoRequest(BaseModel):
    """Cadastro de projeto novo (1.0.0) ou existente (versão informada)."""

    nome_projeto: str = Field(..., min_length=1, description="Nome do projeto")
    descricao: Optional[str] = Field(default=None, description="Descrição opcional")
    responsavel: Optional[str] = Field(default=None, description="Responsável / dono do registro")
    tipo_origem: Literal["novo", "existente"] = Field(
        ...,
        description="novo = inicia em 1.0.0; existente = usa versao_atual informada",
    )
    versao_atual: Optional[str] = Field(
        default=None,
        description="Obrigatório se tipo_origem=existente (MAJOR.MINOR.PATCH, ex.: 3.11.52)",
    )
    status_projeto: Literal["ativo", "arquivado", "descontinuado"] = Field(
        default="ativo",
        description="Estado operacional do projeto no cadastro",
    )

    @model_validator(mode="after")
    def validar_versao_existente(self):
        if self.tipo_origem == "existente":
            v = (self.versao_atual or "").strip()
            if not v:
                raise ValueError("Para tipo_origem='existente', informe versao_atual (ex.: 3.11.52).")
            parse_semver(v)
        return self


class AtualizarStatusProjetoRequest(BaseModel):
    status: Literal["ativo", "arquivado", "descontinuado"] = Field(
        ...,
        description="Novo status: ativo, arquivado ou descontinuado",
    )


class EvoluirVersaoProjetoRequest(BaseModel):
    nivel: Literal["patch", "minor", "major"] = Field(..., description="Tipo de incremento semântico")
    motivo: Optional[str] = Field(
        default=None,
        description="Opcional: motivo da evolução (governança / auditoria)",
        max_length=2000,
    )
    usuario_responsavel: Optional[str] = Field(
        default=None,
        description="Opcional: quem registrou a evolução",
        max_length=255,
    )


class HistoricoVersaoItem(BaseModel):
    id_historico: int
    id_projeto: int
    versao_anterior: str
    versao_nova: str
    nivel_evolucao: str
    motivo: Optional[str] = None
    usuario_responsavel: Optional[str] = None
    criado_em: str


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
    """Corpo da requisição para estruturar a demanda com IA (contexto enriquecido opcional)."""

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
    ha_contorno: Optional[str] = Field(default=None, description="Descrição da alternativa temporária/workaround (opcional)")
    sistema_ou_produto: Optional[str] = Field(default=None, description="Produto/sistema ao qual pertence (opcional)")
    perfil_solicitante: Optional[str] = Field(default=None, description="usuário final, analista, gestor, desenvolvedor, suporte (opcional)")
    texto: Optional[str] = Field(default=None, description="(Compatibilidade) Alias para texto_original")

    @field_validator("ha_contorno", mode="before")
    @classmethod
    def _ha_contorno_compat(cls, v):
        if v is None:
            return None
        if isinstance(v, bool):
            return "sim" if v else "não"
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return str(v)

    @model_validator(mode="before")
    @classmethod
    def texto_ou_texto_original(cls, data):
        if isinstance(data, dict):
            t = data.get("texto_original") or data.get("texto") or ""
            data["texto_original"] = t.strip() if isinstance(t, str) else ""
        return data


class AnaliseRequisitoResponse(BaseModel):
    """Resposta estruturada devolvida pela IA (título, tipo, perguntas Likert)."""

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


@app.get(
    "/",
    tags=["Meta / Sistema"],
    summary="Informações básicas da API",
    description="Mensagem institucional, link para documentação interativa e versão do produto.",
)
def root():
    """Raiz da API."""
    return {
        "mensagem": "API Matriz de Priorização",
        "docs": "/docs",
        "app_version": APP_VERSION,
        "release_date": RELEASE_DATE,
    }


@app.get(
    "/api/v1/status",
    response_model=AppStatusResponse,
    tags=["Meta / Sistema"],
    summary="Versão e data de release",
    description="Útil para homologação, monitoramento e conferir qual build está em uso.",
)
def obter_status_app():
    return AppStatusResponse(app_version=APP_VERSION, release_date=RELEASE_DATE)


@app.post(
    "/api/v1/projetos",
    tags=["Projetos"],
    summary="Cadastrar projeto",
    description="Projeto **novo** inicia em 1.0.0; **existente** exige `versao_atual` (semver). Nome único (case-insensitive).",
)
def api_criar_projeto(req: CriarProjetoRequest):
    try:
        return projetos_service.criar_projeto(
            nome_projeto=req.nome_projeto.strip(),
            tipo_origem=req.tipo_origem,
            descricao=req.descricao,
            responsavel=req.responsavel,
            versao_atual_informada=(req.versao_atual or "").strip() or None,
            status_projeto=req.status_projeto,
        )
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar projeto: {str(e)}")


@app.get(
    "/api/v1/projetos",
    summary="Listar projetos cadastrados",
)
def api_listar_projetos(
    tipo_origem: Optional[str] = Query(
        None,
        description="Filtrar: novo, existente, ou omitir para todos",
    ),
    status: Optional[str] = Query(
        None,
        description="Filtrar por status: ativo, arquivado, descontinuado, ou omitir para todos",
    ),
    q: Optional[str] = Query(
        None,
        description="Busca parcial no nome do projeto (case-insensitive)",
        max_length=200,
    ),
):
    try:
        return projetos_service.listar_projetos(tipo_origem=tipo_origem, status=status, busca_nome=q)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar projetos: {str(e)}")


@app.patch(
    "/api/v1/projetos/{id_projeto}/status",
    tags=["Projetos"],
    summary="Alterar status operacional do projeto",
    description="Estado de cadastro: ativo, arquivado ou descontinuado (não confundir com status da atividade no Kanban).",
)
def api_patch_status_projeto(id_projeto: int, body: AtualizarStatusProjetoRequest):
    try:
        return projetos_service.atualizar_status_projeto(id_projeto, body.status)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")


@app.post(
    "/api/v1/projetos/{id_projeto}/evoluir-versao",
    tags=["Projetos"],
    summary="Evoluir versão semântica do projeto",
    description="Incrementa `versao_atual` (patch / minor / major) e regista linha no histórico.",
)
def api_evoluir_versao_projeto(id_projeto: int, body: EvoluirVersaoProjetoRequest):
    try:
        return projetos_service.evoluir_versao_projeto(
            id_projeto,
            body.nivel,
            motivo=body.motivo,
            usuario_responsavel=body.usuario_responsavel,
        )
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao evoluir versão: {str(e)}")


@app.get(
    "/api/v1/projetos/{id_projeto}/historico-versao",
    response_model=list[HistoricoVersaoItem],
    tags=["Projetos"],
    summary="Histórico de evoluções de versão",
    description="Últimas alterações de versão (auditoria), mais recente primeiro.",
)
def api_historico_versao_projeto(
    id_projeto: int,
    limite: int = Query(100, ge=1, le=500),
):
    try:
        rows = projetos_service.listar_historico_versao(id_projeto, limite=limite)
        return [HistoricoVersaoItem(**r) for r in rows]
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar histórico: {str(e)}")


@app.get(
    "/api/v1/config-fila",
    tags=["Calibragem"],
    summary="Obter configuração da fila e WIP",
    description="Leitura da calibragem operacional usada pela fila e pelos limites WIP do Kanban.",
)
def api_get_config_fila():
    try:
        return config_fila_service.obter_configuracao()
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler config-fila: {str(e)}")


@app.post(
    "/api/v1/config-fila",
    tags=["Calibragem"],
    summary="Salvar configuração da fila e WIP",
    description="Escrita da calibragem operacional. Campos omitidos são mesclados com os padrões.",
)
def api_post_config_fila(body: dict[str, Any] = Body(...)):
    try:
        return config_fila_service.salvar_configuracao(body)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar config-fila: {str(e)}")


@app.post(
    "/api/v1/requisitos/analise",
    response_model=AnaliseRequisitoResponse,
    tags=["Requisitos - Estruturação com IA e avaliação"],
    summary="Estruturar demanda com IA",
    description=(
        "Envia texto e contexto opcional ao Gemini; devolve a demanda estruturada (BUG/INCREMENTO) e perguntas Likert "
        "por dimensão (criticidade/severidade ou esforço/valor) para a matriz."
    ),
)
def analisar_requisito(req: AnaliseRequisitoRequest):
    """
    Estrutura a demanda com IA e devolve título/descrição/tipo e perguntas de avaliação
    com vínculo explícito (dimensao, eixo_matriz, coordenada_relacionada).
    """
    try:
        payload = analise_ia_service.montar_payload_de_requisicao_analise(req.model_dump())
        out = analise_ia_service.executar_analise_requisito(payload)
        return AnaliseRequisitoResponse.model_validate(out)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao estruturar com IA: {str(e)}")


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
    cadastro: Optional[dict] = Field(
        default=None,
        description="Dados do cadastro inicial; obrigatório incluir id_projeto (projeto existente com versão).",
    )


class AtividadePriorizada(BaseModel):
    """Item da lista de atividades para visualização nos gráficos."""
    id: int
    titulo: str = ""
    tipo_requisito: str = Field(..., description="BUG ou INCREMENTO")
    coordenada_x: float = Field(..., description="Criticidade (bugs) ou Esforço (incrementos)")
    coordenada_y: float = Field(..., description="Severidade (bugs) ou Valor (incrementos)")
    score: float = Field(..., description="coordenada_x * coordenada_y")
    prioridade_categorica: str = Field(..., description="ALTA, MEDIA ou BAIXA")
    status_atual: str = Field(default="BACKLOG", description="Status no fluxo (ex.: BACKLOG, AVALIADO, EM_DESENVOLVIMENTO)")
    id_projeto: Optional[int] = Field(default=None, description="Projeto vinculado na entrada bruta, se houver")
    nome_projeto: Optional[str] = Field(default=None)
    versao_projeto: Optional[str] = Field(default=None, description="versao_atual do projeto no vínculo")


class AtualizarStatusRequest(BaseModel):
    """Payload para atualizar o status de uma atividade no fluxo/Kanban."""
    status: str = Field(..., description="Novo status (ex.: BACKLOG, TO_DO, DEVELOP, TEST, DEPLOY, DONE)")


class DocumentacaoFaseUpdate(BaseModel):
    """Corpo para gravar texto de uma fase (evidências para o Kanban)."""
    conteudo: str = Field(default="", description="Texto livre: RF/RNF, links, critérios de aceite, notas.")


class EventoAuditoriaResponse(BaseModel):
    tipo: str
    titulo: str
    descricao: str = ""
    quando: Optional[str] = None
    responsavel: Optional[str] = None


class AuditoriaDemandaResponse(BaseModel):
    id_requisito: int
    titulo: str = ""
    tipo_requisito: str = ""
    eventos: list[EventoAuditoriaResponse]


@app.get(
    "/api/v1/requisitos/atividades",
    response_model=list[AtividadePriorizada],
    tags=["Requisitos - Estruturação com IA e avaliação"],
    summary="Listar atividades priorizadas (matriz)",
    description="Leitura: atividades já avaliadas com coordenadas, score e prioridade categórica (bugs e incrementos).",
)
def listar_atividades():
    """Lista atividades com coordenadas para matriz de bugs (Criticidade x Severidade) e de incrementos (Esforço x Valor)."""
    try:
        return avaliacao_service.listar_atividades_matriz()
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar atividades: {str(e)}")


@app.post(
    "/api/v1/requisitos/salvar-avaliacao",
    tags=["Requisitos - Estruturação com IA e avaliação"],
    summary="Salvar avaliação completa",
    description=(
        "**Escrita transacional:** entrada bruta, requisito estruturado, avaliação e respostas Likert. "
        "Obrigatório `cadastro.id_projeto` com projeto existente e `versao_atual` preenchida. "
        "Após gravar, a atividade passa a integrar matriz, fila e Kanban."
    ),
)
def salvar_avaliacao(req: SalvarAvaliacaoRequest):
    """
    Salva todos os dados da avaliação no banco: cadastro, requisito estruturado,
    avaliação (com usuário avaliador) e cada resposta às perguntas.
    """
    try:
        cadastro = req.cadastro or {}
        respostas = [{"id_pergunta": r.id_pergunta, "texto": r.texto, "dimensao": r.dimensao, "valor_resposta": r.valor_resposta} for r in req.respostas]
        resultado = avaliacao_service.salvar_avaliacao(
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
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")


@app.get(
    "/api/v1/requisitos/{id_requisito}/documentacao-fase",
    tags=["Requisitos - Documentação por fase"],
    summary="Listar documentação por fase",
    description="Leitura: todas as fases (`doc_requisito`, `prontidao_dev`, …) com conteúdo atual ou vazio. Usado pelos gates ao avançar coluna.",
)
def get_documentacao_fase(id_requisito: int):
    try:
        return documentacao_service.listar_documentacao_fases(id_requisito)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler documentação: {str(e)}")


@app.put(
    "/api/v1/requisitos/{id_requisito}/documentacao-fase/{fase_codigo}",
    tags=["Requisitos - Documentação por fase"],
    summary="Gravar documentação de uma fase (PUT)",
    description=(
        "**Escrita:** corpo `{\"conteudo\": \"...\"}` (JSON estruturado por fase quando aplicável). "
        f"fase_codigo ∈ {{{', '.join(documentacao_service.FASES_DOC_VALIDAS)}}}. "
        "Conteúdo completo alimenta validação de gates no Kanban."
    ),
)
@app.post(
    "/api/v1/requisitos/{id_requisito}/documentacao-fase/{fase_codigo}",
    tags=["Requisitos - Documentação por fase"],
    summary="Gravar documentação de uma fase (POST)",
    description="Equivalente ao PUT; útil para clientes que só enviam POST.",
)
def put_documentacao_fase(id_requisito: int, fase_codigo: str, body: DocumentacaoFaseUpdate):
    try:
        return documentacao_service.gravar_documentacao_fase(id_requisito, fase_codigo, body.conteudo)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gravar: {str(e)}")


@app.post(
    "/api/v1/requisitos/{id_requisito}/status",
    tags=["Kanban e Gates"],
    summary="Atualizar status da atividade (fluxo Kanban)",
    description=(
        "**Escrita:** altera o estado da atividade na esteira. Avanço de coluna é **uma de cada vez**; "
        "retrocesso é permitido. Avanço exige documentação da fase atual conforme regras de gate "
        "(ver GET `/api/v1/kanban/{id_requisito}/gates`)."
    ),
)
def atualizar_status(id_requisito: int, body: AtualizarStatusRequest):
    """Atualiza o status_atual de uma atividade (usado pelo Kanban)."""
    try:
        kanban_status_service.atualizar_status_atividade(id_requisito, body.status)
        return {"ok": True}
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")


@app.get(
    "/api/v1/kanban/{id_requisito}/gates",
    tags=["Kanban e Gates"],
    summary="Consultar gates documentais",
    description=(
        "Leitura: coluna Kanban atual, próxima coluna, se a documentação permite avançar e lista do que falta "
        "(`falta_documentacao`). Baseado em `requisito_doc_fase` e no status persistido da atividade."
    ),
)
def get_kanban_gates(id_requisito: int):
    try:
        return kanban_status_service.obter_gates_kanban(id_requisito)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular gates: {str(e)}")


@app.get(
    "/api/v1/demandas/{id_requisito}/visao-360",
    tags=["Demandas - Consulta consolidada"],
    summary="Obter visão 360 da demanda",
    description="Leitura consolidada da atividade: origem, estruturação da IA, avaliação, documentação e gates.",
)
def get_demanda_visao_360(id_requisito: int):
    try:
        return demanda_consulta_service.obter_visao_360(id_requisito)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter visão 360: {str(e)}")


@app.get(
    "/api/v1/demandas/{id_requisito}/auditoria",
    response_model=AuditoriaDemandaResponse,
    tags=["Demandas - Consulta consolidada"],
    summary="Obter auditoria da demanda",
    description="Leitura consolidada de eventos relevantes da demanda e do projeto associado.",
)
def get_demanda_auditoria(id_requisito: int):
    try:
        return demanda_consulta_service.obter_auditoria(id_requisito)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter auditoria: {str(e)}")


@app.get(
    "/api/v1/fila",
    tags=["Fila de priorização"],
    summary="Obter fila operacional intercalada",
    description=(
        "Fila única para a esteira: ordenação por matriz (quadrante e coordenadas) "
        "e intercalação bugs/melhorias conforme vazão da config (ex.: 50/50)."
    ),
)
def obter_fila_operacional():
    try:
        return fila_service.obter_fila_priorizacao(intercalar=True)
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao montar fila operacional: {str(e)}")


@app.get(
    "/api/v1/fila/bugs",
    tags=["Fila de priorização"],
    summary="Obter fila ordenada de bugs",
    description="Leitura: lista ordenada automaticamente por regra de quadrante/score contendo apenas demandas BUG.",
)
def obter_fila_bugs():
    try:
        return fila_service.obter_fila_bugs()
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao montar fila de bugs: {str(e)}")


@app.get(
    "/api/v1/fila/incrementos",
    tags=["Fila de priorização"],
    summary="Obter fila ordenada de incrementos",
    description="Leitura: lista ordenada automaticamente por regra de quadrante/score contendo apenas demandas INCREMENTO (features).",
)
def obter_fila_incrementos():
    try:
        return fila_service.obter_fila_incrementos()
    except DomainError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao montar fila de incrementos: {str(e)}")


@app.on_event("startup")
async def _startup_aviso_documentacao():
    """Ajuda a diagnosticar processo antigo ainda na porta 8000 (404 = outro serviço ou código velho)."""
    print(
        "[api] Confirme com: GET http://127.0.0.1:8000/api/v1/ping",
        flush=True,
    )
    if os.getenv("SEED_INICIAL_ON_STARTUP", "true").strip().lower() in ("1", "true", "yes", "on"):
        try:
            from db.seed_runner import executar_seed_inicial_se_necessario

            if executar_seed_inicial_se_necessario():
                print("[api] Seed inicial aplicado (projetos, bugs e features).", flush=True)
            else:
                print("[api] Seed inicial ignorado: já existem projetos no banco.", flush=True)
        except Exception as exc:
            print(f"[api] Aviso: seed inicial não executado ({exc}).", flush=True)


@app.get(
    "/api/v1/ping",
    tags=["Meta / Sistema"],
    summary="Identificar esta API",
    description="Se devolver 404, o cliente não está a falar com este serviço (porta ou processo errado).",
)
def ping_matriz():
    """Se este endpoint der 404, o cliente não está a falar com este projeto (porta errada ou outro processo)."""
    return {
        "service": "matriz-priorizacao",
        "app_version": APP_VERSION,
        "rotas_documentacao_fase": "PUT e POST /api/v1/requisitos/{id}/documentacao-fase/{fase_codigo}",
    }


if __name__ == "__main__":
    import uvicorn

    # reload=True: ao gravar api.py, o servidor recarrega (evita ficar com rotas antigas).
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
