import plotly.express as px
from .base import aplicar_layout_padrao


def bar_proventos(proventos):
    fig = px.bar(
        proventos,
        x="mes",
        y="valor_liquido",
        title="Histórico Mensal de Proventos Recebidos",
        labels={"mes": "Mês de Pagamento", "valor_liquido": "Proventos Líquidos (R$)"},
        color_discrete_sequence=["#10b981"],
    )
    fig.update_traces(
        hovertemplate="<b>Mês:</b> %{x}<br><b>Recebido:</b> R$ %{y:,.2f}<extra></extra>"
    )
    return aplicar_layout_padrao(fig, altura=400, legenda_horizontal=False)


def bar_dy(dy):
    y_col = "dy_ltm_pct" if "dy_ltm_pct" in dy.columns else "dy_pct"
    fig = px.bar(
        dy,
        x="produto",
        y=y_col,
        title="Dividend Yield LTM por Ativo (%)",
        labels={"produto": "Ativo", y_col: "Dividend Yield (%)"},
        color_discrete_sequence=["#0284c7"],
    )
    fig.update_traces(
        hovertemplate="<b>Ativo:</b> %{x}<br><b>DY LTM:</b> %{y:.2f}%<extra></extra>"
    )
    return aplicar_layout_padrao(fig, altura=400, legenda_horizontal=False)
