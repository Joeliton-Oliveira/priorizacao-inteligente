#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Carga inicial: projetos com bugs (BUG) e features/melhorias (INCREMENTO) para ambiente novo.

Uso manual (Postgres no ar):
    python db/seed_inicial.py
    python db/seed_inicial.py --force   # apaga demandas/projetos do seed e recria

Automático: na subida da API, se não houver projetos (ver db/seed_runner.py).
"""
from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.avaliacao_repo import listar_atividades_priorizadas, salvar_avaliacao_completa
from db.connection import get_connection
from db.projeto_repo import criar_projeto
from db.seed_variacoes_graficos import (
    PERGUNTAS_CRIT,
    PERGUNTAS_ESF,
    PERGUNTAS_SEV,
    PERGUNTAS_VAL,
    _gerar_alvos,
    _montar_respostas,
    _tabela_existe,
)

SEED_TAG = "seed_inicial"
SEED_RANDOM = 20260604
MODULO = "Priorização Inteligente"
CONTEXTO = (
    "Dados de demonstração para matriz de priorização, filas e esteira Kanban. "
    "Gerado automaticamente no primeiro start do ambiente."
)

# status_atual gravado em status_requisito (valores da API / kanban_gates)
STATUS_PADRAO = "BACKLOG"

# Índices (0-based) na lista de bugs do seed que compartilham a mesma matriz
BUG_INDICES_MESMA_MATRIZ = (0, 1)

NOMES_PROJETOS_SEED = (
    "Portal Acadêmico",
    "Priorização Inteligente",
    "Integração Financeira",
)

PROJETOS: list[dict] = [
    {
        "nome_projeto": "Portal Acadêmico",
        "tipo_origem": "existente",
        "versao_atual": "2.4.0",
        "descricao": "Autoatendimento e consultas acadêmicas para alunos.",
        "responsavel": "Mariana Costa",
        "demandas": [
            {
                "titulo": "Erro 500 ao exportar histórico de notas",
                "tipo": "BUG",
                "status": "BACKLOG",
                "texto": "Ao exportar PDF do histórico, a API retorna erro interno.",
                "avaliador": "Lucas Ferreira",
            },
            {
                "titulo": "Filtro de disciplinas não persiste após logout",
                "tipo": "BUG",
                "status": "AVALIADO",
                "texto": "Preferências de filtro somem ao encerrar a sessão.",
                "avaliador": "Ana Paula Ribeiro",
            },
            {
                "titulo": "Dashboard de desempenho do aluno",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Painel com médias, frequência e alertas de reprovação.",
                "avaliador": "Thiago Nunes",
            },
            {
                "titulo": "Notificações push de prazos de entrega",
                "tipo": "INCREMENTO",
                "status": "EM_DESENVOLVIMENTO",
                "texto": "Alertas configuráveis para trabalhos e provas.",
                "avaliador": "Camila Duarte",
            },
        ],
    },
    {
        "nome_projeto": "Priorização Inteligente",
        "tipo_origem": "novo",
        "versao_atual": None,
        "descricao": "Este produto: matriz, filas e Kanban de requisitos.",
        "responsavel": "Rafael Mendes",
        "demandas": [
            {
                "titulo": "Validação WIP não bloqueia drag no Kanban",
                "tipo": "BUG",
                "status": "BACKLOG",
                "texto": "É possível exceder o limite WIP ao arrastar cards.",
                "avaliador": "Juliana Prado",
            },
            {
                "titulo": "Toast duplicado ao mover card na esteira",
                "tipo": "BUG",
                "status": "EM_TESTE",
                "texto": "Sucesso aparece em banner e toast ao mesmo tempo.",
                "avaliador": "Ricardo Souza",
            },
            {
                "titulo": "Fila intercalada bugs e melhorias",
                "tipo": "INCREMENTO",
                "status": "AVALIADO",
                "texto": "Montagem da fila respeitando percentual de vazão configurado.",
                "avaliador": "Fernanda Lima",
            },
            {
                "titulo": "Matriz de priorização em tempo real",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Gráficos de bugs e incrementos alimentados pela API.",
                "avaliador": "Rafael Mendes",
            },
        ],
    },
    {
        "nome_projeto": "Integração Financeira",
        "tipo_origem": "existente",
        "versao_atual": "1.2.0",
        "descricao": "Cobrança, boletos e conciliação com ERP.",
        "responsavel": "Beatriz Almeida",
        "demandas": [
            {
                "titulo": "Duplicidade de boletos na conciliação",
                "tipo": "BUG",
                "status": "BACKLOG",
                "texto": "Mesmo título aparece duas vezes no lote diário.",
                "avaliador": "Gustavo Martins",
            },
            {
                "titulo": "Timeout na consulta de saldo em horário de pico",
                "tipo": "BUG",
                "status": "EM_HOMOLOGACAO",
                "texto": "Consulta demora mais de 30s entre 18h e 20h.",
                "avaliador": "Patrícia Gomes",
            },
            {
                "titulo": "Relatório de inadimplência por curso",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Visão consolidada para coordenação financeira.",
                "avaliador": "Diego Cardoso",
            },
            {
                "titulo": "API de pagamentos PIX com webhook",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Confirmação automática de pagamento via callback.",
                "avaliador": "Beatriz Almeida",
            },
        ],
    },
]


def _ocupados_por_tipo() -> tuple[set[tuple[float, float]], set[tuple[float, float]]]:
    bugs: set[tuple[float, float]] = set()
    incs: set[tuple[float, float]] = set()
    for item in listar_atividades_priorizadas():
        chave = (float(item["coordenada_x"]), float(item["coordenada_y"]))
        if (item.get("tipo_requisito") or "").upper() == "BUG":
            bugs.add(chave)
        else:
            incs.add(chave)
    return bugs, incs


def _atualizar_status_requisito(id_requisito: int, status: str) -> None:
    st = (status or STATUS_PADRAO).strip().upper()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO status_requisito (id_requisito, status_atual)
                VALUES (%s, %s)
                ON CONFLICT (id_requisito) DO UPDATE SET status_atual = EXCLUDED.status_atual
                """,
                (id_requisito, st),
            )
        conn.commit()
    finally:
        conn.close()


