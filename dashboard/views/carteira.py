"""Aba 📊 Carteira & Alocação."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.charts import (
        pie_carteira,
        pie_carteira_por_categoria,
        sunburst_carteira,
        treemap_carteira,
    )
    from dashboard.state import DashboardState
    from dashboard.views._helpers import render_section
except ImportError:  # pragma: no cover
    from charts import (
        pie_carteira,
        pie_carteira_por_categoria,
        sunburst_carteira,
        treemap_carteira,
    )
    from state import DashboardState
    from views._helpers import render_section


def render(state: DashboardState) -> None:
    """Renderiza a aba Carteira & Alocação."""
    if state.pos.empty:
        st.info("Nenhum ativo encontrado para os filtros selecionados.")
        return

    col_view, col_toggle = st.columns([3, 2])
    with col_view:
        tipo_grafico = st.radio(
            "Visualização da Distribuição:",
            options=[
                "🌳 Mapa de Árvore (Treemap)",
                "☀️ Gráfico de Hierarquia (Sunburst)",
                "🥧 Gráficos de Pizza",
            ],
            horizontal=True,
            key="radio_tipo_grafico_carteira",
        )
    with col_toggle:
        separar = st.toggle(
            "Separar BDR e Ações no gráfico de alocação",
            value=False,
            key="toggle_separar_bdr_acoes",
        )

    pos_categoria_exibida = (
        state.pos_categoria if separar else state.pos_categoria_agrupada
    )

    if tipo_grafico == "🌳 Mapa de Árvore (Treemap)":
        st.plotly_chart(
            treemap_carteira(state.pos, separar_bdr_acoes=separar),
            width="stretch",
        )
    elif tipo_grafico == "☀️ Gráfico de Hierarquia (Sunburst)":
        st.plotly_chart(
            sunburst_carteira(state.pos, separar_bdr_acoes=separar),
            width="stretch",
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(pie_carteira(state.pos), width="stretch")
        with col2:
            st.plotly_chart(
                pie_carteira_por_categoria(pos_categoria_exibida),
                width="stretch",
            )

    st.markdown("### Posição Detalhada em Custódia")

    pos_acoes_bdr = state.pos[state.pos["categoria"].isin(["AÇÕES", "BDR"])].sort_values("produto")
    pos_tesouro = state.pos[state.pos["categoria"] == "TESOURO"].sort_values("produto")

    if separar:
        pos_acoes = state.pos[state.pos["categoria"] == "AÇÕES"].sort_values("produto")
        pos_bdr = state.pos[state.pos["categoria"] == "BDR"].sort_values("produto")
        render_section(pos_acoes, "📈 Ações", "Nenhum ativo de Ações em custódia.")
        render_section(pos_bdr, "🌎 BDR", "Nenhum BDR em custódia.")
    else:
        render_section(pos_acoes_bdr, "📈 Bolsa de Valores (Ações & BDR)", "Nenhum ativo de Ações ou BDR em custódia.")

    render_section(pos_tesouro, "🏦 Tesouro Direto", "Nenhum ativo de Tesouro Direto em custódia.")

    if not state.pos_filtered.empty:
        st.caption("ℹ️ Dados baseados no snapshot de custódia mais recente da B3.")
