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

PROJETOS: list[dict] = [
    {
        "nome_projeto": "Portal Acadêmico",
        "tipo_origem": "existente",
        "versao_atual": "2.4.0",
        "descricao": "Autoatendimento e consultas acadêmicas para alunos.",
        "demandas": [
            {
                "titulo": "Erro 500 ao exportar histórico de notas",
                "tipo": "BUG",
                "status": "BACKLOG",
                "texto": "Ao exportar PDF do histórico, a API retorna erro interno.",
            },
            {
                "titulo": "Filtro de disciplinas não persiste após logout",
                "tipo": "BUG",
                "status": "AVALIADO",
                "texto": "Preferências de filtro somem ao encerrar a sessão.",
            },
            {
                "titulo": "Dashboard de desempenho do aluno",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Painel com médias, frequência e alertas de reprovação.",
            },
            {
                "titulo": "Notificações push de prazos de entrega",
                "tipo": "INCREMENTO",
                "status": "EM_DESENVOLVIMENTO",
                "texto": "Alertas configuráveis para trabalhos e provas.",
            },
        ],
    },
    {
        "nome_projeto": "Priorização Inteligente",
        "tipo_origem": "novo",
        "versao_atual": None,
        "descricao": "Este produto: matriz, filas e Kanban de requisitos.",
        "demandas": [
            {
                "titulo": "Validação WIP não bloqueia drag no Kanban",
                "tipo": "BUG",
                "status": "BACKLOG",
                "texto": "É possível exceder o limite WIP ao arrastar cards.",
            },
            {
                "titulo": "Toast duplicado ao mover card na esteira",
                "tipo": "BUG",
                "status": "EM_TESTE",
                "texto": "Sucesso aparece em banner e toast ao mesmo tempo.",
            },
            {
                "titulo": "Fila intercalada bugs e melhorias",
                "tipo": "INCREMENTO",
                "status": "AVALIADO",
                "texto": "Montagem da fila respeitando percentual de vazão configurado.",
            },
            {
                "titulo": "Matriz de priorização em tempo real",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Gráficos de bugs e incrementos alimentados pela API.",
            },
        ],
    },
    {
        "nome_projeto": "Integração Financeira",
        "tipo_origem": "existente",
        "versao_atual": "1.2.0",
        "descricao": "Cobrança, boletos e conciliação com ERP.",
        "demandas": [
            {
                "titulo": "Duplicidade de boletos na conciliação",
                "tipo": "BUG",
                "status": "BACKLOG",
                "texto": "Mesmo título aparece duas vezes no lote diário.",
            },
            {
                "titulo": "Timeout na consulta de saldo em horário de pico",
                "tipo": "BUG",
                "status": "EM_HOMOLOGACAO",
                "texto": "Consulta demora mais de 30s entre 18h e 20h.",
            },
            {
                "titulo": "Relatório de inadimplência por curso",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Visão consolidada para coordenação financeira.",
            },
            {
                "titulo": "API de pagamentos PIX com webhook",
                "tipo": "INCREMENTO",
                "status": "BACKLOG",
                "texto": "Confirmação automática de pagamento via callback.",
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
    out = salvar_avaliacao_completa(
        texto_original=f"[{nome_projeto}] {texto}",
        titulo_requisito=spec["titulo"],
        descricao_requisito=texto,
        tipo_requisito=tipo,
        objetivo="Atender a necessidade registrada no cadastro de demonstração.",
        finalidade="Alimentar priorização, matriz e esteira do ambiente inicial.",
        usuario_avaliador=SEED_TAG,
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


def _limpar_seed_anterior() -> None:
    """Remove projetos criados por este seed (cascade nas FKs de demanda)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM projeto
                WHERE id_projeto IN (
                    SELECT DISTINCT eb.id_projeto
                    FROM entrada_bruta eb
                    WHERE eb.usuario_criacao = %s
                       OR eb.dados_cadastro_json->>'origem_seed' = %s
                )
                """,
                (SEED_TAG, SEED_TAG),
            )
        conn.commit()
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
            responsavel=SEED_TAG,
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
            if spec_dem["tipo"] == "BUG":
                alvo = alvos_bug[idx_bug]
                idx_bug += 1
            else:
                alvo = alvos_inc[idx_inc]
                idx_inc += 1
            rid = _inserir_demanda(id_projeto, spec_proj["nome_projeto"], spec_dem, alvo, rng)
            demandas_criadas += 1
            print(
                f"  {spec_dem['tipo']:10} id={rid} status={spec_dem.get('status', STATUS_PADRAO)} "
                f"→ {spec_dem['titulo'][:56]}"
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
