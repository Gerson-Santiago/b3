"""Testes unitários para dashboard.views.evolucao."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.state import DashboardState
from dashboard.views.evolucao import _OPCOES_PRODUTO, render


@pytest.fixture()
def state_evolucao_mock():
    s = MagicMock(spec=DashboardState)
    df_curva = pd.DataFrame(
        {
            "data": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
            "custo_acumulado": [1000.0, 2000.0],
            "patrimonio_liquido": [1100.0, 2300.0],
        }
    )
    dummy_dict = {"curva_aportes": df_curva, "curva_patrimonio": df_curva}
    s.evol_dict = dummy_dict
    s.evol_bolsa = dummy_dict
    s.evol_tesouro = dummy_dict
    s.evol_inflacao = dummy_dict
    s.evol_pos = dummy_dict
    s.evol_pre = dummy_dict
    s.mov_filtered = pd.DataFrame(
        {
            "data": [pd.Timestamp("2024-01-10")],
            "produto": ["PETR4"],
            "valor_liquido": [1000.0],
        }
    )
    return s


@patch("streamlit.dataframe")
@patch("streamlit.plotly_chart")
@patch("streamlit.radio", return_value="Consolidado")
@patch("streamlit.markdown")
def test_render_evolucao_consolidado(
    mock_md,
    mock_radio,
    mock_chart,
    mock_df,
    state_evolucao_mock,
):
    render(state_evolucao_mock)
    assert mock_chart.call_count == 2
    assert mock_df.call_count == 1


@pytest.mark.parametrize("opcao", _OPCOES_PRODUTO)
@patch("streamlit.dataframe")
@patch("streamlit.plotly_chart")
@patch("streamlit.markdown")
def test_render_evolucao_todas_opcoes(
    mock_md,
    mock_chart,
    mock_df,
    opcao,
    state_evolucao_mock,
):
    with patch("streamlit.radio", return_value=opcao):
        render(state_evolucao_mock)
    assert mock_chart.call_count == 2


@patch("streamlit.dataframe")
@patch("streamlit.plotly_chart")
@patch("streamlit.radio", return_value="Consolidado")
@patch("streamlit.markdown")
def test_render_evolucao_sem_movimentacoes(
    mock_md,
    mock_radio,
    mock_chart,
    mock_df,
    state_evolucao_mock,
):
    state_evolucao_mock.mov_filtered = pd.DataFrame()
    render(state_evolucao_mock)
    assert mock_chart.call_count == 2
    # Não renderiza detalhamento de movimentações se mov_filtered for vazio
    assert mock_df.call_count == 0
