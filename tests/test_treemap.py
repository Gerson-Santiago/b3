"""Testes unitários para dashboard.charts.treemap (Treemap e Sunburst)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts.defaults import HEIGHT_TREEMAP
from dashboard.charts.treemap import (
    _HOVER_HIERARQUIA,
    _figura_hierarquia_vazia,
    sunburst_carteira,
    treemap_carteira,
)


@pytest.fixture()
def pos_sample():
    return pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3", "GOGL35", "Tesouro Selic 2028"],
            "quantidade": [10.0, 5.0, 2.0, 1.0],
            "valor": [500.0, 300.0, 400.0, 1000.0],
            "valor_abs": [500.0, 300.0, 400.0, 1000.0],
            "categoria": ["AÇÕES", "AÇÕES", "BDR", "TESOURO"],
        }
    )


def test_treemap_carteira_retorna_figura_valida(pos_sample):
    fig = treemap_carteira(pos_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    assert fig.layout.height == HEIGHT_TREEMAP
    assert fig.layout.separators == ",."


def test_treemap_carteira_vazio_nao_lanca_excecao():
    empty_df = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
    fig = treemap_carteira(empty_df)
    assert isinstance(fig, go.Figure)
    assert fig.layout.height == HEIGHT_TREEMAP


def test_treemap_carteira_agrupa_bolsa_quando_separar_falso(pos_sample):
    fig = treemap_carteira(pos_sample, separar_bdr_acoes=False)
    labels = list(fig.data[0].labels)
    assert "Bolsa de Valores" in labels
    assert "Tesouro Direto" in labels
    assert "AÇÕES" not in labels


def test_treemap_carteira_separa_bdr_quando_separar_verdadeiro(pos_sample):
    fig = treemap_carteira(pos_sample, separar_bdr_acoes=True)
    labels = list(fig.data[0].labels)
    assert "AÇÕES" in labels
    assert "BDR" in labels
    assert "Bolsa de Valores" not in labels


def test_sunburst_carteira_retorna_figura_valida(pos_sample):
    fig = sunburst_carteira(pos_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    assert fig.layout.height == HEIGHT_TREEMAP


def test_sunburst_carteira_vazio_nao_lanca_excecao():
    empty_df = pd.DataFrame()
    fig = sunburst_carteira(empty_df)
    assert isinstance(fig, go.Figure)
    assert fig.layout.height == HEIGHT_TREEMAP


def test_treemap_carteira_none_retorna_figura_vazia():
    fig = treemap_carteira(None, titulo="Carteira Vazia")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0
    assert fig.layout.title.text == "Carteira Vazia"
    assert fig.layout.height == HEIGHT_TREEMAP


def test_sunburst_carteira_none_retorna_figura_vazia():
    fig = sunburst_carteira(None, titulo="Hierarquia Vazia")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0
    assert fig.layout.title.text == "Hierarquia Vazia"
    assert fig.layout.height == HEIGHT_TREEMAP


def test_figura_hierarquia_vazia_helper():
    fig = _figura_hierarquia_vazia("Título Customizado", altura=420)
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "Título Customizado"
    assert fig.layout.height == 420


def test_hovertemplate_compartilhado_treemap_e_sunburst(pos_sample):
    fig_tree = treemap_carteira(pos_sample)
    fig_sun = sunburst_carteira(pos_sample)
    assert fig_tree.data[0].hovertemplate == _HOVER_HIERARQUIA
    assert fig_sun.data[0].hovertemplate == _HOVER_HIERARQUIA
