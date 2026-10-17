"""Filtragem de DataFrames do Dashboard B3.

Responsabilidade única: aplicar filtros de sidebar (instituição, produto, período)
a qualquer DataFrame que siga o contrato de colunas do projeto.
"""
from __future__ import annotations

from datetime import date

import pandas as pd


def filtrar_dataframe(
    df: pd.DataFrame,
    *,
    instituicoes: list[str],
    produtos: list[str],
    start_date: date | None = None,
    end_date: date | None = None,
) -> pd.DataFrame:
    """Aplica filtros de sidebar a *df* e retorna uma cópia filtrada.

    Parameters
    ----------
    df:
        DataFrame a ser filtrado (movimentação ou posição).
    instituicoes:
        Lista de instituições selecionadas. Vazia = sem filtro.
    produtos:
        Lista de produtos selecionados. Vazia = sem filtro.
    start_date / end_date:
        Intervalo de datas inclusive. Ignorado se a coluna ``data`` não existir
        ou se ambos forem ``None``.
    """
    if df.empty:
        return df.copy()

    resultado = df.copy()

    # Filtro por data (só aplica se a coluna existir e as datas forem informadas)
    if start_date is not None and end_date is not None and "data" in resultado.columns:
        resultado = resultado[
            (resultado["data"] >= pd.Timestamp(start_date))
            & (resultado["data"] <= pd.Timestamp(end_date))
        ]

    if instituicoes and "instituicao" in resultado.columns:
        resultado = resultado[resultado["instituicao"].isin(instituicoes)]

    if produtos:
        col_prod = "ativo" if "ativo" in resultado.columns else ("produto" if "produto" in resultado.columns else None)
        if col_prod:
            resultado = resultado[resultado[col_prod].isin(produtos)]

    return resultado
