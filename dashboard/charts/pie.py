from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base import aplicar_layout_padrao
from .defaults import HEIGHT_PIE, HEIGHT_PIE_SMALL, PIE_COLOR_SEQUENCE

_HOVERTEMPLATE = (
    "<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>"
)


def agrupar_posicao_outros(
    df: pd.DataFrame,
    names_col: str = "produto",
    values_col: str = "valor_abs",
    limite_pct: float = 3.0,
    max_itens: int | None = None,
) -> pd.DataFrame:
    """Agrupa fatias menores que `limite_pct` (ou além de `max_itens`) em 'Outros'."""
    if df is None or getattr(df, "empty", True) or values_col not in df.columns or names_col not in df.columns:
        return df

    df_copia = df.copy()
    valores = pd.to_numeric(df_copia[values_col], errors="coerce").fillna(0.0)
    total = valores.sum()
    if total <= 0:
        return df

    df_copia[values_col] = valores
    df_copia = df_copia[df_copia[values_col] > 0]
    df_copia["_pct"] = (df_copia[values_col] / total) * 100.0
    df_copia = df_copia.sort_values(values_col, ascending=False).reset_index(drop=True)

    condicao_pequeno = df_copia["_pct"] < limite_pct
    if max_itens is not None and max_itens > 0 and len(df_copia) > max_itens:
        condicao_pequeno = condicao_pequeno | (df_copia.index >= max_itens)

    itens_pequenos = df_copia[condicao_pequeno]
    if len(itens_pequenos) > 1:
        principais = df_copia[~condicao_pequeno].copy()
        soma_outros = round(float(itens_pequenos[values_col].sum()), 2)
        qtd_outros = len(itens_pequenos)

        linha_outros = {
            names_col: f"Outros ({qtd_outros} ativos)",
            values_col: soma_outros,
        }
        for col in df_copia.columns:
            if col not in linha_outros and col != "_pct":
                linha_outros[col] = "Outros"

        df_agrupado = pd.concat([principais, pd.DataFrame([linha_outros])], ignore_index=True)
        return df_agrupado.drop(columns=["_pct"], errors="ignore")

    return df_copia.drop(columns=["_pct"], errors="ignore")


def _criar_donut(
    df,
    names_col: str,
    values_col: str,
    titulo: str,
    height: int,
    mostrar_total_centro: bool = True,
) -> go.Figure:
    """Fábrica interna: cria um gráfico donut padronizado.

    Centraliza px.pie + update_traces + aplicar_layout_padrao para que
    qualquer ajuste visual (hole, hover, textinfo, cores) seja feito em
    um único lugar.
    """
    if df is None or getattr(df, "empty", True):
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=height)

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
        textinfo="percent",
        insidetextorientation="horizontal",
        hovertemplate=_HOVERTEMPLATE,
    )

    # Aplica layout padrão com separadores pt-BR e tipografia
    aplicar_layout_padrao(fig, altura=height, legenda_horizontal=False)

    # Legenda vertical lateral direita organizada para nunca sobrepor o gráfico
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        margin=dict(l=20, r=20, t=55, b=25),
    )

    if mostrar_total_centro and values_col in df.columns:
        total = df[values_col].sum()
        if total > 0:
            fig.add_annotation(
                text=f"<span style='font-size:11px;color:#64748b'>Total</span><br><b style='font-size:13px;color:#1e293b'>R$ {total:,.2f}</b>",
                showarrow=False,
                x=0.5,
                y=0.5,
                align="center",
            )

    return fig


def pie_carteira(pos, limite_outros_pct: float = 0.0) -> go.Figure:
    df = (
        agrupar_posicao_outros(pos, "produto", "valor_abs", limite_pct=limite_outros_pct)
        if limite_outros_pct > 0
        else pos
    )
    return _criar_donut(df, "produto", "valor_abs", "Distribuição da Carteira por Ativo", HEIGHT_PIE)


def pie_carteira_por_categoria(pos_categoria) -> go.Figure:
    return _criar_donut(pos_categoria, "categoria", "valor", "Alocação por Classe de Ativos", HEIGHT_PIE)


def pie_categoria(pos, titulo: str = "Distribuição por Ativo") -> go.Figure:
    return _criar_donut(pos, "produto", "valor_abs", titulo, HEIGHT_PIE_SMALL)

