import plotly.express as px


def line_evolucao(evol):
    return px.line(
        evol,
        x="data",
        y="patrimonio",
        title="Evolução do patrimônio",
        labels={"data": "Data", "patrimonio": "Patrimônio"},
        markers=True,
    )
