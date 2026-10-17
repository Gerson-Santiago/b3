"""
Testes unitários para dashboard/charts/pie.py.

Cobre as 3 funções públicas:
  - pie_carteira
  - pie_carteira_por_categoria
  - pie_categoria

Estes testes servem como contrato para a refatoração DRY (Issue 3.1):
após a extração de _criar_donut(), todos devem continuar passando sem
nenhuma modificação aqui.
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts.pie import (
    pie_carteira,
    pie_carteira_por_categoria,
    pie_categoria,
)
from dashboard.charts.defaults import HEIGHT_PIE, HEIGHT_PIE_SMALL


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pos_sample():
    """DataFrame mínimo com as colunas exigidas por pie_carteira e pie_categoria."""
    return pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3", "BBAS3"],
            "valor_abs": [5000.0, 3000.0, 2000.0],
            "categoria": ["Ações", "Ações", "Ações"],
        }
    )


@pytest.fixture
def pos_categoria_sample():
    """DataFrame mínimo com as colunas exigidas por pie_carteira_por_categoria."""
    return pd.DataFrame(
        {
            "categoria": ["Ações", "FIIs", "Renda Fixa"],
            "valor": [6000.0, 2500.0, 1500.0],
        }
    )


# ---------------------------------------------------------------------------
# pie_carteira
# ---------------------------------------------------------------------------


class TestPieCarteira:
    def test_retorna_go_figure(self, pos_sample):
        fig = pie_carteira(pos_sample)
        assert isinstance(fig, go.Figure)

    def test_tem_dados(self, pos_sample):
        fig = pie_carteira(pos_sample)
        assert len(fig.data) > 0

    def test_hole_donut(self, pos_sample):
        fig = pie_carteira(pos_sample)
        assert fig.data[0].hole == pytest.approx(0.45)

    def test_altura(self, pos_sample):
        fig = pie_carteira(pos_sample)
        assert fig.layout.height == HEIGHT_PIE

    def test_separadores_ptbr(self, pos_sample):
        fig = pie_carteira(pos_sample)
        assert fig.layout.separators == ",."


# ---------------------------------------------------------------------------
# pie_carteira_por_categoria
# ---------------------------------------------------------------------------


class TestPieCarteiraPorCategoria:
    def test_retorna_go_figure(self, pos_categoria_sample):
        fig = pie_carteira_por_categoria(pos_categoria_sample)
        assert isinstance(fig, go.Figure)

    def test_tem_dados(self, pos_categoria_sample):
        fig = pie_carteira_por_categoria(pos_categoria_sample)
        assert len(fig.data) > 0

    def test_hole_donut(self, pos_categoria_sample):
        fig = pie_carteira_por_categoria(pos_categoria_sample)
        assert fig.data[0].hole == pytest.approx(0.45)

    def test_altura(self, pos_categoria_sample):
        fig = pie_carteira_por_categoria(pos_categoria_sample)
        assert fig.layout.height == HEIGHT_PIE


# ---------------------------------------------------------------------------
# pie_categoria
# ---------------------------------------------------------------------------


class TestPieCategoria:
    def test_retorna_go_figure(self, pos_sample):
        fig = pie_categoria(pos_sample)
        assert isinstance(fig, go.Figure)

    def test_tem_dados(self, pos_sample):
        fig = pie_categoria(pos_sample)
        assert len(fig.data) > 0

    def test_titulo_customizado(self, pos_sample):
        titulo = "Meu Título"
        fig = pie_categoria(pos_sample, titulo=titulo)
        assert fig.layout.title.text == titulo

    def test_titulo_padrao(self, pos_sample):
        fig = pie_categoria(pos_sample)
        assert fig.layout.title.text == "Distribuição por Ativo"

    def test_altura(self, pos_sample):
        fig = pie_categoria(pos_sample)
        assert fig.layout.height == HEIGHT_PIE_SMALL

    def test_hole_donut(self, pos_sample):
        fig = pie_categoria(pos_sample)
        assert fig.data[0].hole == pytest.approx(0.45)
