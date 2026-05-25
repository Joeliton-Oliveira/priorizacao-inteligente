"""
Versão do produto no padrão MAJOR.MINOR.PATCH (xx.xx.xx).

Regras práticas (sem usar “% do código” como regra principal):

- MAJOR — mudança estrutural relevante, quebra de compatibilidade, arquitetura,
  fluxo principal, banco ou comportamento central muito diferente da versão anterior.
  Ex.: 1.4.8 → 2.0.0

- MINOR — nova funcionalidade, módulo novo ou expansão de capacidades sem quebrar
  o que já existia.
  Ex.: 2.0.0 → 2.1.0

- PATCH — correção de bug, ajuste visual, validação, performance ou regra pontual.
  Ex.: 2.1.0 → 2.1.1

Indicadores auxiliares para decidir: módulos/endpoints/telas afetados, tabelas
impactadas, quebra de contrato com clientes ou mudança em regras centrais do negócio.

Automatização sugerida (Git / tarefas / labels): bug → PATCH; feature → MINOR;
breaking_change ou refactor estrutural → MAJOR.

Relação com classificação de demanda (sugestão, não automática no release):

- Bug / correção → tendência PATCH
- Melhoria / incremento / feature → tendência MINOR
- Mudança estrutural / breaking → tendência MAJOR

Use ``sugestao_bump_por_tipo_demanda`` como apoio; a decisão final continua humana.

Commits no estilo Conventional Commits (sugestão de bump, não altera arquivos):

- ``fix:`` → PATCH
- ``feat:`` → MINOR
- ``feat!:`` ou rodapé ``BREAKING CHANGE:`` → MAJOR

Veja ``sugestao_bump_por_mensagem_commit``.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

__version__ = "1.0.0"
RELEASE_DATE = "2026-04-02"

_VERSION_RE = re.compile(r'^(__version__\s*=\s*")([^"]+)(")', re.MULTILINE)
_RELEASE_RE = re.compile(r'^(RELEASE_DATE\s*=\s*")([^"]+)(")', re.MULTILINE)
_VERSION_FILE = Path(__file__).resolve()
_CHANGELOG_FILE = _VERSION_FILE.parent / "README.md"
_CHANGELOG_HEADING_RE = re.compile(
    r"^##\s*\[(\d+\.\d+\.\d+)\]",
    re.MULTILINE,
)


def format_release_date_br(iso_date: str | None = None) -> str:
    """Converte YYYY-MM-DD para DD/MM/AAAA (exibição no Dash)."""
    raw = (iso_date or RELEASE_DATE).strip()
    parts = raw.split("-")
    if len(parts) != 3:
        return raw
    y, m, d = parts
    return f"{d}/{m}/{y}"


def parse_semver(v: str) -> tuple[int, int, int]:
    parts = v.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Versão inválida (esperado MAJOR.MINOR.PATCH): {v!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def proxima_versao_semver(versao_atual: str, nivel: str) -> str:
    """
    Calcula a próxima versão semântica a partir da string atual (ex.: projetos cadastrados).

    ``nivel``: ``patch`` | ``minor`` | ``major``.
    """
    n = (nivel or "").strip().lower()
    if n not in ("patch", "minor", "major"):
        raise ValueError("nivel deve ser patch, minor ou major")
    m, i, p = parse_semver(versao_atual)
    if n == "patch":
        return f"{m}.{i}.{p + 1}"
    if n == "minor":
        return f"{m}.{i + 1}.0"
    return f"{m + 1}.0.0"


def _write_version_file(new_version: str, release_iso: str) -> None:
    text = _VERSION_FILE.read_text(encoding="utf-8")
    if not _VERSION_RE.search(text):
        raise RuntimeError("Não encontrei __version__ em version.py")
    if not _RELEASE_RE.search(text):
        raise RuntimeError("Não encontrei RELEASE_DATE em version.py")
    text = _VERSION_RE.sub(rf'\1{new_version}\3', text, count=1)
    text = _RELEASE_RE.sub(rf'\1{release_iso}\3', text, count=1)
    _VERSION_FILE.write_text(text, encoding="utf-8")


def bump_patch(release_date: date | None = None) -> tuple[str, str]:
    """1.0.0 → 1.0.1. Atualiza ``RELEASE_DATE`` para hoje (ou ``release_date``). Retorna (nova_versão, data_iso)."""
    m, i, p = parse_semver(__version__)
    new = f"{m}.{i}.{p + 1}"
    when = (release_date or date.today()).isoformat()
    _write_version_file(new, when)
    return new, when


def bump_minor(release_date: date | None = None) -> tuple[str, str]:
    """1.0.0 → 1.1.0 (PATCH zera). Retorna (nova_versão, data_iso)."""
    m, i, _ = parse_semver(__version__)
    new = f"{m}.{i + 1}.0"
    when = (release_date or date.today()).isoformat()
    _write_version_file(new, when)
    return new, when


def bump_major(release_date: date | None = None) -> tuple[str, str]:
    """1.4.8 → 2.0.0. Retorna (nova_versão, data_iso)."""
    m, _, _ = parse_semver(__version__)
    new = f"{m + 1}.0.0"
    when = (release_date or date.today()).isoformat()
    _write_version_file(new, when)
    return new, when


def sugestao_bump_por_tipo_demanda(tipo: str | None) -> str:
    """
    Indica ``patch``, ``minor`` ou ``major`` conforme o tipo informado no cadastro
    (BUG, INCREMENTO, etc.). É orientação para o time, não altera arquivos.
    """
    t = (tipo or "").upper().strip().replace(" ", "_")
    if t in (
        "BREAKING",
        "BREAKING_CHANGE",
        "ESTRUTURAL",
        "REFATORACAO_ESTRUTURAL",
        "REFATORAÇÃO_ESTRUTURAL",
        "MAJOR",
    ):
        return "major"
    if t in (
        "BUG",
        "CORRECAO",
        "CORREÇÃO",
        "PATCH",
        "HOTFIX",
    ):
        return "patch"
    if t in (
        "INCREMENTO",
        "FEATURE",
        "MELHORIA",
        "MINOR",
        "FUNCIONALIDADE",
    ):
        return "minor"
    return "minor"


def sugestao_bump_por_mensagem_commit(mensagem: str | None) -> str:
    """
    Sugere bump a partir da mensagem de commit (Conventional Commits).

    - ``fix:`` / ``fix(scope):`` → patch
    - ``feat:`` / ``feat(scope):`` → minor
    - ``tipo!:`` / ``tipo(scope)!:`` ou corpo com ``BREAKING CHANGE`` → major
    """
    raw = (mensagem or "").strip()
    if not raw:
        return "minor"
    if "breaking change" in raw.lower():
        return "major"
    first = raw.splitlines()[0].strip()
    if re.match(r"^[a-z]+(\([^)]*\))?!:", first, re.I):
        return "major"
    fl = first.lower()
    if fl.startswith("fix:") or fl.startswith("fix("):
        return "patch"
    if fl.startswith("feat:") or fl.startswith("feat("):
        return "minor"
    return "minor"


def versao_consta_no_changelog(
    versao: str,
    texto_changelog: str | None = None,
) -> bool:
    """True se existir um cabeçalho ``## [versão]`` no README."""
    text = (
        texto_changelog
        if texto_changelog is not None
        else _CHANGELOG_FILE.read_text(encoding="utf-8")
    )
    return versao.strip() in _CHANGELOG_HEADING_RE.findall(text)


def changelog_alinhado_com_version_py() -> bool:
    """``__version__`` aparece como cabeçalho ``## [versão]`` no ``README.md`` (evita drift)."""
    if not _CHANGELOG_FILE.is_file():
        return False
    return versao_consta_no_changelog(__version__, _CHANGELOG_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Incrementa __version__ e RELEASE_DATE em version.py",
    )
    parser.add_argument(
        "nivel",
        choices=("patch", "minor", "major"),
        help="patch = correções; minor = funcionalidade; major = estrutural/incompatível",
    )
    args = parser.parse_args()
    anterior = __version__
    anterior_data = RELEASE_DATE
    fn = {"patch": bump_patch, "minor": bump_minor, "major": bump_major}[args.nivel]
    nova, release_iso = fn()
    print(f"Versão anterior: {anterior} (release em version.py: {anterior_data})")
    print(f"Nova versão: {nova}")
    print(f"Release date atribuída: {release_iso}")
    print("Lembrete: atualize README.md (secção Changelog) com ## [nova versão] — data e as mudanças.")
