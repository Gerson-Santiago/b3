"""Testes unitários para dashboard.charts.bars (bar_proventos e bar_dy)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts.bars import bar_dy, bar_lucro_prejuizo, bar_proventos
from dashboard.charts.defaults import (
    COLOR_DIVIDENDO,
    COLOR_FII,
    COLOR_JCP,
    COLOR_LUCRO,
    COLOR_PATRIMONIO,
    COLOR_PREJUIZO,
    HEIGHT_BAR,
)


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


def test_bar_proventos_com_acumulado_padrao_retorna_duas_traces(proventos_sample):
    fig = bar_proventos(proventos_sample)
    assert len(fig.data) == 2
    assert fig.data[0].type == "bar"
    assert fig.data[1].type == "scatter"
    assert fig.data[1].mode == "lines+markers"
    assert fig.data[1].line.color == COLOR_PATRIMONIO
    assert fig.data[1].yaxis == "y2"
    assert fig.layout.yaxis2.overlaying == "y"


def test_bar_proventos_sem_acumulado_retorna_uma_trace(proventos_sample):
    fig = bar_proventos(proventos_sample, mostrar_acumulado=False)
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"


def test_bar_proventos_acumulado_valores_corretos(proventos_sample):
    fig = bar_proventos(proventos_sample, mostrar_acumulado=True)
    expected_acumulado = [150.0, 370.50, 550.50]
    assert list(fig.data[1].y) == expected_acumulado


def test_bar_proventos_acumulado_reinicia_na_virada_do_ano():
    df_multi_ano = pd.DataFrame(
        {
            "mes": ["2023-11", "2023-12", "2024-01", "2024-02"],
            "valor_liquido": [100.0, 150.0, 200.0, 50.0],
        }
    )
    fig = bar_proventos(df_multi_ano, mostrar_acumulado=True)
    expected_acumulado = [100.0, 250.0, 200.0, 250.0]
    assert list(fig.data[1].y) == expected_acumulado


def test_bar_proventos_vazio_com_mostrar_acumulado():
    empty_df = pd.DataFrame(columns=["mes", "valor_liquido"])
    fig = bar_proventos(empty_df, mostrar_acumulado=True)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_bar_proventos_segmentar_por_tipo_traces_e_cores():
    df_tipos = pd.DataFrame(
        {
            "mes": ["2024-01", "2024-01", "2024-01", "2024-02"],
            "tipo_provento": ["Dividendo", "JCP", "Rendimento FII", "Dividendo"],
            "valor_liquido": [100.0, 50.0, 30.0, 120.0],
        }
    )
    fig = bar_proventos(df_tipos, segmentar_por_tipo=True, mostrar_acumulado=False)
    assert len(fig.data) == 3
    assert fig.layout.barmode == "stack"
    trace_names = [t.name for t in fig.data]
    assert "Dividendo" in trace_names
    assert "JCP" in trace_names
    assert "Rendimento FII" in trace_names

    # Validar cores atribuídas por tipo
    cor_por_tipo = {t.name: t.marker.color for t in fig.data}
    assert cor_por_tipo["Dividendo"] == COLOR_DIVIDENDO
    assert cor_por_tipo["JCP"] == COLOR_JCP
    assert cor_por_tipo["Rendimento FII"] == COLOR_FII


def test_bar_proventos_segmentar_por_tipo_com_acumulado():
    df_tipos = pd.DataFrame(
        {
            "mes": ["2024-01", "2024-01", "2024-02"],
            "tipo_provento": ["Dividendo", "JCP", "Dividendo"],
            "valor_liquido": [100.0, 50.0, 200.0],
        }
    )
    fig = bar_proventos(df_tipos, segmentar_por_tipo=True, mostrar_acumulado=True)
    # 2 traces de barra + 1 trace de acumulado anual no eixo Y2
    assert len(fig.data) == 3
    bar_traces = [t for t in fig.data if t.type == "bar"]
    scatter_traces = [t for t in fig.data if t.type == "scatter"]
    assert len(bar_traces) == 2
    assert len(scatter_traces) == 1
    # Curva acumulada mensal total: 100+50 = 150 em jan, 150+200 = 350 em fev
    assert list(scatter_traces[0].y) == [150.0, 350.0]
    assert scatter_traces[0].yaxis == "y2"


def test_bar_proventos_segmentar_por_tipo_fallback_sem_coluna_tipo(proventos_sample):
    # proventos_sample só tem ["mes", "valor_liquido"]
    fig = bar_proventos(proventos_sample, segmentar_por_tipo=True, mostrar_acumulado=False)
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"


def test_bar_proventos_segmentar_por_tipo_quando_false_unifica_barras():
    df_tipos = pd.DataFrame(
        {
            "mes": ["2024-01", "2024-01"],
            "tipo_provento": ["Dividendo", "JCP"],
            "valor_liquido": [100.0, 50.0],
        }
    )
    fig = bar_proventos(df_tipos, segmentar_por_tipo=False, mostrar_acumulado=False)
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"
    assert list(fig.data[0].y) == [150.0]


def test_bar_proventos_converte_valor_liquido_nao_numerico_nao_lanca_excecao():
    """Strings não numéricas são convertidas para 0.0 via pd.to_numeric(errors='coerce').
    A normalização de strings pt-BR (ex: '150,00') é responsabilidade do loader, não do chart.
    """
    df_str = pd.DataFrame(
        {
            "mes": ["2024-01", "2024-02"],
            "valor_liquido": ["abc", None],
        }
    )
    fig = bar_proventos(df_str, mostrar_acumulado=False)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert list(fig.data[0].y) == [0.0, 0.0]


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


# ---------------------------------------------------------------------------
# bar_distribuicao_ativos
# ---------------------------------------------------------------------------


class TestBarDistribuicaoAtivos:
    @pytest.fixture()
    def pos_sample(self):
        return pd.DataFrame(
            {
                "produto": ["PETR4", "VALE3", "KNCR11", "Tesouro Selic 2029"],
                "valor_abs": [10000.0, 5000.0, 3000.0, 2000.0],
                "categoria": ["Ações", "Ações", "FIIs", "Tesouro Direto"],
            }
        )

    def test_retorna_figura_valida(self, pos_sample):
        from dashboard.charts.bars import bar_distribuicao_ativos

        fig = bar_distribuicao_ativos(pos_sample)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        assert fig.data[0].orientation == "h"

    def test_ordenacao_e_maior_no_topo(self, pos_sample):
        from dashboard.charts.bars import bar_distribuicao_ativos

        fig = bar_distribuicao_ativos(pos_sample)
        # No Plotly com barras horizontais invertidas para exibição decrescente,
        # o maior ativo fica na última posição do array de Y para ficar no topo visual
        todos_y = []
        for d in fig.data:
            todos_y.extend(list(d.y))
        assert "PETR4" in todos_y

    def test_top_n(self, pos_sample):
        from dashboard.charts.bars import bar_distribuicao_ativos

        fig = bar_distribuicao_ativos(pos_sample, top_n=2)
        todos_y = []
        for d in fig.data:
            todos_y.extend(list(d.y))
        assert len(todos_y) == 2
        assert "PETR4" in todos_y
        assert "VALE3" in todos_y
        assert "KNCR11" not in todos_y

    def test_fallback_coluna_valor(self):
        from dashboard.charts.bars import bar_distribuicao_ativos

        df = pd.DataFrame(
            {
                "produto": ["ITUB4", "BBDC4"],
                "valor": [4000.0, 1000.0],
            }
        )
        fig = bar_distribuicao_ativos(df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_dataframe_vazio_ou_nulo(self):
        from dashboard.charts.bars import bar_distribuicao_ativos

        fig_none = bar_distribuicao_ativos(None)
        assert isinstance(fig_none, go.Figure)
        assert len(fig_none.data) == 0

        fig_empty = bar_distribuicao_ativos(pd.DataFrame())
        assert isinstance(fig_empty, go.Figure)
        assert len(fig_empty.data) == 0

        fig_zeros = bar_distribuicao_ativos(pd.DataFrame({"produto": ["A"], "valor_abs": [0.0]}))
        assert isinstance(fig_zeros, go.Figure)
        assert len(fig_zeros.data) == 0


