"""Aba Reconciliação B3."""
from __future__ import annotations

import streamlit as st

try:
    from dashboard.metrics.reconciliacao import comparar, quantidade_ate
    from dashboard.state import DashboardState
except ImportError:  # pragma: no cover
    from metrics.reconciliacao import comparar, quantidade_ate
    from state import DashboardState


def render(state: DashboardState, pos_df_full, end_date) -> None:
    """Renderiza a aba Reconciliação B3.

    Parameters
    ----------
    state:
        Estado calculado do dashboard.
    pos_df_full:
        Snapshot de posição sem filtros (necessário para comparação completa).
    end_date:
        Data de corte para cálculo da quantidade acumulada de movimentações.
    """
    st.markdown("### Auditoria de Reconciliação (Movimentações vs Posição)")

    mov_full = state.mov_filtered  # movimentações completas (pré-filtro de data já aplicado)
    if mov_full.empty or pos_df_full.empty:
        st.info("Carregue tanto a movimentação quanto a posição para conferência de reconciliação.")
        return

    qtd_calculada = quantidade_ate(mov_full, end_date)
    tabela = comparar(qtd_calculada, pos_df_full, mov_df=mov_full, data_corte=end_date)
    st.dataframe(tabela, width="stretch")

    divergentes = tabela[tabela["delta"].abs() > 1e-4]
    if divergentes.empty:
        st.success("Todos os ativos auditados estão 100% conciliados com o extrato da B3.")
    else:
        st.warning(f"{len(divergentes)} ativo(s) com divergência entre movimentações e posição.")
