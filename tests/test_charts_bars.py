"""Testes unitários para dashboard.charts.bars (bar_proventos e bar_dy)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts.bars import bar_dy, bar_proventos
from dashboard.charts.defaults import HEIGHT_BAR


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
