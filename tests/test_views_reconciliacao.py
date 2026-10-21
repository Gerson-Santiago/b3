"""Testes unitários para dashboard.views.reconciliacao."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.models.qualidade import Aviso, RelatorioQualidade
from dashboard.state import DashboardState
from dashboard.views.reconciliacao import render


@pytest.fixture()
def state_reconciliacao_mock():
    s = MagicMock(spec=DashboardState)
    s.mov_filtered = pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3"],
            "data": [pd.Timestamp("2024-01-10"), pd.Timestamp("2024-01-15")],
            "qtd_liquida": [10.0, 5.0],
            "entrada_saida": ["Credito", "Credito"],
            "movimentacao": ["Compra", "Compra"],
        }
    )
    rq = RelatorioQualidade()
    rq.add(Aviso(tipo="ATIVO_DESCONHECIDO", produto="XYZ", detalhe="Teste"))
    s.qualidade = rq
    return s


@patch("streamlit.info")
def test_render_reconciliacao_vazio(mock_info):
    s = MagicMock(spec=DashboardState)
    s.mov_filtered = pd.DataFrame()
    pos_vazio = pd.DataFrame()

    render(s, pos_vazio, pd.Timestamp("2024-12-31"))
    mock_info.assert_called_once()


@patch("streamlit.success")
@patch("streamlit.warning")
@patch("streamlit.dataframe")
@patch("streamlit.markdown")
def test_render_reconciliacao_conciliado_100(
    mock_md,
    mock_df,
    mock_warn,
    mock_succ,
    state_reconciliacao_mock,
):
    pos_df = pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3"],
            "quantidade": [10.0, 5.0],
            "categoria": ["AÇÕES", "AÇÕES"],
        }
    )
    render(state_reconciliacao_mock, pos_df, pd.Timestamp("2024-12-31"))

    assert mock_df.called
    assert mock_succ.called


@patch("streamlit.success")
@patch("streamlit.warning")
@patch("streamlit.dataframe")
@patch("streamlit.markdown")
def test_render_reconciliacao_com_divergencias(
    mock_md,
    mock_df,
    mock_warn,
    mock_succ,
    state_reconciliacao_mock,
):
    pos_df = pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3"],
            "quantidade": [15.0, 5.0],  # PETR4 com divergência (15 vs 10)
            "categoria": ["AÇÕES", "AÇÕES"],
        }
    )
    render(state_reconciliacao_mock, pos_df, pd.Timestamp("2024-12-31"))

    assert mock_df.called
    assert mock_warn.called


@patch("streamlit.success")
@patch("streamlit.warning")
@patch("streamlit.dataframe")
@patch("streamlit.markdown")
def test_render_reconciliacao_proventos_ok(
    mock_md,
    mock_df,
    mock_warn,
    mock_succ,
    state_reconciliacao_mock,
):
    state_reconciliacao_mock.reconciliacao_proventos = pd.DataFrame(
        {
            "ativo": ["PETR4"],
            "total_movimentacao": [10.0],
            "total_extrato_proventos": [10.0],
            "delta": [0.0],
            "status": ["OK"],
        }
    )
    pos_df = pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3"],
            "quantidade": [10.0, 5.0],
            "categoria": ["AÇÕES", "AÇÕES"],
        }
    )
    render(state_reconciliacao_mock, pos_df, pd.Timestamp("2024-12-31"))

    assert mock_succ.called


@patch("streamlit.success")
@patch("streamlit.warning")
@patch("streamlit.dataframe")
@patch("streamlit.markdown")
def test_render_reconciliacao_proventos_divergente(
    mock_md,
    mock_df,
    mock_warn,
    mock_succ,
    state_reconciliacao_mock,
):
    state_reconciliacao_mock.reconciliacao_proventos = pd.DataFrame(
        {
            "ativo": ["PETR4"],
            "total_movimentacao": [10.0],
            "total_extrato_proventos": [20.0],
            "delta": [10.0],
            "status": ["Divergente"],
        }
    )
    pos_df = pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3"],
            "quantidade": [10.0, 5.0],
            "categoria": ["AÇÕES", "AÇÕES"],
        }
    )
    render(state_reconciliacao_mock, pos_df, pd.Timestamp("2024-12-31"))

    assert mock_warn.called

