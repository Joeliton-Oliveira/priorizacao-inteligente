#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cria 4 projetos; em cada um, 1 BUG e 1 INCREMENTO com coordenadas aleatórias nos gráficos.

Uso (Postgres no ar):
    python3 db/seed_quatro_projetos.py
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.avaliacao_repo import listar_atividades_priorizadas, salvar_avaliacao_completa
from db.projeto_repo import criar_projeto

# Reutiliza geradores de coordenadas do seed de variações
from db.seed_variacoes_graficos import (  # noqa: E402
    PERGUNTAS_CRIT,
    PERGUNTAS_ESF,
    PERGUNTAS_SEV,
    PERGUNTAS_VAL,
    _gerar_alvos,
    _montar_respostas,
)

SEED_RANDOM = 20260528

PROJETOS = [
    {
        "nome_projeto": "Sistema de Faturamento",
        "tipo_origem": "existente",
        "versao_atual": "2.1.0",
        "descricao": "Emissão e cobrança de faturas B2B.",
        "bug_titulo": "Timeout ao gerar PDF da fatura",
        "inc_titulo": "Melhoria: filtro por período no relatório de faturas",
    },
    {
        "nome_projeto": "Portal do Cliente",
        "tipo_origem": "existente",
        "versao_atual": "3.4.2",
        "descricao": "Autoatendimento e consultas do cliente final.",
        "bug_titulo": "Sessão expira ao abrir segunda aba do portal",
        "inc_titulo": "Melhoria: notificações por e-mail de vencimento",
    },
    {
        "nome_projeto": "App Mobile Cliente",
        "tipo_origem": "novo",
        "versao_atual": None,
        "descricao": "Aplicativo iOS/Android para clientes.",
        "bug_titulo": "Crash ao usar login biométrico no iOS 18",
        "inc_titulo": "Melhoria: modo offline para consulta de saldo",
    },
    {
        "nome_projeto": "Integração ERP",
        "tipo_origem": "existente",
        "versao_atual": "1.8.5",
        "descricao": "Sincronização com SAP e legados.",
        "bug_titulo": "Duplicidade de pedidos na fila de integração",
        "inc_titulo": "Melhoria: dashboard de falhas de sincronização",
    },
]

MODULO = "Operação"
CONTEXTO = "Carga demo: 4 projetos com bug e incremento cada."


def _inserir_demanda(
    id_projeto: int,
    titulo: str,
    tipo: str,
    respostas: list[dict],
    texto: str,
) -> dict:
    return salvar_avaliacao_completa(
        texto_original=texto,
        titulo_requisito=titulo,
        descricao_requisito=texto,
        tipo_requisito=tipo,
        objetivo="Corrigir ou entregar o comportamento esperado.",
        finalidade="Suporte à priorização e matriz de atividades.",
        usuario_avaliador="seed_quatro_projetos",
        perfil_avaliador="analista",
        respostas=respostas,
        cadastro={
            "id_projeto": id_projeto,
            "modulo_afetado": MODULO,
            "contexto_negocio": CONTEXTO,
            "perfil_solicitante": "analista",
        },
    )


def _inserir_com_coordenadas(
    id_projeto: int,
    titulo: str,
    tipo: str,
    alvo: tuple[float, float, int, int],
    rng: random.Random,
    texto: str,
) -> tuple[int, float, float]:
    ax, ay, nx, ny = alvo
    if tipo == "BUG":
        respostas, ncx, nsy = _montar_respostas(
            rng, "CRITICIDADE", "SEVERIDADE", PERGUNTAS_CRIT, PERGUNTAS_SEV, ax, ay, nx, ny
        )
        dim_x, dim_y = "CRITICIDADE", "SEVERIDADE"
    else:
        respostas, ncx, nsy = _montar_respostas(
            rng, "ESFORCO", "VALOR", PERGUNTAS_ESF, PERGUNTAS_VAL, ax, ay, nx, ny
        )
        dim_x, dim_y = "ESFORCO", "VALOR"

    out = _inserir_demanda(id_projeto, titulo, tipo, respostas, texto)
    rid = out["id_requisito"]
    mx = round(sum(r["valor_resposta"] for r in respostas if r["dimensao"] == dim_x) / ncx, 2)
    my = round(sum(r["valor_resposta"] for r in respostas if r["dimensao"] == dim_y) / nsy, 2)
    return rid, mx, my


def main() -> None:
    rng = random.Random(SEED_RANDOM)
    ocupados_bug: set[tuple[float, float]] = set()
    ocupados_inc: set[tuple[float, float]] = set()

    for item in listar_atividades_priorizadas():
        t = (item.get("tipo_requisito") or "").upper()
        chave = (float(item["coordenada_x"]), float(item["coordenada_y"]))
        if t == "BUG":
            ocupados_bug.add(chave)
        else:
            ocupados_inc.add(chave)

    alvos_bug = _gerar_alvos(4, rng, ocupados_bug)
    alvos_inc = _gerar_alvos(4, rng, ocupados_inc)

    print("=== Seed: 4 projetos × (1 bug + 1 incremento) ===\n")

    for i, spec in enumerate(PROJETOS):
        p = criar_projeto(
            nome_projeto=spec["nome_projeto"],
            tipo_origem=spec["tipo_origem"],
            descricao=spec["descricao"],
            responsavel="seed_quatro_projetos",
            versao_atual_informada=spec.get("versao_atual"),
            status_projeto="ativo",
        )
        id_projeto = p["id_projeto"]
        versao = p.get("versao_atual") or spec.get("versao_atual") or "1.0.0"
        print(f"Projeto {i + 1}: id={id_projeto} nome={spec['nome_projeto']!r} versao={versao}")

        texto_bug = f"[{spec['nome_projeto']}] {spec['bug_titulo']}"
        texto_inc = f"[{spec['nome_projeto']}] {spec['inc_titulo']}"

        rid_b, xb, yb = _inserir_com_coordenadas(
            id_projeto,
            spec["bug_titulo"],
            "BUG",
            alvos_bug[i],
            rng,
            texto_bug,
        )
        print(f"  BUG id={rid_b} → ({xb}, {yb})")

        rid_i, xi, yi = _inserir_com_coordenadas(
            id_projeto,
            spec["inc_titulo"],
            "INCREMENTO",
            alvos_inc[i],
            rng,
            texto_inc,
        )
        print(f"  INC id={rid_i} → ({xi}, {yi})\n")

    print("Concluído: 4 projetos, 4 bugs, 4 incrementos.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
