import pandas as pd


def classificar_ativo(produto):
    texto = str(produto or "").upper()
    if "TESOURO" in texto:
        return "TESOURO"
    if "BDR" in texto:
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
