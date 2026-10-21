"""Aba Reconciliação B3."""
from __future__ import annotations

import pandas as pd
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
    st.dataframe(tabela, use_container_width=True)

    try:
        from dashboard.models.qualidade import mensagens
    except ImportError:
        from models.qualidade import mensagens

    for msg in mensagens(state.qualidade):
        st.warning(msg)

    divergentes = tabela[tabela["delta"].abs() > 1e-4]
    if divergentes.empty:
        st.success("Todos os ativos auditados estão 100% conciliados com o extrato da B3.")
    else:
        st.warning(f"{len(divergentes)} ativo(s) com divergência entre movimentações e posição.")

    _render_reconciliacao_proventos(state)


def _render_reconciliacao_proventos(state: DashboardState) -> None:
    """Renderiza a seção de auditoria de proventos recebidos."""
    st.markdown("### Reconciliação de Proventos (Movimentação vs Extrato de Proventos)")
    prov_rec = getattr(state, "reconciliacao_proventos", None)

    if not isinstance(prov_rec, pd.DataFrame) or prov_rec.empty:
        st.info("Nenhum extrato de proventos recebidos carregado para conferência cruzada.")
        return

    st.dataframe(
        prov_rec,
        use_container_width=True,
        column_config={
            "ativo": st.column_config.TextColumn("Ativo"),
            "total_movimentacao": st.column_config.NumberColumn(
                "Movimentação (R$)",
                format="R$ %.2f",
            ),
            "total_extrato_proventos": st.column_config.NumberColumn(
                "Extrato Proventos (R$)",
                format="R$ %.2f",
            ),
            "delta": st.column_config.NumberColumn(
                "Diferença (R$)",
                format="R$ %.2f",
            ),
            "status": st.column_config.TextColumn("Status"),
        },
        hide_index=True,
    )

    divergentes = prov_rec[prov_rec["status"] == "Divergente"]
    if divergentes.empty:
        st.success("Todos os proventos auditados estão 100% conciliados com o extrato da B3.")
    else:
        st.warning(f"{len(divergentes)} ativo(s) com divergência de proventos entre movimentação e extrato.")

