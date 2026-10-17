"""Testes unitários para dashboard.charts.bars (bar_proventos e bar_dy)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts.bars import bar_dy, bar_lucro_prejuizo, bar_proventos
from dashboard.charts.defaults import COLOR_LUCRO, COLOR_PREJUIZO, HEIGHT_BAR


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def proventos_sample():
    """DataFrame mínimo válido para bar_proventos."""
    return pd.DataFrame(
        {
            "mes": ["2024-01", "2024-02", "2024-03"],
            "valor_liquido": [150.0, 220.50, 180.0],
        }
    )


@pytest.fixture()
def dy_ltm_sample():
    """DataFrame com coluna preferencial dy_ltm_pct."""
    return pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3", "BBAS3"],
            "dy_ltm_pct": [8.5, 12.0, 10.3],
        }
    )


@pytest.fixture()
def dy_fallback_sample():
    """DataFrame sem dy_ltm_pct — deve usar dy_pct como fallback."""
    return pd.DataFrame(
        {
            "produto": ["ITUB4", "BBDC4"],
            "dy_pct": [6.2, 7.8],
        }
    )


# ---------------------------------------------------------------------------
# bar_proventos
# ---------------------------------------------------------------------------

def test_bar_proventos_retorna_figura_valida(proventos_sample):
    fig = bar_proventos(proventos_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_bar_proventos_altura_correta(proventos_sample):
    fig = bar_proventos(proventos_sample)
    assert fig.layout.height == HEIGHT_BAR


def test_bar_proventos_separadores_ptbr(proventos_sample):
    fig = bar_proventos(proventos_sample)
    assert fig.layout.separators == ",."


def test_bar_proventos_vazio_nao_lanca_excecao():
    empty_df = pd.DataFrame(columns=["mes", "valor_liquido"])
    fig = bar_proventos(empty_df)
    assert isinstance(fig, go.Figure)


def test_bar_proventos_hover_contem_real(proventos_sample):
    fig = bar_proventos(proventos_sample)
    hover = fig.data[0].hovertemplate
    assert "R$" in hover


# ---------------------------------------------------------------------------
# bar_dy — coluna preferencial dy_ltm_pct
# ---------------------------------------------------------------------------

def test_bar_dy_retorna_figura_valida(dy_ltm_sample):
    fig = bar_dy(dy_ltm_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_bar_dy_altura_correta(dy_ltm_sample):
    fig = bar_dy(dy_ltm_sample)
    assert fig.layout.height == HEIGHT_BAR


def test_bar_dy_hover_contem_percentual(dy_ltm_sample):
    fig = bar_dy(dy_ltm_sample)
    hover = fig.data[0].hovertemplate
    assert "%" in hover


# ---------------------------------------------------------------------------
# bar_dy — fallback para dy_pct quando dy_ltm_pct ausente
# ---------------------------------------------------------------------------

def test_bar_dy_fallback_coluna_dy_pct_nao_lanca_excecao(dy_fallback_sample):
    fig = bar_dy(dy_fallback_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_bar_dy_fallback_altura_correta(dy_fallback_sample):
    fig = bar_dy(dy_fallback_sample)
    assert fig.layout.height == HEIGHT_BAR


# ---------------------------------------------------------------------------
# bar_lucro_prejuizo (Issue 4.1)
# ---------------------------------------------------------------------------

@pytest.fixture()
def pos_cards_pl_sample():
    return pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3", "GOGL35", "SEM_CUSTO"],
            "custo_total": [500.0, 1000.0, 300.0, 0.0],
            "valor_abs": [650.0, 800.0, 360.0, 100.0],
            "pl": [150.0, -200.0, 60.0, 100.0],
            "variacao_pct": [30.0, -20.0, 20.0, 0.0],
        }
    )


def test_bar_lucro_prejuizo_retorna_figura_valida(pos_cards_pl_sample):
    fig = bar_lucro_prejuizo(pos_cards_pl_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    # Orientação horizontal: produto no eixo Y e P&L no eixo X
    assert fig.data[0].orientation == "h"
    assert fig.layout.height == HEIGHT_BAR


def test_bar_lucro_prejuizo_filtra_ativos_sem_custo(pos_cards_pl_sample):
    fig = bar_lucro_prejuizo(pos_cards_pl_sample)
    # Todos os produtos plotados em todas as traces
    produtos_plotados = []
    for trace in fig.data:
        produtos_plotados.extend(list(trace.y))
    assert "SEM_CUSTO" not in produtos_plotados
    assert "PETR4" in produtos_plotados
    assert "VALE3" in produtos_plotados


def test_bar_lucro_prejuizo_vazio_nao_lanca_excecao():
    empty_df = pd.DataFrame(columns=["produto", "custo_total", "valor_abs", "pl", "variacao_pct"])
    fig = bar_lucro_prejuizo(empty_df)
    assert isinstance(fig, go.Figure)
    assert fig.layout.height == HEIGHT_BAR


def test_bar_lucro_prejuizo_none_nao_lanca_excecao():
    fig = bar_lucro_prejuizo(None)
    assert isinstance(fig, go.Figure)
    assert fig.layout.height == HEIGHT_BAR


def test_bar_lucro_prejuizo_hover_contem_pl_e_variacao(pos_cards_pl_sample):
    fig = bar_lucro_prejuizo(pos_cards_pl_sample)
    for trace in fig.data:
        hover = trace.hovertemplate
        assert hover is not None
        assert "%" in hover
        assert "R$" in hover

