"""Testes unitários para dashboard.charts.base (aplicar_layout_padrao)."""
from __future__ import annotations

import plotly.graph_objects as go
import pytest

from dashboard.charts.base import aplicar_layout_padrao
from dashboard.charts.defaults import FONT_FAMILY, MARGIN_DEFAULT


def test_aplicar_layout_padrao_retorna_mesma_figura():
    fig_in = go.Figure()
    fig_out = aplicar_layout_padrao(fig_in)
    assert fig_out is fig_in


def test_aplicar_layout_padrao_altura_padrao():
    fig = aplicar_layout_padrao(go.Figure())
    assert fig.layout.height == 400


def test_aplicar_layout_padrao_altura_customizada():
    fig = aplicar_layout_padrao(go.Figure(), altura=600)
    assert fig.layout.height == 600


def test_aplicar_layout_padrao_separadores_ptbr():
    fig = aplicar_layout_padrao(go.Figure())
    assert fig.layout.separators == ",."


def test_aplicar_layout_padrao_fonte_base():
    fig = aplicar_layout_padrao(go.Figure())
    assert "Arial" in fig.layout.font.family


def test_aplicar_layout_padrao_legenda_horizontal_true():
    fig = aplicar_layout_padrao(go.Figure(), legenda_horizontal=True)
    assert fig.layout.legend.orientation == "h"
    assert fig.layout.legend.yanchor == "bottom"
    assert fig.layout.legend.xanchor == "center"


def test_aplicar_layout_padrao_legenda_horizontal_false():
    fig = aplicar_layout_padrao(go.Figure(), legenda_horizontal=False)
    assert fig.layout.legend.orientation is None


def test_aplicar_layout_padrao_margens_padrao():
    fig = aplicar_layout_padrao(go.Figure())
    assert fig.layout.margin.l == MARGIN_DEFAULT["l"]
    assert fig.layout.margin.r == MARGIN_DEFAULT["r"]
    assert fig.layout.margin.t == MARGIN_DEFAULT["t"]
    assert fig.layout.margin.b == MARGIN_DEFAULT["b"]


def test_aplicar_layout_padrao_margens_customizadas():
    custom_margin = dict(l=0, r=0, t=0, b=0)
    fig = aplicar_layout_padrao(go.Figure(), margens=custom_margin)
    assert fig.layout.margin.l == 0
    assert fig.layout.margin.r == 0
    assert fig.layout.margin.t == 0
    assert fig.layout.margin.b == 0
