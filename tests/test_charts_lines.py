"""Testes unitários para dashboard.charts.lines (line_evolucao e line_comparativo_patrimonio_e_aportes)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts.defaults import HEIGHT_LINE, HEIGHT_LINE_COMPARATIVO
from dashboard.charts.lines import (
    line_comparativo_patrimonio_e_aportes,
    line_evolucao,
    line_rentabilidade_acumulada,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def evol_sample():
    """DataFrame válido para line_evolucao."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "patrimonio": [10000.0, 11500.0, 12200.0],
        }
    )


@pytest.fixture()
def curva_aportes_sample():
    """DataFrame válido de aportes acumulados."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "custo_acumulado": [8000.0, 9000.0, 10000.0],
        }
    )


@pytest.fixture()
def curva_patrimonio_sample():
    """DataFrame válido de patrimônio consolidado."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "patrimonio_liquido": [8500.0, 9700.0, 11200.0],
        }
    )


# ---------------------------------------------------------------------------
# line_evolucao
# ---------------------------------------------------------------------------

def test_line_evolucao_retorna_figura_valida(evol_sample):
    fig = line_evolucao(evol_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_line_evolucao_altura_correta(evol_sample):
    fig = line_evolucao(evol_sample)
    assert fig.layout.height == HEIGHT_LINE


def test_line_evolucao_separadores_ptbr(evol_sample):
    fig = line_evolucao(evol_sample)
    assert fig.layout.separators == ",."


def test_line_evolucao_hover_contem_patrimonio(evol_sample):
    fig = line_evolucao(evol_sample)
    hover = fig.data[0].hovertemplate
    assert "Patrimônio" in hover


def test_line_evolucao_vazio_nao_lanca_excecao():
    empty_df = pd.DataFrame(columns=["data", "patrimonio"])
    fig = line_evolucao(empty_df)
    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# line_comparativo_patrimonio_e_aportes
# ---------------------------------------------------------------------------

def test_comparativo_ambos_presentes_retorna_duas_traces(
    curva_aportes_sample, curva_patrimonio_sample
):
    fig = line_comparativo_patrimonio_e_aportes(
        curva_aportes_sample, curva_patrimonio_sample
    )
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_comparativo_apenas_aportes_retorna_uma_trace(curva_aportes_sample):
    fig = line_comparativo_patrimonio_e_aportes(curva_aportes_sample, None)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "Custo Acumulado (Aportes)"


def test_comparativo_apenas_patrimonio_retorna_uma_trace(curva_patrimonio_sample):
    fig = line_comparativo_patrimonio_e_aportes(None, curva_patrimonio_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "Patrimônio Consolidado (Snapshots B3)"


def test_comparativo_ambos_none_retorna_zero_traces():
    fig = line_comparativo_patrimonio_e_aportes(None, None)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_comparativo_ambos_vazios_retorna_zero_traces():
    empty_aportes = pd.DataFrame(columns=["data", "custo_acumulado"])
    empty_patrimonio = pd.DataFrame(columns=["data", "patrimonio_liquido"])
    fig = line_comparativo_patrimonio_e_aportes(empty_aportes, empty_patrimonio)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_comparativo_altura_correta(curva_aportes_sample, curva_patrimonio_sample):
    fig = line_comparativo_patrimonio_e_aportes(
        curva_aportes_sample, curva_patrimonio_sample
    )
    assert fig.layout.height == HEIGHT_LINE_COMPARATIVO


def test_comparativo_separadores_ptbr(curva_aportes_sample, curva_patrimonio_sample):
    fig = line_comparativo_patrimonio_e_aportes(
        curva_aportes_sample, curva_patrimonio_sample
    )
    assert fig.layout.separators == ",."


def test_comparativo_hover_traces(curva_aportes_sample, curva_patrimonio_sample):
    fig = line_comparativo_patrimonio_e_aportes(
        curva_aportes_sample, curva_patrimonio_sample
    )
    assert "Aportes Acumulados" in fig.data[0].hovertemplate
    assert "Patrimônio Real" in fig.data[1].hovertemplate


# ---------------------------------------------------------------------------
# line_rentabilidade_acumulada
# ---------------------------------------------------------------------------

def test_rentabilidade_retorna_figura_valida(curva_patrimonio_sample):
    fig = line_rentabilidade_acumulada(curva_patrimonio_sample)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "Carteira"


def test_rentabilidade_calculo_percentual_acumulado(curva_patrimonio_sample):
    fig = line_rentabilidade_acumulada(curva_patrimonio_sample)
    y_vals = list(fig.data[0].y)
    # curva_patrimonio_sample: [8500.0, 9700.0, 11200.0]
    # primeiro ponto deve ser 0%
    assert y_vals[0] == pytest.approx(0.0)
    # segundo ponto: (9700/8500 - 1) * 100 = 14.1176...
    assert y_vals[1] == pytest.approx((9700.0 / 8500.0 - 1.0) * 100.0)
    # terceiro ponto: (11200/8500 - 1) * 100 = 31.7647...
    assert y_vals[2] == pytest.approx((11200.0 / 8500.0 - 1.0) * 100.0)


def test_rentabilidade_com_benchmark_retorna_duas_traces(curva_patrimonio_sample):
    bench_df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "retorno_pct": [0.0, 1.0, 2.2],
        }
    )
    fig = line_rentabilidade_acumulada(
        curva_patrimonio_sample,
        curva_referencia=bench_df,
        nome_referencia="CDI",
    )
    assert len(fig.data) == 2
    assert fig.data[0].name == "Carteira"
    assert fig.data[1].name == "CDI"


def test_rentabilidade_com_benchmark_valor_referencia(curva_patrimonio_sample):
    bench_df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "valor_referencia": [100.0, 105.0, 110.0],
        }
    )
    fig = line_rentabilidade_acumulada(
        curva_patrimonio_sample,
        curva_referencia=bench_df,
        nome_referencia="IPCA",
    )
    assert len(fig.data) == 2
    y_bench = list(fig.data[1].y)
    assert y_bench[0] == pytest.approx(0.0)
    assert y_bench[1] == pytest.approx(5.0)
    assert y_bench[2] == pytest.approx(10.0)


def test_rentabilidade_dataframe_vazio_retorna_zero_traces():
    empty_df = pd.DataFrame(columns=["data", "patrimonio_liquido"])
    fig = line_rentabilidade_acumulada(empty_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_rentabilidade_none_retorna_zero_traces():
    fig = line_rentabilidade_acumulada(None)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_rentabilidade_um_unico_ponto_retorna_zero_pct():
    single_df = pd.DataFrame(
        {
            "data": [pd.Timestamp("2024-01-01")],
            "patrimonio_liquido": [15000.0],
        }
    )
    fig = line_rentabilidade_acumulada(single_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert list(fig.data[0].y) == [0.0]


def test_rentabilidade_altura_e_separadores(curva_patrimonio_sample):
    fig = line_rentabilidade_acumulada(curva_patrimonio_sample)
    assert fig.layout.height == HEIGHT_LINE
    assert fig.layout.separators == ",."


def test_rentabilidade_hover_contem_rentabilidade(curva_patrimonio_sample):
    fig = line_rentabilidade_acumulada(curva_patrimonio_sample)
    hover = fig.data[0].hovertemplate
    assert "Rentabilidade" in hover
