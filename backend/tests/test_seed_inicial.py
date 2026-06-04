"""Smoke do seed inicial (sem exigir Postgres nos testes padrão)."""
from unittest.mock import MagicMock, patch

from db.seed_runner import _env_bool, executar_seed_inicial_se_necessario


def test_env_bool_defaults_true():
    with patch.dict("os.environ", {}, clear=False):
        assert _env_bool("SEED_INICIAL_ON_STARTUP_INEXISTENTE_X", default=True) is True


def test_seed_runner_skips_when_projetos_existem():
    with patch("db.seed_runner.contar_projetos", return_value=3):
        assert executar_seed_inicial_se_necessario() is False


def test_seed_runner_executa_quando_vazio():
    with patch("db.seed_runner.contar_projetos", return_value=0):
        with patch("db.seed_inicial.executar_seed", return_value={"projetos": 3}) as mock_run:
            assert executar_seed_inicial_se_necessario() is True
            mock_run.assert_called_once_with(force=False)
