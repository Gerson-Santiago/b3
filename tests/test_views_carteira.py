"""Testes unitários para dashboard.views.carteira."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.models.resumo import ResumoAlocacao, ResumoCarteira, ResumoMacro
from dashboard.state import DashboardState
from dashboard.views.carteira import (
    _render_alocacao_macro,
    _render_cards_custodia,
    _render_resultado_pl,
    render,
)


@pytest.fixture()
def state_mock():
    s = MagicMock(spec=DashboardState)
    s.resumo = ResumoCarteira(
        bolsa=ResumoMacro(nome="Bolsa de Valores", patrimonio=10000.0, custo=8000.0, pl=2000.0, pl_pct=25.0, peso_pct=66.7),
        tesouro=ResumoMacro(nome="Tesouro Direto", patrimonio=5000.0, custo=4500.0, pl=500.0, pl_pct=11.1, peso_pct=33.3),
        patrimonio_total=15000.0,
        custo_total=12500.0,
        pl_total=2500.0,
        pl_pct=20.0,
    )
    s.pos = pd.DataFrame(
        {
            "produto": ["PETR4", "Tesouro Selic 2029"],
            "categoria": ["Ações", "TESOURO"],
            "quantidade": [100.0, 1.0],
            "valor": [10000.0, 5000.0],
            "valor_abs": [10000.0, 5000.0],
        }
    )
    s.pos_filtered = s.pos.copy()
    s.pos_categoria = pd.DataFrame(
        {
            "categoria": ["Ações", "Tesouro Direto"],
            "valor": [10000.0, 5000.0],
            "quantidade": [100.0, 1.0],
        }
    )
    s.pos_categoria_agrupada = s.pos_categoria.copy()
    s.pos_5_classes = pd.DataFrame(
        {
            "classe": ["Ações", "Tesouro Direto"],
            "categoria": ["Ações", "Tesouro Direto"],
            "valor": [10000.0, 5000.0],
            "peso_pct": [66.7, 33.3],
        }
    )
    s.pos_cards = pd.DataFrame(
        [
            {
                "produto": "PETR4",
                "categoria": "AÇÕES",
                "quantidade": 100.0,
                "valor_abs": 10000.0,
                "preco_medio": 80.0,
                "custo_total": 8000.0,
                "pl": 2000.0,
                "variacao_pct": 25.0,
                "peso_pct": 66.7,
                "peso_pct_no_produto": 100.0,
            },
            {
                "produto": "Tesouro Selic 2029",
                "categoria": "TESOURO",
                "quantidade": 1.0,
                "valor_abs": 5000.0,
                "preco_medio": 4500.0,
                "custo_total": 4500.0,
                "pl": 500.0,
                "variacao_pct": 11.1,
                "peso_pct": 33.3,
                "peso_pct_no_produto": 100.0,
            },
        ]
    )
    return s


@patch("streamlit.info")
def test_render_vazio(mock_info):
    s = MagicMock(spec=DashboardState)
    s.pos = pd.DataFrame()
    render(s)
    mock_info.assert_called_with("Nenhum ativo encontrado para os filtros selecionados.")


@patch("streamlit.plotly_chart")
@patch("streamlit.toggle", return_value=True)
@patch("streamlit.selectbox", return_value="5 Classes de Ativos")
@patch("streamlit.radio", return_value="Gráficos de Pizza / Donut")
@patch("streamlit.expander")
@patch("streamlit.columns")
@patch("streamlit.metric")
@patch("streamlit.markdown")
@patch("streamlit.progress")
def test_render_com_dados_pizza(
    mock_progress,
    mock_md,
    mock_metric,
    mock_cols,
    mock_expander,
    mock_radio,
    mock_select,
    mock_toggle,
    mock_chart,
    state_mock,
):
    mock_cols.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    render(state_mock)
    assert mock_chart.called


@patch("streamlit.plotly_chart")
@patch("streamlit.selectbox", return_value="5 Classes de Ativos")
@patch("streamlit.radio", return_value="Ranking em Barras (Ativos)")
@patch("streamlit.expander")
@patch("streamlit.columns")
@patch("streamlit.metric")
@patch("streamlit.markdown")
@patch("streamlit.progress")
def test_render_com_dados_ranking_barras(
    mock_progress,
    mock_md,
    mock_metric,
    mock_cols,
    mock_expander,
    mock_radio,
    mock_select,
    mock_chart,
    state_mock,
):
    mock_cols.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    render(state_mock)
    assert mock_chart.called


@patch("streamlit.plotly_chart")
@patch("streamlit.selectbox", return_value="5 Classes de Ativos")
@patch("streamlit.radio", return_value="Mapa de Árvore (Treemap)")
@patch("streamlit.expander")
@patch("streamlit.columns")
@patch("streamlit.metric")
@patch("streamlit.markdown")
@patch("streamlit.progress")
def test_render_com_dados_treemap(
    mock_progress,
    mock_md,
    mock_metric,
    mock_cols,
    mock_expander,
    mock_radio,
    mock_select,
    mock_chart,
    state_mock,
):
    mock_cols.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    render(state_mock)
    assert mock_chart.called


@patch("streamlit.plotly_chart")
@patch("streamlit.columns")
@patch("streamlit.metric")
@patch("streamlit.caption")
@patch("streamlit.markdown")
def test_render_alocacao_macro_donut(
    mock_md,
    mock_caption,
    mock_metric,
    mock_cols,
    mock_chart,
    state_mock,
):
    mock_cols.side_effect = lambda spec: [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
    _render_alocacao_macro(state_mock)
    assert mock_chart.called
