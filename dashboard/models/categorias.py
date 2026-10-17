"""Agrupamento canônico de categorias da carteira."""
from __future__ import annotations

import pandas as pd

CATEGORIAS_BOLSA = frozenset({"AÇÕES", "BDR"})
LABEL_BOLSA = "Bolsa de Valores"
CATEGORIA_TESOURO = "TESOURO"
LABEL_TESOURO = "Tesouro Direto"

# Mapeamento canônico: categoria interna → label de exibição.
# Única fonte da verdade para qualquer camada (charts, views, etc.)
# que precise traduzir códigos de categoria para texto legível.
_MAPA_EXIBICAO: dict[str, str] = {
    cat: LABEL_BOLSA for cat in CATEGORIAS_BOLSA
} | {CATEGORIA_TESOURO: LABEL_TESOURO}


def nome_exibicao_categoria(categoria: str) -> str:
    """Retorna o label de exibição canônico de uma categoria.

    Exemplos:
        "AÇÕES"   → "Bolsa de Valores"
        "BDR"     → "Bolsa de Valores"
        "TESOURO" → "Tesouro Direto"
        "FIIs"    → "FIIs"  (categorias sem mapeamento passam intactas)
    """
    return _MAPA_EXIBICAO.get(categoria, categoria)


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
