"""Testes unitários para dashboard.loader."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import patch
import pandas as pd
import pytest

from dashboard.loader import read_b3_file


def test_read_b3_file_none_lanca_excecao():
    with pytest.raises(ValueError, match="Arquivo B3 não informado"):
        read_b3_file(None)


@patch("dashboard.loader.read_posicao_file", return_value=pd.DataFrame({"a": [1]}))
def test_read_b3_file_bytesio_excel(mock_excel):
    buf = BytesIO(b"dummy")
    buf.name = "posicao.xlsx"
    df = read_b3_file(buf)
    assert not df.empty
    mock_excel.assert_called_once()


@patch("dashboard.loader.read_posicao_file", side_effect=Exception("erro"))
@patch("dashboard.loader.read_movimentacao_file", return_value=pd.DataFrame({"b": [2]}))
def test_read_b3_file_bytesio_fallback_csv(mock_csv, mock_excel):
    buf = BytesIO(b"dummy")
    buf.name = "posicao.xlsx"
    df = read_b3_file(buf)
    assert not df.empty
    mock_csv.assert_called_once()


@patch("dashboard.loader.read_movimentacao_file", return_value=pd.DataFrame({"c": [3]}))
def test_read_b3_file_bytesio_csv_direto(mock_csv):
    buf = BytesIO(b"dummy")
    buf.name = "movimentacao.csv"
    df = read_b3_file(buf)
    assert not df.empty
    mock_csv.assert_called_once()


@patch("dashboard.loader.read_posicao_file", side_effect=Exception("erro"))
@patch("dashboard.loader.read_movimentacao_file", return_value=pd.DataFrame({"d": [4]}))
def test_read_b3_file_path_fallback(mock_csv, mock_excel, tmp_path):
    p = tmp_path / "teste.xlsx"
    p.touch()
    df = read_b3_file(p)
    assert not df.empty
    mock_csv.assert_called_once()


@patch("dashboard.loader.read_movimentacao_file", return_value=pd.DataFrame({"e": [5]}))
def test_read_b3_file_path_csv(mock_csv, tmp_path):
    p = tmp_path / "mov.csv"
    p.touch()
    df = read_b3_file(p)
    assert not df.empty
    mock_csv.assert_called_once()
