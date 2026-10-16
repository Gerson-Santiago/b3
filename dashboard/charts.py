import plotly.express as px


def pie_carteira(pos):
    return px.pie(
        pos,
        names="produto",
        values="valor_abs",
        title="Distribuição da carteira por ativo",
        hole=0.4,
    )


def pie_carteira_por_categoria(pos_categoria):
    return px.pie(
        pos_categoria,
        names="categoria",
        values="valor",
        title="Carteira por categoria (BDR / ACOES / TESOURO)",
        hole=0.4,
    )


def pie_categoria(pos):
    return px.pie(
        pos,
        names="produto",
        values="valor_abs",
        title="Distribuição por ativo",
        hole=0.4,
    )


def bar_proventos(proventos):
    return px.bar(
        proventos,
        x="mes",
        y="valor_liquido",
        title="Proventos por mês",
        labels={"mes": "Mês", "valor_liquido": "Valor"},
        color_discrete_sequence=["#2ecc71"],
    )


def line_evolucao(evol):
    return px.line(
        evol,
        x="data",
        y="patrimonio",
        title="Evolução do patrimônio",
        labels={"data": "Data", "patrimonio": "Patrimônio"},
        markers=True,
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
