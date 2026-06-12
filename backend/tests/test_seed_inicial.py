"""Smoke do seed inicial (sem exigir Postgres nos testes padrão)."""
from unittest.mock import MagicMock, patch

from db.seed_inicial import BUG_INDICES_MESMA_MATRIZ, executar_seed
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


def test_seed_duplica_alvo_matriz_para_par_de_bugs():
    alvos_bug = [
        (2.5, 3.5, 2, 3),
        (4.0, 1.5, 2, 2),
        (3.0, 4.0, 3, 2),
        (1.5, 2.0, 2, 2),
        (4.5, 3.0, 3, 3),
        (2.0, 5.0, 2, 3),
    ]
    alvos_inc = [(1.5, 4.5, 2, 3)] * 6
    alvos_bug_capturados: list[tuple[float, float, int, int]] = []

    def fake_inserir(_id_projeto, _nome, spec, alvo, _rng):
        if spec["tipo"] == "BUG":
            alvos_bug_capturados.append(alvo)
        return len(alvos_bug_capturados) + len(alvos_inc)

    with patch("db.seed_inicial._limpar_seed_anterior"):
        with patch("db.seed_inicial._ocupados_por_tipo", return_value=(set(), set())):
            with patch("db.seed_inicial._gerar_alvos", side_effect=[alvos_bug, alvos_inc]):
                with patch("db.seed_inicial.criar_projeto", return_value={"id_projeto": 1, "versao_atual": "1.0.0"}):
                    with patch("db.seed_inicial._inserir_demanda", side_effect=fake_inserir):
                        executar_seed(force=True)

    ref, dup = BUG_INDICES_MESMA_MATRIZ
    assert len(alvos_bug_capturados) >= dup + 1
    assert alvos_bug_capturados[ref] == alvos_bug_capturados[dup]
