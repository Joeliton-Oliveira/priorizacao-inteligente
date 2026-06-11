#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona 3 BUGs e 3 INCREMENTOs por projeto, um em cada quadrante distinto da matriz,
para validar a ordenação da fila (quadrante → score → desempates).

Requer os 4 projetos de seed_quatro_projetos.py (ou equivalentes).

Uso:
    python3 db/seed_validacao_filas_quadrantes.py
    python3 db/seed_validacao_filas_quadrantes.py --reset   # remove itens com PREFIXO_TITULO
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
from db.seed_variacoes_graficos import (
    PERGUNTAS_CRIT,
    PERGUNTAS_ESF,
    PERGUNTAS_SEV,
    PERGUNTAS_VAL,
    _montar_respostas,
)
from fila_priorizacao import (
    NOMES_QUADRANTE_BUG,
    NOMES_QUADRANTE_INCREMENTO,
    nome_quadrante,
    ordem_quadrante_bug,
    ordem_quadrante_incremento,
)

PREFIXO_TITULO = "[Validação fila]"
SEED_RANDOM = 20260529

NOMES_PROJETOS = [
    "Sistema de Faturamento",
    "Portal do Cliente",
    "App Mobile Cliente",
    "Integração ERP",
]

# 12 coordenadas únicas (4 projetos × 3) — médias Likert por eixo
BUG_ALVOS: list[tuple[float, float, str]] = [
    # Projeto 1: Q1, Q2, Q3
    (4.67, 4.33, "Crítica-alta"),
    (3.67, 2.33, "Alta-média"),
    (2.33, 4.67, "Média"),
    # Projeto 2: Q2, Q3, Q4
    (3.83, 2.17, "Alta-média"),
    (2.17, 4.33, "Média"),
    (1.83, 2.33, "Baixa"),
    # Projeto 3: Q1, Q3, Q4
    (4.83, 4.67, "Crítica-alta"),
    (2.33, 4.83, "Média"),
    (1.67, 1.83, "Baixa"),
    # Projeto 4: Q1, Q2, Q4
    (4.33, 4.83, "Crítica-alta"),
    (3.33, 2.33, "Alta-média"),
    (1.83, 2.17, "Baixa"),
]

INC_ALVOS: list[tuple[float, float, str]] = [
    # Projeto 1: Ganhos rápidos, Grandes, Baixo retorno
    (1.83, 4.67, "Ganhos rápidos"),
    (4.33, 4.17, "Grandes projetos"),
    (4.17, 2.17, "Baixo retorno"),
    # Projeto 2: Ganhos rápidos, Melhorias simples, Baixo retorno
    (2.17, 4.83, "Ganhos rápidos"),
    (2.33, 2.17, "Melhorias simples"),
    (3.83, 2.33, "Baixo retorno"),
    # Projeto 3: Grandes, Melhorias simples, Baixo retorno
    (4.67, 4.33, "Grandes projetos"),
    (1.67, 2.33, "Melhorias simples"),
    (4.83, 2.17, "Baixo retorno"),
    # Projeto 4: Ganhos rápidos, Grandes, Melhorias simples
    (1.33, 4.33, "Ganhos rápidos"),
    (3.67, 4.67, "Grandes projetos"),
    (2.17, 2.33, "Melhorias simples"),
]


