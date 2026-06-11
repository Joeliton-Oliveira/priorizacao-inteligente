#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insere 20 bugs e 20 incrementos com coordenadas espalhadas nos gráficos,
simulando o fluxo real: várias perguntas Likert por eixo → médias quebradas.

Uso:
    .venv/bin/python3 db/seed_variacoes_graficos.py --reset
"""
from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.avaliacao_repo import listar_atividades_priorizadas, salvar_avaliacao_completa
from db.connection import get_connection
from db.projeto_repo import listar_projetos

PREFIXO_TITULO = "Variação matriz —"
NOME_PROJETO_ALVO = "Priorização Inteligente de Requisitos"
SEED_RANDOM = 20260524

MEDIAS_2 = [i / 2 for i in range(2, 11)]  # 1.0 … 5.0 (passo 0,5)
MEDIAS_3 = [round(i / 3, 2) for i in range(3, 16)]  # 1.0 … 5.0 (passo ~0,33)

TEXTO_BASE_BUG = (
    "Quando o usuário tenta mover uma atividade do Kanban da coluna TO DO para DEVELOP, "
    "o sistema não valida corretamente se a coluna de destino já atingiu o limite de WIP configurado."
)
MODULO = "Kanban / Gestão de Fluxo de Demandas"
CONTEXTO = (
    "O Kanban é essencial para acompanhar o avanço das demandas, controlar gargalos e garantir "
    "que bugs e melhorias sejam tratados conforme prioridade. Falhas no WIP comprometem a esteira."
)

PERGUNTAS_CRIT = [
    "Em que medida a falha compromete a eficácia da gestão do fluxo de trabalho?",
    "Quantas equipes ou áreas são diretamente afetadas por este problema?",
    "Qual o risco de acúmulo de demandas críticas na fila por falha no controle de WIP?",
]
PERGUNTAS_SEV = [
    "Com que frequência os usuários encontram esse problema ao mover cards?",
    "Qual a dificuldade e propensão a erros do contorno manual?",
    "Qual o impacto direto na qualidade e no prazo quando o WIP é excedido?",
]
PERGUNTAS_ESF = [
    "Quanto esforço de desenvolvimento a melhoria exige?",
    "Qual a complexidade técnica de integrar com a esteira Kanban existente?",
    "Há dependências externas que aumentam o esforço de entrega?",
]
PERGUNTAS_VAL = [
    "Quanto valor de negócio a melhoria entrega ao time?",
    "A solução reduz risco operacional de forma perceptível?",
    "O ganho melhora métricas visíveis de fluxo ou priorização?",
]

BUG_TITULOS = [
    "Correção: validação WIP ao mover para DEVELOP",
    "Correção: limite WIP ignorado na coluna TEST",
    "Correção: mensagem ausente quando WIP de DEPLOY estoura",
    "Correção: contador WIP desatualizado após mover card",
    "Correção: WIP da calibragem não refletido no Kanban",
    "Correção: permitir exceder WIP com drag entre colunas",
    "Correção: gate de documentação ignorado com WIP cheio",
    "Correção: fila priorizada sem respeitar WIP de DEVELOP",
    "Correção: API aceita status sem checar WIP local",
    "Correção: duplo clique move dois cards além do WIP",
    "Correção: WIP zero tratado como ilimitado",
    "Correção: coluna TO_DO sem bloqueio ao puxar com WIP cheio",
    "Correção: sincronização WIP entre Dash e API",
    "Correção: rollback de movimento não libera slot WIP",
    "Correção: WIP por projeto vs global inconsistente",
    "Correção: alerta WIP some após refresh da esteira",
    "Correção: histórico de movimento sem registro de bloqueio WIP",
    "Correção: feature e bug compartilham mesmo limite WIP incorreto",
    "Correção: validação WIP apenas na UI, não na API",
    "Correção: timeout ao validar WIP com muitos cards",
]

INC_TITULOS = [
    "Melhoria: painel de ocupação WIP por coluna",
    "Melhoria: alerta proativo antes de atingir WIP",
    "Melhoria: simulador de movimentação com preview WIP",
    "Melhoria: histórico de violações de WIP na auditoria",
    "Melhoria: configurar WIP por tipo de demanda",
    "Melhoria: exportar relatório de gargalos WIP",
    "Melhoria: badge visual de slots livres no Kanban",
    "Melhoria: fila sugerir próximo card respeitando WIP",
    "Melhoria: notificação ao gestor quando WIP estoura",
    "Melhoria: calibragem com preview no quadro Kanban",
    "Melhoria: comparar WIP planejado vs realizado",
    "Melhoria: métricas de lead time por coluna WIP",
    "Melhoria: política de exceção temporária de WIP",
    "Melhoria: integração WIP com matriz de priorização",
    "Melhoria: tutorial in-app sobre limites WIP",
    "Melhoria: tema escuro com contraste nos avisos WIP",
    "Melhoria: API de consulta de disponibilidade WIP",
    "Melhoria: dashboard de saúde da esteira",
    "Melhoria: auto-balanceamento sugerido entre colunas",
    "Melhoria: documentação inline de gates e WIP",
]

BUG_TITULOS_LOTE2 = [
    "Correção: WIP ignorado ao retornar card para BACKLOG",
    "Correção: movimento em lote ultrapassa limite DEVELOP",
    "Correção: cache de WIP inválido após calibragem",
    "Correção: tooltip de bloqueio WIP não traduzido",
    "Correção: regra WIP diferente entre ambientes",
    "Correção: card fantasma ocupa slot de WIP",
    "Correção: filtro de atividades ignora status WIP",
    "Correção: exportação CSV sem coluna de WIP atual",
    "Correção: undo de drag não reverte contagem WIP",
    "Correção: limite WIP negativo aceito na API",
    "Correção: coluna DEPLOY sem validação cruzada",
    "Correção: prioridade alta ignora fila por WIP",
    "Correção: websocket não atualiza ocupação WIP",
    "Correção: perfil leitor consegue burlar WIP",
    "Correção: métrica de lead time distorcida por WIP",
    "Correção: duplicata de card conta dois WIPs",
    "Correção: migração de status pula checagem WIP",
    "Correção: alerta sonoro ausente em violação WIP",
    "Correção: integração Jira sem espelho de WIP",
    "Correção: gráfico de matriz desatualizado após WIP cheio",
]

INC_TITULOS_LOTE2 = [
    "Melhoria: heatmap de ocupação WIP por semana",
    "Melhoria: sugestão de redistribuição entre colunas",
    "Melhoria: modo foco escondendo colunas sem slot",
    "Melhoria: comparação WIP entre squads",
    "Melhoria: alerta por e-mail ao estourar WIP",
    "Melhoria: linha do tempo de violações WIP",
    "Melhoria: simulação what-if de novos limites",
    "Melhoria: widget WIP na home do produto",
    "Melhoria: export PDF do estado da esteira",
    "Melhoria: atalho para ver cards bloqueados por WIP",
    "Melhoria: cor por urgência dentro do limite WIP",
    "Melhoria: API batch para consultar slots livres",
    "Melhoria: integração calendário com capacidade WIP",
    "Melhoria: tour guiado sobre política de WIP",
    "Melhoria: favoritos de configuração WIP por projeto",
    "Melhoria: gráfico de tendência de gargalo",
    "Melhoria: comentário obrigatório ao forçar WIP",
    "Melhoria: painel executivo de fluxo e WIP",
    "Melhoria: previsão de estouro com ML simples",
    "Melhoria: sincronizar WIP com planilha externa",
]


def _resolver_id_projeto() -> int:
    for p in listar_projetos(busca_nome=NOME_PROJETO_ALVO):
        if (p.get("nome_projeto") or "").strip().lower() == NOME_PROJETO_ALVO.lower():
            return int(p["id_projeto"])
    rows = listar_projetos()
    if not rows:
        raise RuntimeError("Nenhum projeto cadastrado.")
    return int(rows[0]["id_projeto"])


def _tabela_existe(cur, nome: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s",
        (nome,),
    )
    return cur.fetchone() is not None


def _remover_anteriores() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_requisito FROM requisito_estruturado WHERE titulo LIKE %s",
                (f"{PREFIXO_TITULO}%",),
            )
            ids = [row[0] for row in cur.fetchall()]
            if not ids:
                conn.commit()
                return 0
            cur.execute(
                "DELETE FROM resposta_avaliacao WHERE id_avaliacao IN "
                "(SELECT id_avaliacao FROM avaliacao_requisito WHERE id_requisito = ANY(%s))",
                (ids,),
            )
            cur.execute("DELETE FROM avaliacao_requisito WHERE id_requisito = ANY(%s)", (ids,))
            if _tabela_existe(cur, "status_requisito"):
                cur.execute("DELETE FROM status_requisito WHERE id_requisito = ANY(%s)", (ids,))
            if _tabela_existe(cur, "requisito_doc_fase"):
                cur.execute("DELETE FROM requisito_doc_fase WHERE id_requisito = ANY(%s)", (ids,))
            cur.execute(
                """
                SELECT id_entrada_bruta FROM requisito_estruturado WHERE id_requisito = ANY(%s)
                """,
                (ids,),
            )
            entrada_ids = [row[0] for row in cur.fetchall() if row[0] is not None]
            cur.execute("DELETE FROM requisito_estruturado WHERE id_requisito = ANY(%s)", (ids,))
            if entrada_ids:
                cur.execute(
                    "DELETE FROM entrada_bruta WHERE id_entrada_bruta = ANY(%s)",
                    (entrada_ids,),
                )
            conn.commit()
            return len(ids)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _n_perguntas_eixo(rng: random.Random) -> int:
    return rng.choice([2, 2, 3])


def _medias_possiveis(n: int) -> list[float]:
    return MEDIAS_3 if n == 3 else MEDIAS_2


def _media_nao_inteira(n: int, rng: random.Random) -> float:
    opcoes = [m for m in _medias_possiveis(n) if m != int(m)]
    return rng.choice(opcoes)


def _valores_para_media(media_alvo: float, n: int, rng: random.Random) -> list[int]:
    alvo_total = round(media_alvo * n)
    alvo_total = max(n, min(5 * n, alvo_total))
    vals = [1] * n
    extra = alvo_total - n
    indices = list(range(n))
    rng.shuffle(indices)
    for i in indices:
        while extra > 0 and vals[i] < 5:
            vals[i] += 1
            extra -= 1
    rng.shuffle(vals)
    return vals


def _montar_respostas(
    rng: random.Random,
    dim_x: str,
    dim_y: str,
    textos_x: list[str],
    textos_y: list[str],
    alvo_x: float,
    alvo_y: float,
    nx: int,
    ny: int,
) -> tuple[list[dict], int, int]:
    vx = _valores_para_media(alvo_x, nx, rng)
    vy = _valores_para_media(alvo_y, ny, rng)
    respostas: list[dict] = []
    pid = 1
    for i, v in enumerate(vx):
        respostas.append({
            "id_pergunta": pid,
            "texto": textos_x[i],
            "dimensao": dim_x,
            "valor_resposta": v,
        })
        pid += 1
    for i, v in enumerate(vy):
        respostas.append({
            "id_pergunta": pid,
            "texto": textos_y[i],
            "dimensao": dim_y,
            "valor_resposta": v,
        })
        pid += 1
    return respostas, nx, ny


def _coords_ocupadas(tipo: str) -> set[tuple[float, float]]:
    tipo_u = tipo.upper()
    out: set[tuple[float, float]] = set()
    for item in listar_atividades_priorizadas():
        if (item.get("tipo_requisito") or "").upper() != tipo_u:
            continue
        out.add((float(item["coordenada_x"]), float(item["coordenada_y"])))
    return out


def _gerar_alvos(
    n: int,
    rng: random.Random,
    ocupados: set[tuple[float, float]] | None = None,
) -> list[tuple[float, float, int, int]]:
    """Retorna (alvo_x, alvo_y, n_perg_x, n_perg_y) sem colidir com ocupados."""
    out: list[tuple[float, float, int, int]] = []
    usados: set[tuple[float, float]] = set(ocupados or ())
    tentativas = 0
    max_tentativas = n * 500
    while len(out) < n and tentativas < max_tentativas:
        tentativas += 1
        nx = _n_perguntas_eixo(rng)
        ny = _n_perguntas_eixo(rng)
        ax = _media_nao_inteira(nx, rng)
        ay = _media_nao_inteira(ny, rng)
        chave = (ax, ay)
        if chave in usados:
            continue
        usados.add(chave)
        out.append((ax, ay, nx, ny))
    if len(out) < n:
        raise RuntimeError(
            f"Só foi possível gerar {len(out)} de {n} coordenadas únicas "
            f"(ocupadas: {len(ocupados or ())}). Tente ampliar o espaço de médias."
        )
    return out


def _inserir_lote(
    id_projeto: int,
    tipo: str,
    titulos: list[str],
    alvos: list[tuple[float, float, int, int]],
    rng: random.Random,
    offset_idx: int,
) -> list[int]:
    ids: list[int] = []
    if tipo == "BUG":
        dim_x, dim_y, tx, ty = "CRITICIDADE", "SEVERIDADE", PERGUNTAS_CRIT, PERGUNTAS_SEV
        rotulo = "BUG"
    else:
        dim_x, dim_y, tx, ty = "ESFORCO", "VALOR", PERGUNTAS_ESF, PERGUNTAS_VAL
        rotulo = "INC"

    for i, ((ax, ay, nx, ny), titulo) in enumerate(zip(alvos, titulos), start=1):
        respostas, ncx, nsy = _montar_respostas(rng, dim_x, dim_y, tx, ty, ax, ay, nx, ny)
        idx = offset_idx + i
        out = _inserir(id_projeto, titulo, tipo, respostas, idx)
        rid = out["id_requisito"]
        ids.append(rid)
        mx = round(sum(r["valor_resposta"] for r in respostas if r["dimensao"] == dim_x) / ncx, 2)
        my = round(sum(r["valor_resposta"] for r in respostas if r["dimensao"] == dim_y) / nsy, 2)
        print(f"  {rotulo} {idx:02d} {ncx}+{nsy} perguntas → ({mx}, {my}) id={rid}")
    return ids


def _inserir(
    id_projeto: int,
    titulo: str,
    tipo: str,
    respostas: list[dict],
    idx: int,
) -> dict:
    cadastro = {
        "id_projeto": id_projeto,
        "modulo_afetado": MODULO,
        "contexto_negocio": CONTEXTO,
        "perfil_solicitante": "desenvolvedor",
    }
    return salvar_avaliacao_completa(
        texto_original=f"{TEXTO_BASE_BUG} (variação {idx:02d}, {len(respostas)} respostas Likert).",
        titulo_requisito=f"{PREFIXO_TITULO} {titulo}",
        descricao_requisito=(
            f"Variação #{idx:02d} derivada do bug de validação WIP no Kanban. "
            f"Avaliação com {len(respostas)} perguntas Likert (médias por eixo)."
        ),
        tipo_requisito=tipo,
        objetivo="Garantir governança de WIP e fluxo confiável na esteira Kanban.",
        finalidade="Suporte a testes visuais da matriz com médias não inteiras.",
        usuario_avaliador="seed_variacoes",
        perfil_avaliador="desenvolvedor",
        respostas=respostas,
        cadastro=cadastro,
    )


def _contar_variacoes() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM requisito_estruturado WHERE titulo LIKE %s",
                (f"{PREFIXO_TITULO}%",),
            )
            return int(cur.fetchone()[0])
    finally:
        conn.close()


def main(reset: bool, append: bool, quantidade: int) -> None:
    seed = SEED_RANDOM + (99 if append else 0)
    rng = random.Random(seed)
    if reset:
        n = _remover_anteriores()
        if n:
            print(f"Removidas {n} variações anteriores.")

    id_projeto = _resolver_id_projeto()
    print(f"Projeto: id={id_projeto}")

    if append:
        ocup_bug = _coords_ocupadas("BUG")
        ocup_inc = _coords_ocupadas("INCREMENTO")
        print(f"Coordenadas já ocupadas: {len(ocup_bug)} bugs, {len(ocup_inc)} incrementos")
        offset = _contar_variacoes()
        titulos_bug = BUG_TITULOS_LOTE2[:quantidade]
        titulos_inc = INC_TITULOS_LOTE2[:quantidade]
        alvos_bug = _gerar_alvos(quantidade, rng, ocup_bug)
        alvos_inc = _gerar_alvos(quantidade, rng, ocup_inc)
    else:
        offset = 0
        titulos_bug = BUG_TITULOS[:quantidade]
        titulos_inc = INC_TITULOS[:quantidade]
        alvos_bug = _gerar_alvos(quantidade, rng)
        alvos_inc = _gerar_alvos(quantidade, rng)

    ids_criados: list[int] = []
    ids_criados.extend(_inserir_lote(id_projeto, "BUG", titulos_bug, alvos_bug, rng, offset))
    ids_criados.extend(_inserir_lote(id_projeto, "INCREMENTO", titulos_inc, alvos_inc, rng, offset))

    print(f"\nConcluído: {quantidade} bugs + {quantidade} incrementos ({len(ids_criados)} novos itens).")
    print("Recarregue http://localhost:3000/activities")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help=f"Remove itens «{PREFIXO_TITULO}» antes de inserir.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Acrescenta itens sem apagar os existentes; evita colisão de coordenadas no gráfico.",
    )
    parser.add_argument("-n", "--quantidade", type=int, default=20, help="Quantidade por tipo (default 20).")
    args = parser.parse_args()
    try:
        main(reset=args.reset, append=args.append, quantidade=args.quantidade)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
