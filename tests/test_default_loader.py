"""Testes para dashboard.loaders.default_loader (TDD Red → Green → Refactor)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from dashboard.loaders.default_loader import load_default


@pytest.fixture()
def df_stub():
    return pd.DataFrame({"produto": ["PETR4"], "quantidade": [10.0]})


@pytest.fixture()
def reader_ok(df_stub):
    """Reader que sempre retorna um DataFrame válido."""
    return MagicMock(return_value=df_stub)


@pytest.fixture()
def reader_vazio():
    """Reader que retorna DataFrame vazio (arquivo inválido)."""
    return MagicMock(return_value=pd.DataFrame())


class TestLoadDefaultArquivoEncontrado:
    def test_retorna_dataframe_quando_arquivo_existe(self, tmp_path, reader_ok, df_stub):
        arquivo = tmp_path / "movimentacao-2024-01-01.xlsx"
        arquivo.touch()

        resultado = load_default("movimentacao", reader_ok, search_dirs=[(tmp_path, "movimentacao")])

        assert not resultado.empty
        reader_ok.assert_called_once_with(arquivo)

    def test_usa_primeiro_diretorio_com_arquivo(self, tmp_path, reader_ok, df_stub):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "posicao-2024-01-01.xlsx").touch()
        (dir_b / "posicao-2024-06-01.xlsx").touch()

        resultado = load_default("posicao", reader_ok, search_dirs=[(dir_a, "posicao"), (dir_b, "posicao")])

        assert not resultado.empty
        # Deve ter sido chamado com o arquivo do primeiro diretório
        chamado_com = reader_ok.call_args[0][0]
        assert chamado_com.parent == dir_a


class TestLoadDefaultSemArquivo:
    def test_lanca_file_not_found_quando_nenhum_arquivo(self, tmp_path, reader_ok):
        vazio = tmp_path / "vazio"
        vazio.mkdir()

        with pytest.raises(FileNotFoundError, match="movimentacao"):
            load_default("movimentacao", reader_ok, search_dirs=[(vazio, "movimentacao")])

    def test_pula_diretorios_inexistentes(self, tmp_path, reader_ok, df_stub):
        inexistente = tmp_path / "nao_existe"
        real = tmp_path / "real"
        real.mkdir()
        (real / "movimentacao-2024-01-01.xlsx").touch()

        resultado = load_default(
            "movimentacao",
            reader_ok,
            search_dirs=[(inexistente, "movimentacao"), (real, "movimentacao")],
        )
        assert not resultado.empty

    def test_lista_de_dirs_vazia_lanca_file_not_found(self, reader_ok):
        with pytest.raises(FileNotFoundError):
            load_default("posicao", reader_ok, search_dirs=[])


class TestLoadDefaultReaderFalha:
    def test_propaga_excecao_do_reader(self, tmp_path):
        arquivo = tmp_path / "movimentacao-2024-01-01.xlsx"
        arquivo.touch()
        reader_quebrado = MagicMock(side_effect=ValueError("arquivo corrompido"))

        with pytest.raises(ValueError, match="corrompido"):
            load_default("movimentacao", reader_quebrado, search_dirs=[(tmp_path, "movimentacao")])