def _resolver_projetos() -> list[dict]:
    por_nome: dict[str, dict] = {}
    for p in listar_projetos():
        nome = (p.get("nome_projeto") or "").strip()
        por_nome[nome.lower()] = p
    out = []
    for nome in NOMES_PROJETOS:
        p = por_nome.get(nome.lower())
        if not p:
            raise RuntimeError(
                f"Projeto {nome!r} não encontrado. Execute antes: python3 db/seed_quatro_projetos.py"
            )
        out.append(p)
    return out


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
                return 0
            cur.execute(
                "DELETE FROM resposta_avaliacao WHERE id_avaliacao IN "
                "(SELECT id_avaliacao FROM avaliacao_requisito WHERE id_requisito = ANY(%s))",
                (ids,),
            )
            cur.execute("DELETE FROM avaliacao_requisito WHERE id_requisito = ANY(%s)", (ids,))
            cur.execute("DELETE FROM status_requisito WHERE id_requisito = ANY(%s)", (ids,))
            cur.execute("DELETE FROM requisito_doc_fase WHERE id_requisito = ANY(%s)", (ids,))
            cur.execute(
                "SELECT id_entrada_bruta FROM requisito_estruturado WHERE id_requisito = ANY(%s)",
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


def _inserir(
    rng: random.Random,
    id_projeto: int,
    nome_projeto: str,
    titulo: str,
    tipo: str,
    alvo_x: float,
    alvo_y: float,
    rotulo_quadrante: str,
) -> dict:
    nx, ny = 2, 2
    if tipo == "BUG":
        respostas, _, _ = _montar_respostas(
            rng, "CRITICIDADE", "SEVERIDADE", PERGUNTAS_CRIT, PERGUNTAS_SEV, alvo_x, alvo_y, nx, ny
        )
        ordem = ordem_quadrante_bug(alvo_x, alvo_y)
    else:
        respostas, _, _ = _montar_respostas(
            rng, "ESFORCO", "VALOR", PERGUNTAS_ESF, PERGUNTAS_VAL, alvo_x, alvo_y, nx, ny
        )
        ordem = ordem_quadrante_incremento(alvo_x, alvo_y)

    texto = (
        f"{PREFIXO_TITULO} {nome_projeto} — {rotulo_quadrante}. "
        f"Coordenadas alvo ({alvo_x}, {alvo_y}) para teste da fila."
    )
    out = salvar_avaliacao_completa(
        texto_original=texto,
        titulo_requisito=titulo,
        descricao_requisito=texto,
        tipo_requisito=tipo,
        objetivo="Validar ordenação da fila por quadrante e score.",
        finalidade="Cenário de teste visual na matriz e nas filas separadas.",
        usuario_avaliador="seed_validacao_filas",
        perfil_avaliador="analista",
        respostas=respostas,
        cadastro={
            "id_projeto": id_projeto,
            "modulo_afetado": "Validação fila",
            "contexto_negocio": rotulo_quadrante,
            "perfil_solicitante": "analista",
        },
    )
    rid = out["id_requisito"]
    nome_q = nome_quadrante(tipo, ordem)
    if nome_q != rotulo_quadrante:
        raise RuntimeError(
            f"Quadrante esperado {rotulo_quadrante!r}, calculado {nome_q!r} (ordem {ordem}) em ({alvo_x}, {alvo_y})"
        )
    mapa = NOMES_QUADRANTE_BUG if tipo == "BUG" else NOMES_QUADRANTE_INCREMENTO
    if mapa.get(ordem) != rotulo_quadrante:
        raise RuntimeError(f"Inconsistência de rótulo interno para ordem {ordem}")
    print(
        f"  {tipo:11} id={rid:3} Q{ordem} {nome_q:16} "
        f"alvo=({alvo_x:.2f},{alvo_y:.2f}) titulo={titulo[:50]!r}"
    )
    return out


def main(reset: bool) -> None:
    if reset:
        n = _remover_anteriores()
        if n:
            print(f"Removidos {n} itens anteriores ({PREFIXO_TITULO}).\n")

    rng = random.Random(SEED_RANDOM)
    projetos = _resolver_projetos()
    ocup_bug = {(float(i["coordenada_x"]), float(i["coordenada_y"])) for i in listar_atividades_priorizadas() if (i.get("tipo_requisito") or "").upper() == "BUG"}
    ocup_inc = {(float(i["coordenada_x"]), float(i["coordenada_y"])) for i in listar_atividades_priorizadas() if (i.get("tipo_requisito") or "").upper() == "INCREMENTO"}

    print(f"=== Seed validação filas: 3 bugs + 3 incrementos × {len(projetos)} projetos ===\n")
    total = 0

    for p_idx, projeto in enumerate(projetos):
        id_projeto = int(projeto["id_projeto"])
        nome = projeto["nome_projeto"]
        print(f"Projeto {p_idx + 1}: id={id_projeto} {nome!r}")

        for slot in range(3):
            ax, ay, rotulo = BUG_ALVOS[p_idx * 3 + slot]
            if (ax, ay) in ocup_bug:
                raise RuntimeError(f"Coordenada BUG {ax},{ay} já ocupada.")
            ocup_bug.add((ax, ay))
            titulo = f"{PREFIXO_TITULO} BUG {rotulo} — {nome} #{slot + 1}"
            _inserir(rng, id_projeto, nome, titulo, "BUG", ax, ay, rotulo)
            total += 1

        for slot in range(3):
            ax, ay, rotulo = INC_ALVOS[p_idx * 3 + slot]
            if (ax, ay) in ocup_inc:
                raise RuntimeError(f"Coordenada INC {ax},{ay} já ocupada.")
            ocup_inc.add((ax, ay))
            titulo = f"{PREFIXO_TITULO} INC {rotulo} — {nome} #{slot + 1}"
            _inserir(rng, id_projeto, nome, titulo, "INCREMENTO", ax, ay, rotulo)
            total += 1

        print()

    print(f"Concluído: {total} itens inseridos ({len(projetos)} projetos × 6).")
    print("Confira em Atividades (matriz) e Filas (bugs / incrementos).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help=f"Remove demandas cujo título começa com {PREFIXO_TITULO!r} antes de inserir.",
    )
    args = parser.parse_args()
    try:
        main(reset=args.reset)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
