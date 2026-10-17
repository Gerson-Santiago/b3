from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base import aplicar_layout_padrao
from .defaults import HEIGHT_TREEMAP, PIE_COLOR_SEQUENCE


def _preparar_dados_hierarquia(pos: pd.DataFrame, separar_bdr_acoes: bool) -> pd.DataFrame:
    df = pos.copy()
    if "categoria" not in df.columns:
        df["categoria"] = "Ativos"

    if not separar_bdr_acoes:
        df["categoria_hierarquia"] = df["categoria"].replace(
            {"AÇÕES": "Bolsa de Valores", "BDR": "Bolsa de Valores", "TESOURO": "Tesouro Direto"}
        )
    else:
        df["categoria_hierarquia"] = df["categoria"]

    return df


def treemap_carteira(
    pos: pd.DataFrame,
    *,
    titulo: str = "Distribuição da Carteira | Mapa de Árvore",
    separar_bdr_acoes: bool = False,
) -> go.Figure:
    """Gera gráfico Mapa de Árvore (Treemap) com a hierarquia de ativos da carteira."""
    if pos is None or pos.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_TREEMAP)

    df = _preparar_dados_hierarquia(pos, separar_bdr_acoes)

    fig = px.treemap(
        df,
        path=["categoria_hierarquia", "produto"],
        values="valor_abs",
        title=titulo,
        color="categoria_hierarquia",
        color_discrete_sequence=PIE_COLOR_SEQUENCE,
    )
    fig.update_traces(
        textinfo="label+value+percent parent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Valor: R$ %{value:,.2f}<br>"
            "Participação no grupo: %{percentParent:.1%}<br>"
            "Participação na carteira: %{percentRoot:.1%}"
            "<extra></extra>"
        ),
    )
    fig.update_layout(showlegend=False)
    return aplicar_layout_padrao(fig, altura=HEIGHT_TREEMAP, legenda_horizontal=False)


def sunburst_carteira(
    pos: pd.DataFrame,
    *,
    titulo: str = "Distribuição da Carteira | Gráfico de Hierarquia",
    separar_bdr_acoes: bool = False,
) -> go.Figure:
    """Gera gráfico de Hierarquia circular (Sunburst) com os ativos da carteira."""
    if pos is None or pos.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_TREEMAP)

    df = _preparar_dados_hierarquia(pos, separar_bdr_acoes)

    fig = px.sunburst(
        df,
        path=["categoria_hierarquia", "produto"],
        values="valor_abs",
        title=titulo,
        color="categoria_hierarquia",
        color_discrete_sequence=PIE_COLOR_SEQUENCE,
    )
    fig.update_traces(
        textinfo="label+percent parent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Valor: R$ %{value:,.2f}<br>"
            "Participação no grupo: %{percentParent:.1%}<br>"
            "Participação na carteira: %{percentRoot:.1%}"
            "<extra></extra>"
        ),
    )
    fig.update_layout(showlegend=False)
    return aplicar_layout_padrao(fig, altura=HEIGHT_TREEMAP, legenda_horizontal=False)
