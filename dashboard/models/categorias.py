"""Agrupamento canônico de categorias da carteira."""
from __future__ import annotations

import pandas as pd

CATEGORIAS_BOLSA = frozenset({"AÇÕES", "BDR"})
LABEL_BOLSA = "Bolsa de Valores"
CATEGORIA_TESOURO = "TESOURO"


def agrupar_bolsa(pos_categoria: pd.DataFrame) -> pd.DataFrame:
    """Agrupa AÇÕES e BDR em 'Bolsa de Valores'."""
    if pos_categoria.empty:
        return pos_categoria.copy()

    agrupada = pos_categoria.copy()
    agrupada["categoria"] = agrupada["categoria"].replace(
        {cat: LABEL_BOLSA for cat in CATEGORIAS_BOLSA}
    )
    return (
        agrupada.groupby("categoria", as_index=False)
        .agg(valor=("valor", "sum"), quantidade=("quantidade", "sum"))
        .sort_values("valor", ascending=False)
    )
