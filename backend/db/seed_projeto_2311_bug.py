#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insere um projeto com versão 2.3.11 (tipo existente) e, em seguida, um bug
avaliado e vinculado a esse projeto (entra em Atividades / Kanban / Fila).

Uso (API e Postgres no ar, mesmo `config.py`):

    python3 db/seed_projeto_2311_bug.py

Se já existir um projeto com o mesmo nome, o script termina com erro —
altere `NOME_PROJETO` abaixo ou remova o projeto duplicado.
"""
from __future__ import annotations

import sys

# Raiz do projeto no path
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.avaliacao_repo import salvar_avaliacao_completa
from db.projeto_repo import criar_projeto

NOME_PROJETO = "Plataforma Integração v2.3.11"
VERSAO = "2.3.11"


def main() -> None:
    p = criar_projeto(
        nome_projeto=NOME_PROJETO,
        tipo_origem="existente",
        descricao="Seed: projeto legado na versão 2.3.11.",
        responsavel="seed_script",
        versao_atual_informada=VERSAO,
        status_projeto="ativo",
    )
    id_projeto = p["id_projeto"]
    print(f"Projeto criado: id_projeto={id_projeto} nome={NOME_PROJETO!r} versao_atual={VERSAO}")

    cadastro = {
        "id_projeto": id_projeto,
        "modulo_afetado": "Faturas",
        "contexto_negocio": "Portal do cliente",
        "objetivo_desejado": "Correção estável em produção",
    }
    respostas = [
        {
            "id_pergunta": 1,
            "texto": "Criticidade do impacto no negócio",
            "dimensao": "CRITICIDADE",
            "valor_resposta": 4,
        },
        {
            "id_pergunta": 2,
            "texto": "Severidade técnica / utilizador",
            "dimensao": "SEVERIDADE",
            "valor_resposta": 5,
        },
    ]

    out = salvar_avaliacao_completa(
        texto_original="Ao abrir o detalhe da fatura no portal, a página devolve erro 500 e o cliente não consegue fazer download do PDF.",
        titulo_requisito="Erro 500 ao abrir fatura no portal",
        descricao_requisito="Falha intermitente na API de documentos; stack trace referencia timeout na integração com o motor de PDF.",
        tipo_requisito="BUG",
        objetivo="Restaurar a visualização e download de faturas.",
        finalidade="Evitar bloqueio de cobrança e suporte.",
        usuario_avaliador="seed_script",
        perfil_avaliador="analista",
        respostas=respostas,
        cadastro=cadastro,
    )
    print(
        "Bug gravado:",
        f"id_requisito={out['id_requisito']}",
        f"id_entrada_bruta={out['id_entrada_bruta']}",
        f"id_avaliacao={out['id_avaliacao']}",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
