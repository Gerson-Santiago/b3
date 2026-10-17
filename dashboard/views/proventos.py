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
        st.plotly_chart(bar_proventos(state.proventos), width="stretch")

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
