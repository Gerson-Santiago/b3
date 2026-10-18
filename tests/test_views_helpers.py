"""Testes para dashboard.views._helpers."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.views._helpers import (
    _obter_tipo_e_grupo,
    _render_card,
    render_cards_grid,
    render_section,
)


def test_obter_tipo_e_grupo():
    assert _obter_tipo_e_grupo("AÇÕES") == ("Ação", "das Ações")
    assert _obter_tipo_e_grupo("Acoes") == ("Ação", "das Ações")
    assert _obter_tipo_e_grupo("AÇÃO") == ("Ação", "das Ações")
    assert _obter_tipo_e_grupo("BDR") == ("BDR", "dos BDRs")
    assert _obter_tipo_e_grupo("BDRS") == ("BDR", "dos BDRs")
    assert _obter_tipo_e_grupo("Tesouro Direto") == ("Tesouro", "do Tesouro")
    assert _obter_tipo_e_grupo("FII") == ("FII", "dos FIIs")
    assert _obter_tipo_e_grupo("FIIS") == ("FII", "dos FIIs")
    assert _obter_tipo_e_grupo("Cripto") == ("Cripto", "de Cripto")
    assert _obter_tipo_e_grupo("") == ("Ativo", "de Ativo")


@patch("streamlit.dataframe")
@patch("streamlit.info")
@patch("streamlit.markdown")
def test_render_section(mock_md, mock_info, mock_df):
    empty = pd.DataFrame()
    render_section(empty, "Título Teste", "Msg Vazia")
    mock_md.assert_called_with("#### Título Teste")
    mock_info.assert_called_with("Msg Vazia")

    non_empty = pd.DataFrame({"col": [1, 2]})
    render_section(non_empty, "Título Teste", "Msg Vazia")
    mock_df.assert_called_once()


@patch("streamlit.markdown")
@patch("streamlit.columns")
@patch("streamlit.container")
@patch("streamlit.info")
def test_render_cards_grid(mock_info, mock_container, mock_columns, mock_md):
    # Empty
    render_cards_grid(pd.DataFrame(), "Título", "Sem dados")
    mock_info.assert_called_with("Sem dados")

    # Non-empty
    def _mock_cols_factory(spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [MagicMock() for _ in range(n)]

    mock_columns.side_effect = _mock_cols_factory
    df = pd.DataFrame(
        [
            {
                "produto": "PETR4",
                "categoria": "Ações",
                "quantidade": 100,
                "valor_abs": 3500.0,
                "preco_medio": 30.0,
                "custo_total": 3000.0,
                "pl": 500.0,
                "variacao_pct": 16.67,
                "peso_pct": 10.0,
                "peso_pct_no_produto": 100.0,
            },
            {
                "produto": "Tesouro Selic 2029",
                "categoria": "Tesouro Direto",
                "quantidade": 0.5,
                "valor_abs": 7500.0,
                "preco_medio": 14000.0,
                "custo_total": 7000.0,
                "pl": -100.0,
                "variacao_pct": -1.43,
                "peso_pct": 20.0,
                "peso_pct_no_produto": 100.0,
            },
        ]
    )
    render_cards_grid(df, "Meus Cards", "Sem dados")
    assert mock_md.called
