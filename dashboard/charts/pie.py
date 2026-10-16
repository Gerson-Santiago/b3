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
