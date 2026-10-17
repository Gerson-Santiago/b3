from __future__ import annotations

import pandas as pd

from dashboard.models.ativos import renomear_ativo, ticker


def obter_mapa_categorias(pos_df: pd.DataFrame) -> dict[str, str]:
    if pos_df is None or pos_df.empty or "categoria" not in pos_df.columns:
        return {}

    mapa: dict[str, str] = {}
    for _, row in pos_df.iterrows():
        prod = str(row.get("produto") or "").strip()
        cat = str(row.get("categoria") or "").strip()
        if not prod or not cat:
            continue
        tick = ticker(prod)
        if tick:
            mapa[tick] = cat
            mapa[renomear_ativo(tick)] = cat
        mapa[prod] = cat
        mapa[prod.upper()] = cat

    return mapa


mapear_categorias_posicao = obter_mapa_categorias


def classificar_ativo_por_mapa(produto: object, mapa_categorias: dict[str, str] | None = None) -> str:
    if not mapa_categorias:
        return "Não classificado"

    texto = str(produto or "").strip()
    if not texto:
        return "Não classificado"

    if texto in mapa_categorias:
        return mapa_categorias[texto]

    if texto.upper() in mapa_categorias:
        return mapa_categorias[texto.upper()]

    tick = ticker(texto)
    if tick in mapa_categorias:
        return mapa_categorias[tick]

    renomeado = renomear_ativo(tick)
    if renomeado in mapa_categorias:
        return mapa_categorias[renomeado]

    return "Não classificado"


obter_categoria_ativo = classificar_ativo_por_mapa



def classificar_ativo(produto, mapa_categorias: dict[str, str] | None = None):
    if mapa_categorias:
        return classificar_ativo_por_mapa(produto, mapa_categorias)

    texto = str(produto or "").upper().strip()
    if not texto:
        return "Não classificado"
    if "TESOURO" in texto:
        return "TESOURO"

    tick = ticker(texto)
    if tick in {"GOGL35", "MSFT34", "AAPL34", "ROXO34", "NUBR33", "NUBR35", "TSLA34", "COCA34"}:
        return "BDR"

    return "ACOES"


def _normalize_positions(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs"])

    base = df.copy()
    if "valor_liquido" not in base.columns and "valor_operacao" in base.columns:
        base["valor_liquido"] = base["valor_operacao"]
    if "qtd_liquida" not in base.columns and "quantidade" in base.columns:
        base["qtd_liquida"] = base["quantidade"]

    if "produto" not in base.columns:
        return pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs"])

    return base


def compute_position(df):
    base = _normalize_positions(df)
    if base.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs"])

    pos = (
        base.groupby("produto", as_index=False)
        .agg(quantidade=("qtd_liquida", "sum"), valor=("valor_liquido", "sum"))
    )
    pos = pos[pos["quantidade"].abs() > 0].sort_values("valor", key=lambda s: s.abs(), ascending=False)
    pos["valor"] = pos["valor"].round(2)
    pos["valor_abs"] = pos["valor"].abs().round(2)
    return pos


def compute_position_categoria(df):
    pos = compute_position(df).copy()
    if pos.empty:
        return pd.DataFrame(columns=["categoria", "valor", "quantidade"])

    if "categoria" in df.columns:
        categoria_map = df[["produto", "categoria"]].drop_duplicates().set_index("produto")["categoria"]
        pos["categoria"] = pos["produto"].map(categoria_map).fillna(pos["produto"].apply(classificar_ativo))
    else:
        pos["categoria"] = pos["produto"].apply(classificar_ativo)

    resumo = pos.groupby("categoria", as_index=False).agg(valor=("valor_abs", "sum"), quantidade=("quantidade", "sum"))
    resumo["valor"] = resumo["valor"].round(2)
    return resumo.sort_values("valor", ascending=False)


def compute_position_por_categoria(df, categoria):
    pos = compute_position(df).copy()
    if pos.empty:
        return pos

    if "categoria" in df.columns:
        categoria_map = df[["produto", "categoria"]].drop_duplicates().set_index("produto")["categoria"]
        pos["categoria"] = pos["produto"].map(categoria_map).fillna(pos["produto"].apply(classificar_ativo))
    else:
        pos["categoria"] = pos["produto"].apply(classificar_ativo)

    return pos[pos["categoria"].eq(categoria)].sort_values("valor_abs", ascending=False)
