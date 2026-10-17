"""Aba Evolução & Aportes."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.charts import (
        line_comparativo_patrimonio_e_aportes,
        line_rentabilidade_acumulada,
    )
    from dashboard.state import DashboardState
except ImportError:  # pragma: no cover
    from charts import (
        line_comparativo_patrimonio_e_aportes,
        line_rentabilidade_acumulada,
    )
    from state import DashboardState

# Opções de produto disponíveis no seletor
_OPCOES_PRODUTO = [
    "Bolsa de Valores (Ações & BDR)",
    "Tesouro Direto",
    "Consolidado",
]

# Mapeamento opção → chave no state
_MAP_EVOL = {
    "Bolsa de Valores (Ações & BDR)": "bolsa",
    "Tesouro Direto": "tesouro",
    "Consolidado": "consolidado",
}

# Mapeamento chave → atributo do DashboardState
_MAP_STATE = {
    "bolsa": "evol_bolsa",
    "tesouro": "evol_tesouro",
    "consolidado": "evol_dict",
}


def render(state: DashboardState) -> None:
    """Renderiza a aba Evolução & Aportes."""
    st.markdown("### Curva Comparativa de Patrimônio e Aportes")

    produto_sel = st.radio(
        "Produto:",
        options=_OPCOES_PRODUTO,
        horizontal=True,
        key="radio_produto_evolucao",
    )

    chave = _MAP_EVOL[produto_sel]
    evol = getattr(state, _MAP_STATE[chave])

    st.plotly_chart(
        line_comparativo_patrimonio_e_aportes(
            evol["curva_aportes"],
            evol["curva_patrimonio"],
        ),
        width="stretch",
    )

    st.markdown("### Rentabilidade Acumulada da Carteira (%)")
    st.plotly_chart(
        line_rentabilidade_acumulada(evol["curva_patrimonio"]),
        width="stretch",
    )

    if not state.mov_filtered.empty:
        st.markdown("### Detalhamento das Movimentações")
        st.dataframe(state.mov_filtered, width="stretch")
