from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base import aplicar_layout_padrao
from .defaults import (
    COLOR_DIVIDENDO,
    COLOR_DY,
    COLOR_FII,
    COLOR_JCP,
    COLOR_LUCRO,
    COLOR_PATRIMONIO,
    COLOR_PREJUIZO,
    COLOR_PROVENTOS,
    HEIGHT_BAR,
)


def bar_proventos(
    proventos: pd.DataFrame | None,
    mostrar_acumulado: bool = True,
    segmentar_por_tipo: bool = False,
) -> go.Figure:
    if proventos is None or proventos.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text="Histórico Mensal de Proventos Recebidos"))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    df = proventos.copy()
    if "valor_liquido" in df.columns:
        df["valor_liquido"] = pd.to_numeric(df["valor_liquido"], errors="coerce").fillna(0.0)

    # Identificar se há coluna de tipo para segmentação
    tipo_col = next((c for c in ["tipo_provento", "tipo", "movimentacao"] if c in df.columns), None)
    usar_segmentacao = segmentar_por_tipo and tipo_col is not None

    # Agregação mensal total para ordenação e cálculo da curva de acumulado anual
    if "mes" in df.columns:
        df_mensal = df.groupby("mes", as_index=False)["valor_liquido"].sum()
        df_mensal["_dt"] = pd.to_datetime(df_mensal["mes"])
        df_mensal = df_mensal.sort_values("_dt").reset_index(drop=True)
        ano = df_mensal["_dt"].dt.year
        df_mensal["acumulado_ano"] = df_mensal.groupby(ano)["valor_liquido"].cumsum()
    else:
        df_mensal = pd.DataFrame(columns=["mes", "valor_liquido", "acumulado_ano"])

    if usar_segmentacao:
        fig = go.Figure()
        df_bar = df.groupby(["mes", tipo_col], as_index=False)["valor_liquido"].sum()
        df_bar["_dt"] = pd.to_datetime(df_bar["mes"])
        df_bar = df_bar.sort_values("_dt").reset_index(drop=True)

        meses_ordenados = df_mensal["mes"].tolist()

        def obter_cor_tipo(tipo_nome: str) -> str:
            t = str(tipo_nome).strip().lower()
            if "dividendo" in t:
                return COLOR_DIVIDENDO
            if "jcp" in t or "juros" in t:
                return COLOR_JCP
            if "fii" in t or "rendimento" in t:
                return COLOR_FII
            return COLOR_PROVENTOS

        tipos_presentes = list(df_bar[tipo_col].unique())
        ordem_preferencial = ["Dividendo", "Dividendos", "JCP", "Rendimento FII", "FII", "Rendimento", "Outros"]
        tipos_ordenados = [t for t in ordem_preferencial if t in tipos_presentes] + [
            t for t in tipos_presentes if t not in ordem_preferencial
        ]

        for t in tipos_ordenados:
            sub = df_bar[df_bar[tipo_col] == t]
            fig.add_trace(
                go.Bar(
                    x=sub["mes"],
                    y=sub["valor_liquido"],
                    name=str(t),
                    marker_color=obter_cor_tipo(str(t)),
                    hovertemplate=f"<b>Mês:</b> %{{x}}<br><b>{t}:</b> R$ %{{y:,.2f}}<extra></extra>",
                )
            )

        fig.update_layout(
            barmode="stack",
            title=dict(text="Histórico Mensal de Proventos Recebidos por Tipo"),
            xaxis=dict(title="Mês de Pagamento", categoryorder="array", categoryarray=meses_ordenados),
            yaxis=dict(title="Proventos Líquidos (R$)"),
        )
    else:
        fig = px.bar(
            df_mensal,
            x="mes",
            y="valor_liquido",
            title="Histórico Mensal de Proventos Recebidos",
            labels={"mes": "Mês de Pagamento", "valor_liquido": "Proventos Líquidos (R$)"},
            color_discrete_sequence=[COLOR_PROVENTOS],
        )
        fig.update_traces(
            name="Mensal",
            hovertemplate="<b>Mês:</b> %{x}<br><b>Recebido:</b> R$ %{y:,.2f}<extra></extra>",
        )

    if mostrar_acumulado and not df_mensal.empty:
        if len(fig.data) > 0:
            fig.data[0].showlegend = True
        fig.add_trace(
            go.Scatter(
                x=df_mensal["mes"],
                y=df_mensal["acumulado_ano"],
                mode="lines+markers",
                name="Acumulado no Ano",
                line=dict(color=COLOR_PATRIMONIO, width=2.5),
                marker=dict(size=6, color=COLOR_PATRIMONIO),
                yaxis="y2",
                hovertemplate="<b>Mês:</b> %{x}<br><b>Acumulado no Ano:</b> R$ %{y:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title="Acumulado no Ano (R$)",
                overlaying="y",
                side="right",
                showgrid=False,
            )
        )
        return aplicar_layout_padrao(
            fig,
            altura=HEIGHT_BAR,
            legenda_horizontal=True,
            margens=dict(l=30, r=50, t=60, b=40),
        )

    if usar_segmentacao:
        return aplicar_layout_padrao(
            fig,
            altura=HEIGHT_BAR,
            legenda_horizontal=True,
            margens=dict(l=30, r=30, t=60, b=40),
        )

    return aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)


