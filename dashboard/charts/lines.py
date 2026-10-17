import plotly.express as px
import plotly.graph_objects as go
from .base import aplicar_layout_padrao


def line_evolucao(evol):
    fig = px.line(
        evol,
        x="data",
        y="patrimonio",
        title="Evolução Temporal do Portfólio",
        labels={"data": "Data", "patrimonio": "Valor (R$)"},
        markers=True,
    )
    fig.update_traces(
        hovertemplate="<b>Data:</b> %{x|%d/%m/%Y}<br><b>Patrimônio:</b> R$ %{y:,.2f}<extra></extra>"
    )
    return aplicar_layout_padrao(fig, altura=400, legenda_horizontal=False)


def line_comparativo_patrimonio_e_aportes(curva_aportes, curva_patrimonio):
    fig = go.Figure()

    if curva_aportes is not None and not curva_aportes.empty:
        fig.add_trace(
            go.Scatter(
                x=curva_aportes["data"],
                y=curva_aportes["custo_acumulado"],
                mode="lines",
                name="Custo Acumulado (Aportes)",
                line=dict(color="#64748b", width=2, dash="dash"),
                hovertemplate="<b>Aportes Acumulados:</b> R$ %{y:,.2f}<extra></extra>",
            )
        )

    if curva_patrimonio is not None and not curva_patrimonio.empty:
        fig.add_trace(
            go.Scatter(
                x=curva_patrimonio["data"],
                y=curva_patrimonio["patrimonio_liquido"],
                mode="lines+markers",
                name="Patrimônio Consolidado (Snapshots B3)",
                line=dict(color="#2563eb", width=3),
                marker=dict(size=8, color="#1d4ed8"),
                hovertemplate="<b>Patrimônio Real:</b> R$ %{y:,.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Patrimônio Consolidado vs Custo Acumulado de Aportes",
        xaxis_title="Data de Referência",
        yaxis_title="Montante (R$)",
    )
    return aplicar_layout_padrao(fig, altura=430, legenda_horizontal=True)
