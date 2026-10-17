from __future__ import annotations

import plotly.graph_objects as go


def aplicar_layout_padrao(
    fig: go.Figure,
    *,
    altura: int = 400,
    legenda_horizontal: bool = True,
    margens: dict | None = None,
) -> go.Figure:
    padrao_margens = margens or dict(l=30, r=30, t=50, b=40)

    fig.update_layout(
        separators=",.",
        height=altura,
        margin=padrao_margens,
        font=dict(family="Arial, sans-serif", size=12),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )

    if legenda_horizontal:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
            )
        )

    return fig
