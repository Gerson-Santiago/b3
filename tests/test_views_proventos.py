"""Testes unitários para dashboard.views.proventos."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.state import DashboardState
from dashboard.views.proventos import render


@pytest.fixture()
def state_proventos_mock():
    s = MagicMock(spec=DashboardState)
    s.proventos = pd.DataFrame(
        {
            "mes": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
            "tipo_provento": ["Dividendo", "JCP"],
            "valor_liquido": [100.0, 50.0],
        }
    )
    s.dy_metrics = pd.DataFrame(
        {
            "ticker": ["PETR4", "VALE3"],
            "produto": ["PETR4", "VALE3"],
            "valor_atual": [1000.0, 2000.0],
            "custo_total": [800.0, 1800.0],
            "proventos_12m": [100.0, 120.0],
            "dy_ltm_pct": [10.0, 6.0],
            "yield_on_cost_pct": [12.5, 6.7],
        }
    )
    s.calendario_proventos = pd.DataFrame(
        {
            "data": [pd.Timestamp("2024-02-15"), pd.Timestamp("2024-01-15")],
            "ativo": ["VALE3", "PETR4"],
            "tipo_provento": ["JCP", "Dividendo"],
            "valor_liquido": [50.0, 100.0],
        }
    )
    return s


@patch("streamlit.info")
def test_render_proventos_vazio(mock_info):
    s = MagicMock(spec=DashboardState)
    s.proventos = pd.DataFrame()
    s.dy_metrics = pd.DataFrame()
    s.calendario_proventos = pd.DataFrame()

    render(s)
    assert mock_info.call_count >= 3


@patch("streamlit.dataframe")
@patch("streamlit.plotly_chart")
@patch("streamlit.toggle", side_effect=[True, True])
@patch("streamlit.columns")
@patch("streamlit.caption")
@patch("streamlit.markdown")
def test_render_proventos_com_dados(
    mock_md,
    mock_caption,
    mock_cols,
    mock_toggle,
    mock_chart,
    mock_df,
    state_proventos_mock,
):
    mock_cols.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    render(state_proventos_mock)

    assert mock_chart.call_count >= 2
    assert mock_df.call_count >= 2
