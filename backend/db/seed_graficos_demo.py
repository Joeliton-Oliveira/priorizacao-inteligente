#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insere 20 bugs e 18 incrementos com coordenadas distintas para popular os gráficos
da tela «Atividades priorizadas».

Uso (Postgres configurado em config.py):

    .venv/bin/python3 db/seed_graficos_demo.py

Opções:
    --reset   Remove itens anteriores cujo título começa por «Demo gráfico —».
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.avaliacao_repo import salvar_avaliacao_completa
from db.connection import get_connection
from db.projeto_repo import criar_projeto, listar_projetos

NOME_PROJETO = "Demo Matriz Gráficos"
PREFIXO_TITULO = "Demo gráfico —"

# 20 posições espalhadas na matriz Criticidade × Severidade
BUG_COORDS: list[tuple[int, int]] = [
    (1, 1), (1, 3), (1, 5),
    (2, 2), (2, 4), (2, 5),
    (3, 1), (3, 3), (3, 5),
    (4, 2), (4, 4), (4, 5),
    (5, 1), (5, 2), (5, 3), (5, 4), (5, 5),
    (2, 1), (4, 1), (3, 4),
]

# 18 posições espalhadas na matriz Esforço × Valor
INC_COORDS: list[tuple[int, int]] = [
    (1, 5), (1, 4), (1, 2),
    (2, 5), (2, 4), (2, 3),
    (3, 5), (3, 4), (3, 2),
    (4, 5), (4, 3), (4, 2),
    (5, 5), (5, 4), (5, 2),
    (2, 2), (3, 3), (4, 4),
]


def _obter_ou_criar_projeto() -> int:
    for p in listar_projetos(busca_nome=NOME_PROJETO):
        if (p.get("nome_projeto") or "").strip().lower() == NOME_PROJETO.lower():
            return int(p["id_projeto"])
    p = criar_projeto(
        nome_projeto=NOME_PROJETO,
        tipo_origem="novo",
        descricao="Projeto de demonstração para gráficos de matriz.",
        responsavel="seed_graficos_demo",
    )
    return int(p["id_projeto"])


def _remover_demonstracao_anterior() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id_requisito
                FROM requisito_estruturado r
                WHERE r.titulo LIKE %s
                """,
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
            cur.execute(
                "DELETE FROM avaliacao_requisito WHERE id_requisito = ANY(%s)",
                (ids,),
            )
            cur.execute("DELETE FROM status_requisito WHERE id_requisito = ANY(%s)", (ids,))
            cur.execute(
                "DELETE FROM requisito_doc_fase WHERE id_requisito = ANY(%s)",
                (ids,),
            )
            cur.execute(
                """
                DELETE FROM entrada_bruta
                WHERE id_entrada_bruta IN (
                    SELECT id_entrada_bruta FROM requisito_estruturado WHERE id_requisito = ANY(%s)
                )
                """,
                (ids,),
            )
            cur.execute("DELETE FROM requisito_estruturado WHERE id_requisito = ANY(%s)", (ids,))
            conn.commit()
            return len(ids)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _respostas_bug(cx: int, cy: int) -> list[dict]:
    return [
        {
            "id_pergunta": 1,
            "texto": "Criticidade",
            "dimensao": "CRITICIDADE",
            "valor_resposta": cx,
        },
        {
            "id_pergunta": 2,
            "texto": "Severidade",
            "dimensao": "SEVERIDADE",
            "valor_resposta": cy,
        },
    ]


def _respostas_inc(ex: int, val: int) -> list[dict]:
    return [
        {
            "id_pergunta": 1,
            "texto": "Esforço",
            "dimensao": "ESFORCO",
            "valor_resposta": ex,
        },
        {
            "id_pergunta": 2,
            "texto": "Valor",
            "dimensao": "VALOR",
            "valor_resposta": val,
        },
    ]


def _inserir_item(
    id_projeto: int,
    titulo: str,
    tipo: str,
    respostas: list[dict],
    cx: int,
    cy: int,
) -> dict:
    cadastro = {"id_projeto": id_projeto, "modulo_afetado": "Demo"}
    eixo = "criticidade×severidade" if tipo == "BUG" else "esforço×valor"
    return salvar_avaliacao_completa(
        texto_original=f"Seed para gráfico ({eixo} {cx},{cy}).",
        titulo_requisito=titulo,
        descricao_requisito=f"Item de demonstração posicionado em ({cx}, {cy}).",
        tipo_requisito=tipo,
        objetivo="Popular matriz para testes visuais.",
        finalidade="Validar leitura do gráfico com vários pontos.",
        usuario_avaliador="seed_graficos_demo",
        perfil_avaliador="analista",
        respostas=respostas,
        cadastro=cadastro,
    )


def main(reset: bool) -> None:
    if reset:
        n = _remover_demonstracao_anterior()
        if n:
            print(f"Removidos {n} itens de demonstração anteriores.")

    id_projeto = _obter_ou_criar_projeto()
    print(f"Projeto: id={id_projeto} ({NOME_PROJETO})")

    bugs_ok = 0
    for i, (cx, cy) in enumerate(BUG_COORDS, start=1):
        titulo = f"{PREFIXO_TITULO} Bug {i:02d}"
        out = _inserir_item(id_projeto, titulo, "BUG", _respostas_bug(cx, cy), cx, cy)
        bugs_ok += 1
        print(f"  BUG {i:02d} → ({cx}, {cy}) id_requisito={out['id_requisito']}")

    inc_ok = 0
    for i, (ex, val) in enumerate(INC_COORDS, start=1):
        titulo = f"{PREFIXO_TITULO} Incremento {i:02d}"
        out = _inserir_item(
            id_projeto, titulo, "INCREMENTO", _respostas_inc(ex, val), ex, val
        )
        inc_ok += 1
        print(f"  INC {i:02d} → ({ex}, {val}) id_requisito={out['id_requisito']}")

    print(f"\nConcluído: {bugs_ok} bugs e {inc_ok} incrementos.")
    print("Abra http://127.0.0.1:8051/atividades e recarregue a página.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de pontos para gráficos da matriz.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga itens «Demo gráfico —» antes de inserir de novo.",
    )
    args = parser.parse_args()
    try:
        main(reset=args.reset)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
