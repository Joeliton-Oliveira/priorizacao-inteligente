# -*- coding: utf-8 -*-
"""Testes de fumaça do front-end Dash — layout, IDs e consistência."""

import pytest


def test_app_importa():
    from app import app
    assert app is not None


def test_versao_semantica_definida():
    import re
    from version import RELEASE_DATE, __version__

    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", RELEASE_DATE)


def test_format_release_date_br():
    from version import format_release_date_br

    assert format_release_date_br("2026-04-02") == "02/04/2026"


def test_sugestao_bump_por_tipo_demanda():
    from version import sugestao_bump_por_tipo_demanda

    assert sugestao_bump_por_tipo_demanda("BUG") == "patch"
    assert sugestao_bump_por_tipo_demanda("INCREMENTO") == "minor"
    assert sugestao_bump_por_tipo_demanda("breaking_change") == "major"


def test_parse_semver():
    from version import parse_semver

    assert parse_semver("2.10.3") == (2, 10, 3)


def test_proxima_versao_semver():
    from version import proxima_versao_semver

    assert proxima_versao_semver("1.0.0", "patch") == "1.0.1"
    assert proxima_versao_semver("3.11.52", "patch") == "3.11.53"
    assert proxima_versao_semver("1.0.0", "minor") == "1.1.0"
    assert proxima_versao_semver("1.4.8", "major") == "2.0.0"


def test_changelog_contem_versao_atual():
    from version import __version__, changelog_alinhado_com_version_py

    assert changelog_alinhado_com_version_py(), (
        f"README.md (Changelog) deve incluir uma seção ## [{__version__}] alinhada a version.py"
    )


def test_versao_consta_no_changelog_helper():
    from version import versao_consta_no_changelog

    assert versao_consta_no_changelog("1.0.0", "## [1.0.0] — 2026-01-01\n")
    assert not versao_consta_no_changelog("9.9.9", "## [1.0.0]\n")


def test_sugestao_bump_por_mensagem_commit():
    from version import sugestao_bump_por_mensagem_commit

    assert sugestao_bump_por_mensagem_commit("fix: login") == "patch"
    assert sugestao_bump_por_mensagem_commit("feat: cadastro") == "minor"
    assert sugestao_bump_por_mensagem_commit("feat(api)!: quebra contrato") == "major"
    assert sugestao_bump_por_mensagem_commit("x\n\nBREAKING CHANGE: remove campo") == "major"


def test_app_layout_tem_location():
    from app import app
    layout_str = str(app.layout)
    assert "url" in layout_str or "Location" in layout_str


def test_layout_tem_cadastro_wrapper():
    from app import app
    assert "cadastro" in str(app.layout).lower()


def test_layout_tem_store_atividades():
    from app import app
    layout_str = str(app.layout)
    assert "store-atividades" in layout_str or "store_atividades" in layout_str


def test_layout_tem_calibragem_wrapper():
    from app import app
    assert "calibragem" in str(app.layout).lower()


def test_estilos_definidos():
    from app import CORES, ESTILO_APP, ESTILO_SECAO, ESTILO_BOTAO
    assert "primary" in CORES
    assert "bg" in CORES
    assert "fontFamily" in ESTILO_APP or "backgroundColor" in ESTILO_APP
    assert "borderRadius" in ESTILO_SECAO or "padding" in ESTILO_SECAO
    assert "cursor" in ESTILO_BOTAO or "padding" in ESTILO_BOTAO


def test_calib_inputs_lista_completa():
    """_CALIB_INPUTS reflete vazão bugs/melhorias e WIP por coluna do Kanban."""
    from app import _CALIB_INPUTS
    ids = [id_ for id_, _, _ in _CALIB_INPUTS]
    assert "calib-vazao-bugs" in ids
    assert "calib-vazao-incrementos" in ids
    assert "calib-wip-todo" in ids
    assert "calib-wip-deploy" in ids
    assert len(ids) == 6
