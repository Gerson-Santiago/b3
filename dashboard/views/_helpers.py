"""Helpers de renderização reutilizados por todas as views.

Responsabilidade única: eliminar o padrão repetido
``if df.empty: st.info(...) else: st.dataframe(...)``
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

# Quantas colunas de cards por linha
_CARDS_POR_LINHA = 3


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


def _render_card(row: pd.Series, rotulo_valor: str = "Valor Atual (snapshot)") -> None:
    """Renderiza um único card de ativo dentro de um st.container."""
    produto = str(row.get("produto", "—"))
    categoria = str(row.get("categoria", ""))
    quantidade = row.get("quantidade", 0)
    valor_abs = float(row.get("valor_abs", 0))
    preco_medio = float(row.get("preco_medio", 0))
    custo_total = float(row.get("custo_total", 0))
    pl = float(row.get("pl", 0))
    variacao_pct = float(row.get("variacao_pct", 0))
    peso_pct = float(row.get("peso_pct", 0))

    if custo_total > 0:
        if variacao_pct > 0:
            delta_val = f"+R$ {pl:,.2f} (+{variacao_pct:.2f}%)"
            delta_color = "normal"
        elif variacao_pct < 0:
            delta_val = f"-R$ {abs(pl):,.2f} ({variacao_pct:.2f}%)"
            delta_color = "normal"
        else:
            delta_val = "R$ 0,00 (0.00%)"
            delta_color = "off"
    else:
        delta_val = "0.00%"
        delta_color = "off"

    with st.container(border=True):
        badge_peso = (
            f"&nbsp;<span style='font-size:0.75rem;background:#dbeafe;"
            f"border-radius:4px;padding:1px 6px;color:#1e40af;font-weight:600'>{peso_pct:.1f}% da carteira</span>"
            if peso_pct > 0
            else ""
        )
        st.markdown(
            f"**{produto}** &nbsp; "
            f"<span style='font-size:0.75rem;background:#e2e8f0;"
            f"border-radius:4px;padding:1px 6px;color:#475569'>{categoria}</span>"
            f"{badge_peso}",
            unsafe_allow_html=True,
        )
        # Métricas em 2 colunas
        c1, c2 = st.columns(2)
        c1.metric("Quantidade", f"{quantidade:,.0f}")
        c2.metric("Preço Médio", f"R$ {preco_medio:,.2f}" if preco_medio else "—")
        c3, c4 = st.columns(2)
        c3.metric("Custo Total", f"R$ {custo_total:,.2f}" if custo_total else "—")
        c4.metric(
            rotulo_valor,
            f"R$ {valor_abs:,.2f}",
            delta=delta_val,
            delta_color=delta_color,
        )


def render_cards_grid(
    df: pd.DataFrame,
    titulo: str,
    msg_vazia: str,
    *,
    nivel: str = "####",
    cards_por_linha: int = _CARDS_POR_LINHA,
    rotulo_valor: str = "Valor Atual (snapshot)",
) -> None:
    """Renderiza uma grade de cards de ativos.

    Espera as colunas produzidas por ``_enriquecer_pos_cards`` em state.py:
    produto, categoria, quantidade, valor_abs, preco_medio, custo_total, pl, variacao_pct.

    Para DataFrames sem essas colunas extras (ex.: Tesouro sem PM), exibe
    os dados disponíveis sem quebrar.
    """
    st.markdown(f"{nivel} {titulo}")
    if df.empty:
        st.info(msg_vazia)
        return

    # Delta sem ícone (nulo/neutro) fica em azul
    st.markdown(
        "<style>div[data-testid='stMetricDelta']:not(:has(svg)) { color: #2563eb !important; }</style>",
        unsafe_allow_html=True,
    )

    rows = [row for _, row in df.iterrows()]
    for i in range(0, len(rows), cards_por_linha):
        bloco = rows[i : i + cards_por_linha]
        cols = st.columns(len(bloco))
        for col, row in zip(cols, bloco):
            with col:
                _render_card(row, rotulo_valor=rotulo_valor)