def _inserir_demanda(
    id_projeto: int,
    nome_projeto: str,
    spec: dict,
    alvo: tuple[float, float, int, int],
    rng: random.Random,
) -> int:
    tipo = spec["tipo"]
    ax, ay, nx, ny = alvo
    if tipo == "BUG":
        respostas, ncx, nsy = _montar_respostas(
            rng, "CRITICIDADE", "SEVERIDADE", PERGUNTAS_CRIT, PERGUNTAS_SEV, ax, ay, nx, ny
        )
    else:
        respostas, _, _ = _montar_respostas(
            rng, "ESFORCO", "VALOR", PERGUNTAS_ESF, PERGUNTAS_VAL, ax, ay, nx, ny
        )

    texto = spec.get("texto") or spec["titulo"]
    avaliador = (spec.get("avaliador") or "Analista de requisitos").strip()
    out = salvar_avaliacao_completa(
        texto_original=f"[{nome_projeto}] {texto}",
        titulo_requisito=spec["titulo"],
        descricao_requisito=texto,
        tipo_requisito=tipo,
        objetivo="Atender a necessidade registrada no cadastro de demonstração.",
        finalidade="Alimentar priorização, matriz e esteira do ambiente inicial.",
        usuario_avaliador=avaliador,
        perfil_avaliador="analista",
        respostas=respostas,
        cadastro={
            "id_projeto": id_projeto,
            "modulo_afetado": MODULO,
            "contexto_negocio": CONTEXTO,
            "perfil_solicitante": "analista",
            "origem_seed": SEED_TAG,
        },
    )
    id_requisito = int(out["id_requisito"])
    status = spec.get("status") or STATUS_PADRAO
    if status != STATUS_PADRAO:
        _atualizar_status_requisito(id_requisito, status)
    return id_requisito


def _ids_projetos_seed(cur) -> list[int]:
    cur.execute(
        """
        SELECT DISTINCT id_projeto FROM (
            SELECT eb.id_projeto
            FROM entrada_bruta eb
            WHERE eb.dados_cadastro_json->>'origem_seed' = %s
            UNION
            SELECT id_projeto FROM projeto WHERE nome_projeto = ANY(%s)
        ) AS alvo
        """,
        (SEED_TAG, list(NOMES_PROJETOS_SEED)),
    )
    return [row[0] for row in cur.fetchall()]


def _remover_requisitos(cur, req_ids: list[int]) -> None:
    if not req_ids:
        return
    cur.execute(
        "DELETE FROM resposta_avaliacao WHERE id_avaliacao IN "
        "(SELECT id_avaliacao FROM avaliacao_requisito WHERE id_requisito = ANY(%s))",
        (req_ids,),
    )
    cur.execute(
        "DELETE FROM avaliacao_requisito WHERE id_requisito = ANY(%s)",
        (req_ids,),
    )
    if _tabela_existe(cur, "status_requisito"):
        cur.execute(
            "DELETE FROM status_requisito WHERE id_requisito = ANY(%s)",
            (req_ids,),
        )
    if _tabela_existe(cur, "requisito_doc_fase"):
        cur.execute(
            "DELETE FROM requisito_doc_fase WHERE id_requisito = ANY(%s)",
            (req_ids,),
        )
    cur.execute(
        "DELETE FROM requisito_estruturado WHERE id_requisito = ANY(%s)",
        (req_ids,),
    )


