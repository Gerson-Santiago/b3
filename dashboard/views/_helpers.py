"""Helpers de renderização reutilizados por todas as views.

Responsabilidade única: eliminar o padrão repetido
``if df.empty: st.info(...) else: st.dataframe(...)``
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from dashboard.views.svg.links import get_svg_url
except ImportError:  # pragma: no cover
    from views.svg.links import get_svg_url


def _svg_icon_html(ticker: str) -> str:
    """Retorna o HTML do ícone SVG do ativo, ou string vazia.

    Usa ``<img loading="lazy">`` — o browser busca, cacheia e renderiza
    em paralelo, sem bloquear o Python. Dimensão fixa 28 × 28 px.
    Se o ticker não estiver mapeado, retorna ``""`` (sem elemento).
    """
    url = get_svg_url(ticker)
    if not url:
        return ""
    return (
        f'<img src="{url}" '
        f'width="28" height="28" '
        f'loading="lazy" '
        f'onerror="this.style.display=\'none\'" '
        f'style="border-radius:4px; object-fit:contain; flex-shrink:0;" '
        f'alt="{ticker}">'
    )

# Quantas colunas de cards por linha
_CARDS_POR_LINHA = 2


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
        st.dataframe(df, use_container_width=True)


def _obter_tipo_e_grupo(categoria: str) -> tuple[str, str]:
    """Retorna o tipo no singular (para o badge do card) e o texto de referência do grupo.

    Exemplos
    --------
    'AÇÕES'   -> ('Ação', 'das Ações')
    'BDR'     -> ('BDR', 'dos BDRs')
    'TESOURO' -> ('Tesouro', 'do Tesouro')
    """
    cat = (categoria or "").strip().upper()
    if cat in ("AÇÕES", "ACOES", "AÇÃO"):
        return "Ação", "das Ações"
    if cat in ("BDR", "BDRS"):
        return "BDR", "dos BDRs"
    if "TESOURO" in cat:
        return "Tesouro", "do Tesouro"
    if cat in ("FII", "FIIS"):
        return "FII", "dos FIIs"
    rotulo = categoria.title() if categoria else "Ativo"
    return rotulo, f"de {rotulo}"


def _extrair_ticker(produto: str) -> str:
    """Extrai o ticker de uma string de produto.

    Suporta os dois formatos presentes nos arquivos B3:

    * ``"PETR4"``                       → ``"PETR4"``
    * ``"PETR4 - PETROLEO BRASILEIRO"`` → ``"PETR4"``
    * ``"Tesouro Selic 2029"``          → ``"Tesouro Selic 2029"`` (sem " - ", retorna inteiro)
    """
    return produto.split(" - ")[0].strip()


def format_moeda_brl(valor: float | int | None) -> str:
    """Formata valor numérico como moeda brasileira (ex.: 2943.59 -> 'R$ 2.943,59')."""
    if valor is None or pd.isna(valor):
        return "—"
    try:
        v = float(valor)
        s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
    except (ValueError, TypeError):
        return "—"


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
    peso_pct_no_produto = float(row.get("peso_pct_no_produto", 0))

    tipo_singular, texto_grupo = _obter_tipo_e_grupo(categoria)
    peso_prod_str = f"{peso_pct_no_produto:.1f}%".replace(".", ",")
    peso_cart_str = f"{peso_pct:.1f}%".replace(".", ",")

    if custo_total > 0:
        s_pl = format_moeda_brl(abs(pl))
        s_pct = f"{abs(variacao_pct):.2f}".replace(".", ",")
        if variacao_pct > 0:
            delta_val = f"+{s_pl} (+{s_pct}%)"
            delta_color = "normal"
        elif variacao_pct < 0:
            delta_val = f"-{s_pl} (-{s_pct}%)"
            delta_color = "normal"
        else:
            delta_val = "R$ 0,00 (0,00%)"
            delta_color = "off"
    else:
        delta_val = "0,00%"
        delta_color = "off"

    with st.container(border=True):
        # Topo: ícone SVG + nome do ativo à esquerda, badge de tipo à direita
        ticker = _extrair_ticker(produto)          # "PETR4 - PETROBRAS" → "PETR4"
        icon_html = _svg_icon_html(ticker)
        icon_block = (
            f'<div style="display:flex; align-items:center; gap:6px; min-width:0;">'
            f'{icon_html}'
            f'<span style="font-weight:600; font-size:0.95rem; line-height:1.3; '
            f'overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{produto}</span>'
            f'</div>'
        ) if icon_html else (
            f'<span style="font-weight:600; font-size:0.95rem; line-height:1.3;">{produto}</span>'
        )
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; align-items:center; '
            f'gap:8px; margin-bottom:8px;">'
            f'{icon_block}'
            f'<span style="font-size:0.75rem; background:#e2e8f0; border-radius:4px; '
            f'padding:2px 8px; color:#475569; white-space:nowrap; flex-shrink:0;">{tipo_singular}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Métricas em 2 colunas
        c1, c2 = st.columns(2)
        # Tesouro Direto permite frações (ex.: 0,12 título) → exibe 2 decimais.
        # Ações, BDR e FII são sempre inteiros → sem casas decimais.
        is_tesouro = "TESOURO" in categoria.upper()
        if is_tesouro:
            qtd_str = f"{quantidade:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            rotulo_pm = "PU Médio (1 título)"
        else:
            qtd_str = f"{int(round(quantidade)):,}".replace(",", ".")
            rotulo_pm = "Preço Médio"

        c1.metric("Quantidade", qtd_str)
        c2.metric(rotulo_pm, format_moeda_brl(preco_medio) if preco_medio else "—")
        c3, c4 = st.columns(2)
        c3.metric("Custo Total", format_moeda_brl(custo_total) if custo_total else "—")
        c4.metric(
            rotulo_valor,
            format_moeda_brl(valor_abs),
            delta=delta_val,
            delta_color=delta_color,
        )

        # Rodapé: pílulas de percentuais limpas e distribuídas (sem 'Ativo' ou 'Representa', sem emoji)
        st.markdown(
            f"""<div style="border-top: 1px solid rgba(128, 128, 128, 0.15); margin-top: 10px; padding-top: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
    <span style="font-size:0.75rem; background:#f3e8ff; border-radius:4px; padding:2px 8px; color:#6b21a8; font-weight:600;">{peso_prod_str} {texto_grupo}</span>
    <span style="font-size:0.75rem; background:#dbeafe; border-radius:4px; padding:2px 8px; color:#1e40af; font-weight:600;">{peso_cart_str} da carteira</span>
</div>""",
            unsafe_allow_html=True,
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
