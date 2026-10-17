from __future__ import annotations

import plotly.graph_objects as go

from .defaults import (
    FONT_FAMILY,
    FONT_SIZE_BASE,
    FONT_SIZE_TITLE,
    FONT_COLOR_TITLE,
    MARGIN_DEFAULT,
    HOVERLABEL,
)


def aplicar_layout_padrao(
    fig: go.Figure,
    *,
    altura: int = 400,
    legenda_horizontal: bool = True,
    margens: dict | None = None,
) -> go.Figure:
    padrao_margens = margens or MARGIN_DEFAULT

    fig.update_layout(
        separators=",.",
        height=altura,
        margin=padrao_margens,
        font=dict(family=FONT_FAMILY, size=FONT_SIZE_BASE),
        hoverlabel=HOVERLABEL,
        title=dict(
            font=dict(family=FONT_FAMILY, size=FONT_SIZE_TITLE, color=FONT_COLOR_TITLE),
            x=0,
            xanchor="left",
            pad=dict(l=4),
        ),
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
