"""Aba Carteira & Alocação."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.charts import (
        bar_distribuicao_ativos,
        bar_lucro_prejuizo,
        pie_carteira,
        pie_carteira_por_categoria,
        pie_macro_alocacao,
        sunburst_carteira,
        treemap_carteira,
    )
    from dashboard.models.categorias import CATEGORIA_TESOURO, CATEGORIAS_BOLSA
    from dashboard.state import DashboardState
    from dashboard.views._helpers import render_cards_grid, render_section
except ImportError:  # pragma: no cover
    from charts import (
        bar_distribuicao_ativos,
        bar_lucro_prejuizo,
        pie_carteira,
        pie_carteira_por_categoria,
        pie_macro_alocacao,
        sunburst_carteira,
        treemap_carteira,
    )
    from models.categorias import CATEGORIA_TESOURO, CATEGORIAS_BOLSA
    from state import DashboardState
    from views._helpers import render_cards_grid, render_section



def _render_cards_macro(res) -> None:
    """Renderiza os cards de métricas macro (Bolsa de Valores e Tesouro Direto)."""
    col_b, col_t = st.columns(2)
    with col_b:
        delta_b = f"{res.bolsa.pl:+,.2f} ({res.bolsa.pl_pct:+.2f}%)" if res.bolsa.custo > 0 else None
        st.metric(
            "Bolsa de Valores (Ações & BDR)",
            f"R$ {res.bolsa.patrimonio:,.2f}",
            delta=delta_b,
        )
        st.caption(f"**Peso:** {res.bolsa.peso_pct:.1f}% &nbsp;|&nbsp; **Custo:** R$ {res.bolsa.custo:,.2f}")

    with col_t:
        delta_t = f"{res.tesouro.pl:+,.2f} ({res.tesouro.pl_pct:+.2f}%)" if res.tesouro.custo > 0 else None
        st.metric(
            "Tesouro Direto (Renda Fixa)",
            f"R$ {res.tesouro.patrimonio:,.2f}",
            delta=delta_t,
        )
        st.caption(f"**Peso:** {res.tesouro.peso_pct:.1f}% &nbsp;|&nbsp; **Custo:** R$ {res.tesouro.custo:,.2f}")

    if res.patrimonio_total > 0:
        st.caption(
            f"**Patrimônio Consolidado:** R$ {res.patrimonio_total:,.2f} &nbsp;|&nbsp; "
            f"**Lucro/Prejuízo Total:** {res.pl_total:+,.2f} ({res.pl_pct:+.2f}%)"
        )


def _render_alocacao_macro(state: DashboardState) -> bool:
    """Exibe cards de alocação macro (Bolsa vs Tesouro), donut alinhado e raio-X detalhado sob demanda."""
    st.markdown("### Alocação Macro & Risco")
    res = state.resumo

    col_cards, col_donut = st.columns([3, 2])
    with col_cards:
        _render_cards_macro(res)

    with col_donut:
        if res.patrimonio_total > 0:
            st.plotly_chart(pie_macro_alocacao(res), width="stretch")

    # Distribuição calculada dinamicamente pelas 5 Classes de Ativos
    if hasattr(state, "pos_5_classes") and not state.pos_5_classes.empty:
        st.markdown("### Alocação por Classe de Ativos")
        cols = st.columns(len(state.pos_5_classes))
        for i, (_, row) in enumerate(state.pos_5_classes.iterrows()):
            with cols[i]:
                st.metric(
                    label=row["classe"],
                    value=f"{row['peso_pct']:.1f}%",
                    delta=f"R$ {row['valor']:,.2f}",
                    delta_color="off",
                )

    # Raio-X detalhado sob demanda (expander)
    separar = False
    with st.expander("Explorar Raio-X Detalhado (Treemap, Sunburst, Donut ou Barras)", expanded=False):
        col_view, col_toggle = st.columns([3, 2])
        with col_view:
            tipo_grafico = st.radio(
                "Visualização da Distribuição:",
                options=[
                    "Gráficos de Pizza / Donut",
                    "Ranking em Barras (Ativos)",
                    "Mapa de Árvore (Treemap)",
                    "Gráfico de Hierarquia (Sunburst)",
                ],
                horizontal=True,
                key="radio_tipo_grafico_carteira",
            )
        with col_toggle:
            modo_hierarquia = st.selectbox(
                "Agrupamento de Classes:",
                options=[
                    "5 Classes de Ativos",
                    "Ações, BDR e Tesouro",
                    "Bolsa de Valores vs Tesouro Direto",
                ],
                index=0,
                key="select_modo_hierarquia_carteira",
            )
            modo_5 = (modo_hierarquia == "5 Classes de Ativos")
            separar = (modo_hierarquia != "Bolsa de Valores vs Tesouro Direto")

        if tipo_grafico == "Mapa de Árvore (Treemap)":
            st.plotly_chart(
                treemap_carteira(state.pos, separar_bdr_acoes=separar, modo_5_classes=modo_5),
                width="stretch",
            )
        elif tipo_grafico == "Gráfico de Hierarquia (Sunburst)":
            st.plotly_chart(
                sunburst_carteira(state.pos, separar_bdr_acoes=separar, modo_5_classes=modo_5),
                width="stretch",
            )
        elif tipo_grafico == "Ranking em Barras (Ativos)":
            st.plotly_chart(
                bar_distribuicao_ativos(state.pos),
                width="stretch",
            )
        else:
            col_opt1, _ = st.columns([1, 1])
            with col_opt1:
                agrupar_outros = st.toggle(
                    "Agrupar fatias menores (< 3%) em 'Outros'",
                    value=True,
                    help="Agrupa ativos com menos de 3% da carteira em uma única fatia para manter o donut legível e desobstruído.",
                    key="toggle_agrupar_outros_pie",
                )
            limite = 3.0 if agrupar_outros else 0.0

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(pie_carteira(state.pos, limite_outros_pct=limite), width="stretch")
            with col2:
                if modo_5 and hasattr(state, "pos_5_classes") and not state.pos_5_classes.empty:
                    pos_categoria_exibida = state.pos_5_classes
                else:
                    pos_categoria_exibida = (
                        state.pos_categoria if separar else state.pos_categoria_agrupada
                    )
                st.plotly_chart(
                    pie_carteira_por_categoria(pos_categoria_exibida),
                    width="stretch",
                )

    return separar


def _render_resultado_pl(state: DashboardState) -> None:
    """Exibe o gráfico de Lucro e Prejuízo por Ativo (Issue 4.1)."""
    if not state.pos_cards.empty and (state.pos_cards["custo_total"] > 0).any():
        st.markdown("### Resultado por Ativo (P&L)")
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
        st.info("Exibindo **Custo histórico**: Nenhum arquivo de posição carregado. Os valores correspondem ao custo acumulado de aquisição.")


def render(state: DashboardState) -> None:
    """Renderiza a aba Carteira & Alocação."""
    if state.pos.empty:
        st.info("Nenhum ativo encontrado para os filtros selecionados.")
        return

    separar = _render_alocacao_macro(state)
    _render_resultado_pl(state)
    _render_cards_custodia(state, separar)

