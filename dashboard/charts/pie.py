from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

from .base import aplicar_layout_padrao
from .defaults import HEIGHT_PIE, HEIGHT_PIE_SMALL, PIE_COLOR_SEQUENCE

_HOVERTEMPLATE = (
    "<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>"
)


def _criar_donut(
    df,
    names_col: str,
    values_col: str,
    titulo: str,
    height: int,
) -> go.Figure:
    """Fábrica interna: cria um gráfico donut padronizado.

    Centraliza px.pie + update_traces + aplicar_layout_padrao para que
    qualquer ajuste visual (hole, hover, textinfo, cores) seja feito em
    um único lugar.
    """
    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=titulo,
        hole=0.45,
        color_discrete_sequence=PIE_COLOR_SEQUENCE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate=_HOVERTEMPLATE,
    )
    return aplicar_layout_padrao(fig, altura=height)


def pie_carteira(pos) -> go.Figure:
    return _criar_donut(pos, "produto", "valor_abs", "Distribuição da Carteira por Ativo", HEIGHT_PIE)


def pie_carteira_por_categoria(pos_categoria) -> go.Figure:
    return _criar_donut(pos_categoria, "categoria", "valor", "Alocação por Classe de Ativos", HEIGHT_PIE)


def pie_categoria(pos, titulo: str = "Distribuição por Ativo") -> go.Figure:
    return _criar_donut(pos, "produto", "valor_abs", titulo, HEIGHT_PIE_SMALL)
