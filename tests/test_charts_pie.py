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


# ---------------------------------------------------------------------------
# agrupar_posicao_outros e melhorias do Donut
# ---------------------------------------------------------------------------


class TestAgruparPosicaoOutros:
    def test_agrupa_pequenos_com_sucesso(self):
        from dashboard.charts.pie import agrupar_posicao_outros

        df = pd.DataFrame(
            {
                "produto": ["ATIVO_A", "ATIVO_B", "PEQ_1", "PEQ_2", "PEQ_3"],
                "valor_abs": [8000.0, 1800.0, 50.0, 80.0, 70.0],  # total = 10000.0
            }
        )
        res = agrupar_posicao_outros(df, limite_pct=2.0)
        # PEQ_1 (0.5%), PEQ_2 (0.8%), PEQ_3 (0.7%) devem ser agrupados em 'Outros (3 ativos)'
        assert len(res) == 3
        assert "Outros (3 ativos)" in res["produto"].values
        outros_val = res.loc[res["produto"] == "Outros (3 ativos)", "valor_abs"].values[0]
        assert outros_val == pytest.approx(200.0)

    def test_nao_agrupa_se_menos_de_dois_pequenos(self):
        from dashboard.charts.pie import agrupar_posicao_outros

        df = pd.DataFrame(
            {
                "produto": ["ATIVO_A", "PEQ_1"],
                "valor_abs": [9900.0, 100.0],
            }
        )
        res = agrupar_posicao_outros(df, limite_pct=2.0)
        assert len(res) == 2
        assert "Outros" not in res["produto"].values[1]

    def test_df_vazio_ou_nulo(self):
        from dashboard.charts.pie import agrupar_posicao_outros

        assert agrupar_posicao_outros(None) is None
        empty_df = pd.DataFrame()
        assert agrupar_posicao_outros(empty_df).empty

    def test_agrupar_com_max_itens(self):
        from dashboard.charts.pie import agrupar_posicao_outros

        df = pd.DataFrame(
            {
                "produto": ["A", "B", "C", "D"],
                "valor_abs": [40.0, 30.0, 20.0, 10.0],
            }
        )
        res = agrupar_posicao_outros(df, limite_pct=0.0, max_itens=2)
        assert len(res) == 3
        assert "Outros (2 ativos)" in res["produto"].values

    def test_total_zero_ou_negativo(self):
        from dashboard.charts.pie import agrupar_posicao_outros

        df = pd.DataFrame({"produto": ["A", "B"], "valor_abs": [0.0, 0.0]})
        res = agrupar_posicao_outros(df)
        assert len(res) == 2

    def test_pie_carteira_vazio(self):
        fig = pie_carteira(pd.DataFrame())
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0

    def test_pie_carteira_com_agrupamento(self):
        df = pd.DataFrame(
            {
                "produto": ["A1", "A2", "P1", "P2"],
                "valor_abs": [5000.0, 4800.0, 100.0, 100.0],
            }
        )
        fig = pie_carteira(df, limite_outros_pct=3.0)
        assert isinstance(fig, go.Figure)
        labels = list(fig.data[0].labels)
        assert "Outros (2 ativos)" in labels
        # Confirma legenda lateral e anotação com Total
        assert fig.layout.legend.orientation == "v"
        assert len(fig.layout.annotations) > 0
        assert "Total" in fig.layout.annotations[0].text


