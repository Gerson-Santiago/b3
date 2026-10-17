from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base import aplicar_layout_padrao
from .defaults import (
    COLOR_DY,
    COLOR_LUCRO,
    COLOR_PATRIMONIO,
    COLOR_PREJUIZO,
    COLOR_PROVENTOS,
    HEIGHT_BAR,
)


def bar_proventos(
    proventos: pd.DataFrame | None,
    mostrar_acumulado: bool = True,
) -> go.Figure:
    if proventos is None or proventos.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text="Histórico Mensal de Proventos Recebidos"))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    df = proventos.copy()
    if "valor_liquido" in df.columns:
        df["valor_liquido"] = df["valor_liquido"].fillna(0.0)

    # Ordenação cronológica e cálculo do acumulado por ano
    if "mes" in df.columns:
        mes_dt = pd.to_datetime(df["mes"])
        df["_dt"] = mes_dt
        df = df.sort_values("_dt").reset_index(drop=True)
        ano = df["_dt"].dt.year
        df["acumulado_ano"] = df.groupby(ano)["valor_liquido"].cumsum()
    else:
        df["acumulado_ano"] = df["valor_liquido"].cumsum() if "valor_liquido" in df.columns else 0.0

    fig = px.bar(
        df,
        x="mes",
        y="valor_liquido",
        title="Histórico Mensal de Proventos Recebidos",
        labels={"mes": "Mês de Pagamento", "valor_liquido": "Proventos Líquidos (R$)"},
        color_discrete_sequence=[COLOR_PROVENTOS],
    )
    fig.update_traces(
        name="Mensal",
        hovertemplate="<b>Mês:</b> %{x}<br><b>Recebido:</b> R$ %{y:,.2f}<extra></extra>",
    )

    if mostrar_acumulado:
        fig.data[0].showlegend = True
        fig.add_trace(
            go.Scatter(
                x=df["mes"],
                y=df["acumulado_ano"],
                mode="lines+markers",
                name="Acumulado no Ano",
                line=dict(color=COLOR_PATRIMONIO, width=2.5),
                marker=dict(size=6, color=COLOR_PATRIMONIO),
                yaxis="y2",
                hovertemplate="<b>Mês:</b> %{x}<br><b>Acumulado no Ano:</b> R$ %{y:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title="Acumulado no Ano (R$)",
                overlaying="y",
                side="right",
                showgrid=False,
            )
        )
        return aplicar_layout_padrao(
            fig,
            altura=HEIGHT_BAR,
            legenda_horizontal=True,
            margens=dict(l=30, r=50, t=60, b=40),
        )

    return aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)


def bar_dy(dy: pd.DataFrame | None) -> go.Figure:
    if dy is None or dy.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text="Dividend Yield LTM por Ativo (%)"))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    y_col = "dy_ltm_pct" if "dy_ltm_pct" in dy.columns else "dy_pct"
    fig = px.bar(
        dy,
        x="produto",
        y=y_col,
        title="Dividend Yield LTM por Ativo (%)",
        labels={"produto": "Ativo", y_col: "Dividend Yield (%)"},
        color_discrete_sequence=[COLOR_DY],
    )
    fig.update_traces(
        hovertemplate="<b>Ativo:</b> %{x}<br><b>DY LTM:</b> %{y:.2f}%<extra></extra>"
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)


def bar_lucro_prejuizo(
    pos_cards: pd.DataFrame | None,
    *,
    titulo: str = "Resultado por Ativo (P&L em R$)",
) -> go.Figure:
    """Gera gráfico de barras horizontais com Lucro e Prejuízo por ativo."""
    if pos_cards is None or pos_cards.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    df = pos_cards.copy()
    if "custo_total" in df.columns:
        df = df[df["custo_total"] > 0].copy()

    if df.empty or "pl" not in df.columns or "produto" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    # Ordena por pl crescente para que o maior lucro fique no topo do eixo Y
    df = df.sort_values("pl", ascending=True).copy()

    if "variacao_pct" not in df.columns:
        df["variacao_pct"] = 0.0

    df["status"] = df["pl"].apply(lambda v: "Lucro" if v >= 0 else "Prejuízo")

    fig = px.bar(
        df,
        x="pl",
        y="produto",
        orientation="h",
        color="status",
        color_discrete_map={"Lucro": COLOR_LUCRO, "Prejuízo": COLOR_PREJUIZO},
        title=titulo,
        labels={"pl": "Lucro / Prejuízo (R$)", "produto": "Ativo", "status": "Resultado"},
        custom_data=["variacao_pct"],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>Ativo:</b> %{y}<br>"
            "<b>P&L:</b> R$ %{x:,.2f}<br>"
            "<b>Variação:</b> %{customdata[0]:+.2f}%"
            "<extra></extra>"
        )
    )
    fig.update_layout(showlegend=False)
    return aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)

