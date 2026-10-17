import plotly.express as px

from .base import aplicar_layout_padrao
from .defaults import HEIGHT_PIE, HEIGHT_PIE_SMALL, PIE_COLOR_SEQUENCE


def pie_carteira(pos):
    fig = px.pie(
        pos,
        names="produto",
        values="valor_abs",
        title="Distribuição da Carteira por Ativo",
        hole=0.45,
        color_discrete_sequence=PIE_COLOR_SEQUENCE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>",
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_PIE)


def pie_carteira_por_categoria(pos_categoria):
    fig = px.pie(
        pos_categoria,
        names="categoria",
        values="valor",
        title="Alocação por Classe de Ativos",
        hole=0.45,
        color_discrete_sequence=PIE_COLOR_SEQUENCE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>",
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_PIE)


def pie_categoria(pos, titulo: str = "Distribuição por Ativo"):
    fig = px.pie(
        pos,
        names="produto",
        values="valor_abs",
        title=titulo,
        hole=0.45,
        color_discrete_sequence=PIE_COLOR_SEQUENCE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>",
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_PIE_SMALL)
