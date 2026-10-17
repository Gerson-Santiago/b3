"""Aba 📈 Evolução & Aportes."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.charts import line_comparativo_patrimonio_e_aportes
    from dashboard.state import DashboardState
except ImportError:  # pragma: no cover
    from charts import line_comparativo_patrimonio_e_aportes
    from state import DashboardState


def render(state: DashboardState) -> None:
    """Renderiza a aba Evolução & Aportes."""
    st.markdown("### Curva Comparativa de Patrimônio e Aportes")
    st.plotly_chart(
        line_comparativo_patrimonio_e_aportes(
            state.evol_dict["curva_aportes"],
            state.evol_dict["curva_patrimonio"],
        ),
        width="stretch",
    )
    if not state.mov_filtered.empty:
        st.markdown("### Detalhamento das Movimentações")
        st.dataframe(state.mov_filtered, width="stretch")