def bar_dy(dy: pd.DataFrame | None) -> go.Figure:
    if dy is None or dy.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text="Dividend Yield LTM por Ativo (%)"))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    y_col = "dy_ltm_pct" if "dy_ltm_pct" in dy.columns else "dy_pct"
    fig = px.bar(
        dy,
        x="produto",
        y=y_col,
        title="Dividend Yield LTM por Ativo (%)",
        labels={"produto": "Ativo", y_col: "Dividend Yield (%)"},
        color_discrete_sequence=[COLOR_DY],
    )
    fig.update_traces(
        hovertemplate="<b>Ativo:</b> %{x}<br><b>DY LTM:</b> %{y:.2f}%<extra></extra>"
    )
    return aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)


def bar_lucro_prejuizo(
    pos_cards: pd.DataFrame | None,
    *,
    titulo: str = "Resultado por Ativo (P&L em R$)",
) -> go.Figure:
    """Gera gráfico de barras horizontais com Lucro e Prejuízo por ativo."""
    if pos_cards is None or pos_cards.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    df = pos_cards.copy()
    if "custo_total" in df.columns:
        df = df[df["custo_total"] > 0].copy()

    if df.empty or "pl" not in df.columns or "produto" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    # Ordena por pl crescente para que o maior lucro fique no topo do eixo Y
    df = df.sort_values("pl", ascending=True).copy()

    if "variacao_pct" not in df.columns:
        df["variacao_pct"] = 0.0

    df["status"] = df["pl"].apply(lambda v: "Lucro" if v >= 0 else "Prejuízo")

    fig = px.bar(
        df,
        x="pl",
        y="produto",
        orientation="h",
        color="status",
        color_discrete_map={"Lucro": COLOR_LUCRO, "Prejuízo": COLOR_PREJUIZO},
        title=titulo,
        labels={"pl": "Lucro / Prejuízo (R$)", "produto": "Ativo", "status": "Resultado"},
        custom_data=["variacao_pct"],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>Ativo:</b> %{y}<br>"
            "<b>P&L:</b> R$ %{x:,.2f}<br>"
            "<b>Variação:</b> %{customdata[0]:+.2f}%"
            "<extra></extra>"
        )
    )
    fig.update_layout(showlegend=False)
    return aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)


def bar_distribuicao_ativos(
    pos: pd.DataFrame | None,
    top_n: int | None = None,
    titulo: str = "Ranking de Ativos por Patrimônio (R$)",
) -> go.Figure:
    """Gera gráfico de barras horizontais ordenado com a distribuição da carteira por ativo."""
    if pos is None or pos.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    df = pos.copy()
    col_valor = "valor_abs" if "valor_abs" in df.columns else ("valor" if "valor" in df.columns else None)
    col_nome = "produto" if "produto" in df.columns else None

    if col_valor is None or col_nome is None or df.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    df[col_valor] = pd.to_numeric(df[col_valor], errors="coerce").fillna(0.0)
    df = df[df[col_valor] > 0].copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=titulo))
        return aplicar_layout_padrao(fig, altura=HEIGHT_BAR)

    total = df[col_valor].sum()
    if total > 0:
        df["peso_pct"] = (df[col_valor] / total) * 100.0
    else:
        df["peso_pct"] = 0.0

    # Ordena decrescente pelo valor, aplica top_n se fornecido
    df = df.sort_values(col_valor, ascending=False)
    if top_n is not None and top_n > 0:
        df = df.head(top_n)

    # Inverte para que a maior barra fique no topo no eixo horizontal do Plotly
    df = df.sort_values(col_valor, ascending=True).copy()

    df["texto_barra"] = df.apply(
        lambda r: f"R$ {r[col_valor]:,.2f} ({r['peso_pct']:.1f}%)",
        axis=1,
    )

    tem_categoria = "categoria" in df.columns
    cor_kwargs = dict(color="categoria") if tem_categoria else dict()

    fig = px.bar(
        df,
        x=col_valor,
        y=col_nome,
        orientation="h",
        title=titulo,
        labels={col_valor: "Patrimônio (R$)", col_nome: "Ativo", "categoria": "Classe"},
        custom_data=["peso_pct"],
        **cor_kwargs,
    )

    if not tem_categoria:
        fig.update_traces(marker_color=COLOR_PATRIMONIO)

    fig.update_traces(
        text=df["texto_barra"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Patrimônio: R$ %{x:,.2f}<br>"
            "Participação: %{customdata[0]:.2f}%"
            "<extra></extra>"
        ),
    )

    altura_calculada = max(HEIGHT_BAR, len(df) * 32 + 90)

    fig.update_layout(
        showlegend=tem_categoria,
        xaxis=dict(tickformat=",.2f"),
        yaxis=dict(type="category"),
        margin=dict(l=30, r=110, t=60, b=40),
    )

    return aplicar_layout_padrao(fig, altura=altura_calculada, legenda_horizontal=False)


