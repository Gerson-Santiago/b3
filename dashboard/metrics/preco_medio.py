import pandas as pd

from dashboard.models.eventos import aplicar_eventos_ordenados

_COLUNAS = ["produto", "quantidade", "custo_total", "preco_medio"]


def compute_preco_medio(df):
    resumo = aplicar_eventos_ordenados(df)
    if resumo.empty:
        return pd.DataFrame(columns=_COLUNAS)
    return resumo.sort_values("preco_medio", ascending=False, kind="mergesort").reset_index(drop=True)
