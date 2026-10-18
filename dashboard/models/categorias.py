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


# ---------------------------------------------------------------------------
# As 5 Macro-Classes Canônicas da Carteira
# ---------------------------------------------------------------------------
CLASSE_ACOES = "Ações"
CLASSE_INTERNACIONAL = "Internacional"
CLASSE_RENDA_FIXA_INFLACAO = "Renda fixa inflação"
CLASSE_RENDA_FIXA_POS = "Renda fixa pós-fixada"
CLASSE_RENDA_FIXA_PRE = "Renda fixa prefixada"

CLASSES_5 = (
    CLASSE_ACOES,
    CLASSE_INTERNACIONAL,
    CLASSE_RENDA_FIXA_INFLACAO,
    CLASSE_RENDA_FIXA_POS,
    CLASSE_RENDA_FIXA_PRE,
)


def classificar_classe_5(produto: str, categoria: str | None = None) -> str:
    """Classifica um ativo em uma das 5 macro-classes canônicas.

    - Ações: Ações brasileiras
    - Internacional: BDRs e ativos internacionais
    - Renda fixa inflação: Tesouro IPCA+, Educa+ e indexados à inflação
    - Renda fixa pós-fixada: Tesouro Selic
    - Renda fixa prefixada: Tesouro Prefixado
    """
    cat_upper = str(categoria or "").strip().upper()
    prod_upper = str(produto or "").strip().upper()

    if cat_upper in ("AÇÕES", "ACOES", "AÇÃO"):
        return CLASSE_ACOES
    if cat_upper in ("BDR", "BDRS"):
        return CLASSE_INTERNACIONAL
    if cat_upper == CATEGORIA_TESOURO or "TESOURO" in prod_upper:
        if "SELIC" in prod_upper:
            return CLASSE_RENDA_FIXA_POS
        if "PREFIXADO" in prod_upper:
            return CLASSE_RENDA_FIXA_PRE
        if "IPCA" in prod_upper or "EDUCA" in prod_upper:
            return CLASSE_RENDA_FIXA_INFLACAO
        return LABEL_TESOURO
    return categoria or "Outros"


def calcular_alocacao_5_classes(pos_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula dinamicamente a alocação agregada nas 5 classes a partir de pos ou pos_cards."""
    if pos_df is None or pos_df.empty:
        return pd.DataFrame(columns=["classe", "categoria", "valor", "peso_pct"])

    df = pos_df.copy()
    col_valor = "valor_abs" if "valor_abs" in df.columns else ("valor" if "valor" in df.columns else "valor_operacao")
    if col_valor not in df.columns:
        return pd.DataFrame(columns=["classe", "categoria", "valor", "peso_pct"])

    df["classe"] = df.apply(
        lambda r: classificar_classe_5(r.get("produto"), r.get("categoria")),
        axis=1,
    )
    df["categoria"] = df["classe"]

    agrupado = (
        df.groupby(["classe", "categoria"], as_index=False)[col_valor]
        .sum()
        .rename(columns={col_valor: "valor"})
    )
    total = float(agrupado["valor"].sum())
    agrupado["peso_pct"] = (
        (agrupado["valor"] / total * 100).round(1) if total > 0 else 0.0
    )
    return agrupado.sort_values("valor", ascending=False).reset_index(drop=True)

