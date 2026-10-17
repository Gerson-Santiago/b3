from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base import aplicar_layout_padrao
from .defaults import (
    COLOR_CUSTO,
    COLOR_PATRIMONIO,
    COLOR_PATRIMONIO_MARKER,
    HEIGHT_LINE,
    HEIGHT_LINE_COMPARATIVO,
)


def line_evolucao(evol):
    fig = px.line(
        evol,
        x="data",
        y="patrimonio",
        title="Evolução Temporal do Portfólio",
        labels={"data": "Data", "patrimonio": "Valor (R$)"},
        markers=True,
    )
    fig.update_traces(
        hovertemplate="<b>Data:</b> %{x|%d/%m/%Y}<br><b>Patrimônio:</b> R$ %{y:,.2f}<extra></extra>"
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_LINE, legenda_horizontal=False)


def line_comparativo_patrimonio_e_aportes(curva_aportes, curva_patrimonio):
    fig = go.Figure()

    if curva_aportes is not None and not curva_aportes.empty:
        fig.add_trace(
            go.Scatter(
                x=curva_aportes["data"],
                y=curva_aportes["custo_acumulado"],
                mode="lines",
                name="Custo Acumulado (Aportes)",
                line=dict(color=COLOR_CUSTO, width=2, dash="dash"),
                hovertemplate="<b>Aportes Acumulados:</b> R$ %{y:,.2f}<extra></extra>",
            )
        )

    if curva_patrimonio is not None and not curva_patrimonio.empty:
        fig.add_trace(
            go.Scatter(
                x=curva_patrimonio["data"],
                y=curva_patrimonio["patrimonio_liquido"],
                mode="lines+markers",
                name="Patrimônio Consolidado (Snapshots B3)",
                line=dict(color=COLOR_PATRIMONIO, width=3),
                marker=dict(size=8, color=COLOR_PATRIMONIO_MARKER),
                hovertemplate="<b>Patrimônio Real:</b> R$ %{y:,.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Patrimônio Consolidado vs Custo Acumulado de Aportes",
        xaxis_title="Data de Referência",
        yaxis_title="Montante (R$)",
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_LINE_COMPARATIVO, legenda_horizontal=True)


def line_rentabilidade_acumulada(
    curva_patrimonio: pd.DataFrame | None,
    curva_referencia: pd.DataFrame | None = None,
    nome_referencia: str = "Benchmark",
) -> go.Figure:
    """Gera gráfico de rentabilidade percentual acumulada (%) no tempo.

    Calcula retorno_pct a partir de ((patrimonio / p0) - 1) * 100.
    Permite opcionalmente comparar com uma curva de benchmark.
    """
    fig = go.Figure()

    if curva_patrimonio is not None and not curva_patrimonio.empty and "data" in curva_patrimonio.columns:
        df = curva_patrimonio.sort_values("data").reset_index(drop=True)
        col_val = (
            "patrimonio_liquido"
            if "patrimonio_liquido" in df.columns
            else ("patrimonio" if "patrimonio" in df.columns else None)
        )
        if col_val:
            valores = pd.to_numeric(df[col_val], errors="coerce").fillna(0.0)
            if len(valores) > 0:
                p0 = float(valores.iloc[0])
                if p0 == 0.0:
                    pos = valores[valores > 0]
                    p0 = float(pos.iloc[0]) if not pos.empty else 1.0
                retorno_pct = ((valores / p0) - 1.0) * 100.0

                fig.add_trace(
                    go.Scatter(
                        x=df["data"],
                        y=retorno_pct,
                        mode="lines+markers",
                        name="Carteira",
                        line=dict(color=COLOR_PATRIMONIO, width=3),
                        marker=dict(size=7, color=COLOR_PATRIMONIO_MARKER),
                        hovertemplate="<b>Data:</b> %{x|%d/%m/%Y}<br><b>Rentabilidade:</b> %{y:+.2f}%<extra></extra>",
                    )
                )

    if curva_referencia is not None and not curva_referencia.empty and "data" in curva_referencia.columns:
        df_ref = curva_referencia.sort_values("data").reset_index(drop=True)
        ref_retorno = None
        if "retorno_pct" in df_ref.columns:
            ref_retorno = pd.to_numeric(df_ref["retorno_pct"], errors="coerce").fillna(0.0)
        elif "valor_referencia" in df_ref.columns:
            vals = pd.to_numeric(df_ref["valor_referencia"], errors="coerce").fillna(0.0)
            if len(vals) > 0:
                v0 = float(vals.iloc[0])
                if v0 == 0.0:
                    pos = vals[vals > 0]
                    v0 = float(pos.iloc[0]) if not pos.empty else 1.0
                ref_retorno = ((vals / v0) - 1.0) * 100.0

        if ref_retorno is not None:
            fig.add_trace(
                go.Scatter(
                    x=df_ref["data"],
                    y=ref_retorno,
                    mode="lines",
                    name=nome_referencia,
                    line=dict(color=COLOR_CUSTO, width=2, dash="dash"),
                    hovertemplate=f"<b>{nome_referencia}:</b> %{{y:+.2f}}%<extra></extra>",
                )
            )

    fig.add_hline(y=0, line_dash="dot", line_color="#94a3b8", line_width=1)

    fig.update_layout(
        title="Rentabilidade Acumulada da Carteira (%)",
        xaxis_title="Data de Referência",
        yaxis_title="Rentabilidade Acumulada (%)",
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_LINE, legenda_horizontal=True)