def _limpar_seed_anterior() -> None:
    """Remove demandas e projetos criados por este seed (ordem respeita FK RESTRICT)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            projeto_ids = _ids_projetos_seed(cur)
            if not projeto_ids:
                conn.commit()
                return

            # Apaga todas as demandas dos projetos do seed (não só as com tag),
            # pois entrada_bruta bloqueia DELETE em projeto via RESTRICT.
            cur.execute(
                """
                SELECT r.id_requisito
                FROM requisito_estruturado r
                JOIN entrada_bruta eb ON eb.id_entrada_bruta = r.id_entrada_bruta
                WHERE eb.id_projeto = ANY(%s)
                """,
                (projeto_ids,),
            )
            req_ids = [row[0] for row in cur.fetchall()]
            _remover_requisitos(cur, req_ids)

            cur.execute(
                "DELETE FROM entrada_bruta WHERE id_projeto = ANY(%s)",
                (projeto_ids,),
            )
            cur.execute(
                "DELETE FROM projeto WHERE id_projeto = ANY(%s)",
                (projeto_ids,),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def executar_seed(force: bool = False) -> dict[str, int]:
    from db.seed_runner import contar_projetos

    if not force and contar_projetos() > 0:
        print("Banco já contém projetos. Nada a fazer. Use --force para recriar o seed inicial.")
        return {"projetos": 0, "demandas": 0, "bugs": 0, "features": 0}

    if force:
        _limpar_seed_anterior()

    rng = random.Random(SEED_RANDOM)
    ocupados_bug, ocupados_inc = _ocupados_por_tipo()
    total_bugs = sum(1 for p in PROJETOS for d in p["demandas"] if d["tipo"] == "BUG")
    total_inc = sum(1 for p in PROJETOS for d in p["demandas"] if d["tipo"] == "INCREMENTO")
    alvos_bug = _gerar_alvos(total_bugs, rng, ocupados_bug)
    alvos_inc = _gerar_alvos(total_inc, rng, ocupados_inc)
    titulos_bug = [
        d["titulo"]
        for p in PROJETOS
        for d in p["demandas"]
        if d["tipo"] == "BUG"
    ]
    if len(alvos_bug) > max(BUG_INDICES_MESMA_MATRIZ):
        ref, dup = BUG_INDICES_MESMA_MATRIZ
        alvos_bug[dup] = alvos_bug[ref]
        ax, ay, _, _ = alvos_bug[ref]
        print(
            f"Bugs «{titulos_bug[ref]}» e «{titulos_bug[dup]}» "
            f"compartilham matriz (criticidade={ax}, severidade={ay})\n"
        )
    idx_bug = 0
    idx_inc = 0

    projetos_criados = 0
    demandas_criadas = 0

    print("=== Seed inicial: projetos, bugs e features ===\n")

    for spec_proj in PROJETOS:
        p = criar_projeto(
            nome_projeto=spec_proj["nome_projeto"],
            tipo_origem=spec_proj["tipo_origem"],
            descricao=spec_proj["descricao"],
            responsavel=spec_proj.get("responsavel"),
            versao_atual_informada=spec_proj.get("versao_atual"),
            status_projeto="ativo",
        )
        id_projeto = int(p["id_projeto"])
        projetos_criados += 1
        print(
            f"Projeto id={id_projeto} nome={spec_proj['nome_projeto']!r} "
            f"versao={p.get('versao_atual', '1.0.0')}"
        )

        for spec_dem in spec_proj["demandas"]:
            matriz_nota = ""
            if spec_dem["tipo"] == "BUG":
                alvo = alvos_bug[idx_bug]
                if idx_bug == BUG_INDICES_MESMA_MATRIZ[1]:
                    ref_titulo = titulos_bug[BUG_INDICES_MESMA_MATRIZ[0]]
                    ax, ay, _, _ = alvo
                    matriz_nota = (
                        f" [mesma matriz que «{ref_titulo}»: "
                        f"criticidade={ax}, severidade={ay}]"
                    )
                idx_bug += 1
            else:
                alvo = alvos_inc[idx_inc]
                idx_inc += 1
            rid = _inserir_demanda(id_projeto, spec_proj["nome_projeto"], spec_dem, alvo, rng)
            demandas_criadas += 1
            print(
                f"  {spec_dem['tipo']:10} id={rid} status={spec_dem.get('status', STATUS_PADRAO)} "
                f"→ {spec_dem['titulo'][:56]}{matriz_nota}"
            )
        print()

    print(
        f"Concluído: {projetos_criados} projetos, "
        f"{demandas_criadas} demandas ({total_bugs} bugs, {total_inc} features)."
    )
    return {
        "projetos": projetos_criados,
        "demandas": demandas_criadas,
        "bugs": total_bugs,
        "features": total_inc,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga inicial de demonstração.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove dados anteriores deste seed e recria.",
    )
    args = parser.parse_args()
    executar_seed(force=args.force)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
