"""Aba Proventos & Renda."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.charts import bar_dy, bar_proventos
    from dashboard.state import DashboardState
except ImportError:  # pragma: no cover
    from charts import bar_dy, bar_proventos
    from state import DashboardState


def render(state: DashboardState) -> None:
    """Renderiza a aba Proventos & Renda."""
    if state.proventos.empty:
        st.info("Não há proventos registrados no período selecionado.")
    else:
        col_header, col_toggle1, col_toggle2 = st.columns([3, 1, 1])
        with col_header:
            st.markdown("### Histórico Mensal de Proventos")
        with col_toggle1:
            segmentar_por_tipo = st.toggle(
                "Por Tipo",
                value=False,
                key="proventos_segmentar_tipo",
            )
        with col_toggle2:
            mostrar_acumulado = st.toggle(
                "Acumulado Anual",
                value=True,
                key="proventos_mostrar_acumulado",
            )
        st.plotly_chart(
            bar_proventos(
                state.proventos,
                mostrar_acumulado=mostrar_acumulado,
                segmentar_por_tipo=segmentar_por_tipo,
            ),
            width="stretch",
        )

    st.markdown("### Métricas de Dividend Yield (LTM) & Yield on Cost")
    if state.dy_metrics.empty:
        st.info("Sem dados suficientes para cálculo de Dividend Yield.")
    else:
        st.plotly_chart(bar_dy(state.dy_metrics), width="stretch")
        st.dataframe(
            state.dy_metrics[
                ["ticker", "valor_atual", "custo_total", "proventos_12m", "dy_ltm_pct", "yield_on_cost_pct"]
            ],
            width="stretch",
        )

    st.markdown("### Calendário de Proventos Recebidos")
    cal = state.calendario_proventos
    if cal.empty:
        st.info("Nenhum evento de provento encontrado no período selecionado.")
    else:
        total = float(cal["valor_liquido"].sum()) if "valor_liquido" in cal.columns else 0.0
        st.caption(f"**Total no período:** R$ {total:,.2f} · **{len(cal)} pagamentos**")
        st.dataframe(
            cal,
            use_container_width=True,
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "ativo": st.column_config.TextColumn("Ativo"),
                "tipo_provento": st.column_config.TextColumn("Tipo"),
                "valor_liquido": st.column_config.NumberColumn(
                    "Valor Líquido (R$)",
                    format="R$ %.2f",
                ),
            },
            hide_index=True,
        )
