"""Aba Carteira & Alocação."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.charts import (
        bar_lucro_prejuizo,
        pie_carteira,
        pie_carteira_por_categoria,
        sunburst_carteira,
        treemap_carteira,
    )
    from dashboard.models.categorias import CATEGORIA_TESOURO, CATEGORIAS_BOLSA
    from dashboard.state import DashboardState
    from dashboard.views._helpers import render_cards_grid, render_section
except ImportError:  # pragma: no cover
    from charts import (
        bar_lucro_prejuizo,
        pie_carteira,
        pie_carteira_por_categoria,
        sunburst_carteira,
        treemap_carteira,
    )
    from models.categorias import CATEGORIA_TESOURO, CATEGORIAS_BOLSA
    from state import DashboardState
    from views._helpers import render_cards_grid, render_section


def _render_alocacao_macro(state: DashboardState) -> bool:
    """Exibe cards de alocação macro (Bolsa vs Tesouro) e raio-X detalhado sob demanda."""
    st.markdown("### 02. Alocação Macro & Risco")
    res = state.resumo

    col_b, col_t = st.columns(2)
    with col_b:
        delta_b = f"{res.bolsa.pl:+,.2f} ({res.bolsa.pl_pct:+.2f}%)" if res.bolsa.custo > 0 else None
        st.metric(
            "🏛️ Bolsa de Valores (Ações & BDR)",
            f"R$ {res.bolsa.patrimonio:,.2f}",
            delta=delta_b,
        )
        st.caption(f"**Peso:** {res.bolsa.peso_pct:.1f}% da carteira &nbsp;|&nbsp; **Custo:** R$ {res.bolsa.custo:,.2f}")

    with col_t:
        delta_t = f"{res.tesouro.pl:+,.2f} ({res.tesouro.pl_pct:+.2f}%)" if res.tesouro.custo > 0 else None
        st.metric(
            "🏦 Tesouro Direto (Renda Fixa)",
            f"R$ {res.tesouro.patrimonio:,.2f}",
            delta=delta_t,
        )
        st.caption(f"**Peso:** {res.tesouro.peso_pct:.1f}% da carteira &nbsp;|&nbsp; **Custo:** R$ {res.tesouro.custo:,.2f}")

    # Barra proporcional de alocação macro
    if res.patrimonio_total > 0:
        progresso_bolsa = min(max(res.bolsa.peso_pct / 100.0, 0.0), 1.0)
        st.progress(
            progresso_bolsa,
            text=f"Proporção da Carteira: {res.bolsa.peso_pct:.1f}% Bolsa de Valores | {res.tesouro.peso_pct:.1f}% Tesouro Direto",
        )

    # Raio-X detalhado sob demanda (expander)
    separar = False
    with st.expander("🔍 Explorar Raio-X Detalhado (Treemap, Sunburst ou Pizza)", expanded=False):
        col_view, col_toggle = st.columns([3, 2])
        with col_view:
            tipo_grafico = st.radio(
                "Visualização da Distribuição:",
                options=[
                    "Mapa de Árvore (Treemap)",
                    "Gráfico de Hierarquia (Sunburst)",
                    "Gráficos de Pizza",
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

        if tipo_grafico == "Mapa de Árvore (Treemap)":
            st.plotly_chart(
                treemap_carteira(state.pos, separar_bdr_acoes=separar),
                width="stretch",
            )
        elif tipo_grafico == "Gráfico de Hierarquia (Sunburst)":
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

    return separar


def _render_resultado_pl(state: DashboardState) -> None:
    """Exibe o gráfico de Lucro e Prejuízo por Ativo (Issue 4.1)."""
    if not state.pos_cards.empty and (state.pos_cards["custo_total"] > 0).any():
        st.markdown("### 03. Resultado por Ativo (P&L)")
        st.plotly_chart(bar_lucro_prejuizo(state.pos_cards), width="stretch")


def _render_cards_custodia(state: DashboardState, separar: bool) -> None:
    """Exibe a grade de cards detalhados por ativo."""
    st.markdown("### Posição Detalhada em Custódia")

    is_fallback = state.pos_filtered.empty
    rotulo_valor = "Custo histórico" if is_fallback else "Valor Atual (snapshot)"

    cat_upper = state.pos_cards["categoria"].astype(str).str.upper()
    cards_acoes = state.pos_cards[cat_upper.isin(["AÇÕES", "ACOES", "AÇÃO"])].sort_values("valor_abs", ascending=False)
    cards_bdr = state.pos_cards[cat_upper.isin(["BDR", "BDRS"])].sort_values("valor_abs", ascending=False)
    cards_tesouro = state.pos_cards[cat_upper == CATEGORIA_TESOURO].sort_values("valor_abs", ascending=False)

    render_cards_grid(cards_acoes, "Ações", "Nenhum ativo de Ações em custódia.", rotulo_valor=rotulo_valor)
    render_cards_grid(cards_bdr, "BDR", "Nenhum BDR em custódia.", rotulo_valor=rotulo_valor)
    render_cards_grid(cards_tesouro, "Tesouro Direto", "Nenhum ativo de Tesouro Direto em custódia.", rotulo_valor=rotulo_valor)

    if not is_fallback:
        st.caption("Dados baseados no snapshot de custódia mais recente da B3.")
    else:
        st.info("ℹ️ Exibindo **Custo histórico**: Nenhum arquivo de posição carregado. Os valores correspondem ao custo acumulado de aquisição.")


def render(state: DashboardState) -> None:
    """Renderiza a aba Carteira & Alocação."""
    if state.pos.empty:
        st.info("Nenhum ativo encontrado para os filtros selecionados.")
        return

    separar = _render_alocacao_macro(state)
    _render_resultado_pl(state)
    _render_cards_custodia(state, separar)

