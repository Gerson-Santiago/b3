"""Helpers de renderização reutilizados por todas as views.

Responsabilidade única: eliminar o padrão repetido
``if df.empty: st.info(...) else: st.dataframe(...)``
"""
from __future__ import annotations

import pandas as pd
import streamlit as st


def render_section(
    df: pd.DataFrame,
    titulo: str,
    msg_vazia: str,
    *,
    nivel: str = "####",
) -> None:
    """Exibe um cabeçalho e uma tabela ou mensagem informativa.

    Parameters
    ----------
    df:
        DataFrame a exibir.
    titulo:
        Texto do cabeçalho Markdown (sem os ``#``).
    msg_vazia:
        Mensagem exibida com ``st.info`` quando *df* estiver vazio.
    nivel:
        Nível do cabeçalho Markdown (padrão ``####``).
    """
    st.markdown(f"{nivel} {titulo}")
    if df.empty:
        st.info(msg_vazia)
    else:
        st.dataframe(df, width="stretch")
