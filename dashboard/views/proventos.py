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
        col_header, col_toggle = st.columns([3, 1])
        with col_header:
            st.markdown("### Histórico Mensal de Proventos")
        with col_toggle:
            mostrar_acumulado = st.toggle(
                "Acumulado Anual",
                value=True,
                key="proventos_mostrar_acumulado",
            )
        st.plotly_chart(
            bar_proventos(state.proventos, mostrar_acumulado=mostrar_acumulado),
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
