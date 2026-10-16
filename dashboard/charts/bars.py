import plotly.express as px


def bar_proventos(proventos):
    return px.bar(
        proventos,
        x="mes",
        y="valor_liquido",
        title="Proventos por mês",
        labels={"mes": "Mês", "valor_liquido": "Valor"},
        color_discrete_sequence=["#2ecc71"],
    )


def bar_dy(dy):
    return px.bar(
        dy,
        x="produto",
        y="dy_pct",
        title="Dividend Yield estimado por ativo",
        labels={"produto": "Ativo", "dy_pct": "DY (%)"},
        color_discrete_sequence=["#5dade2"],
    )
