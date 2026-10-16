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
    pos["valor_abs"] = pos["valor"].abs()
    return pos


def compute_position_categoria(df):
    pos = compute_position(df).copy()
    if pos.empty:
        return pd.DataFrame(columns=["categoria", "valor", "quantidade"])

    pos["categoria"] = pos["produto"].apply(classificar_ativo)
    resumo = pos.groupby("categoria", as_index=False).agg(valor=("valor_abs", "sum"), quantidade=("quantidade", "sum"))
    return resumo.sort_values("valor", ascending=False)


def compute_position_por_categoria(df, categoria):
    pos = compute_position(df).copy()
    if pos.empty:
        return pos

    pos["categoria"] = pos["produto"].apply(classificar_ativo)
    return pos[pos["categoria"].eq(categoria)].sort_values("valor_abs", ascending=False)


def compute_proventos(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["mes", "valor_liquido"])

    proventos = df.loc[
        df["entrada_saida"].str.contains("credito|crédito", case=False, na=False)
        & ~df["movimentacao"].str.contains("compra|transferência|liquidação|transferencia|liquidacao", case=False, na=False)
    ].copy()

    if proventos.empty:
        return pd.DataFrame(columns=["mes", "valor_liquido"])

    resumo = proventos.groupby("mes", as_index=False)["valor_liquido"].sum()
    resumo["mes"] = pd.to_datetime(resumo["mes"].astype(str) + "-01")
    resumo["valor_liquido"] = resumo["valor_liquido"].clip(lower=0)
    return resumo


def compute_evolucao(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["data", "patrimonio"])

    evol = df.groupby("data", as_index=False)["valor_liquido"].sum()
    evol["patrimonio"] = evol["valor_liquido"].cumsum()
    return evol


def compute_dy(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "valor_abs", "provento_total", "dy_pct"])

    pos = compute_position(df)
    recebidos = (
        df.loc[
            df["entrada_saida"].str.contains("credito|crédito", case=False, na=False)
            & ~df["movimentacao"].str.contains("compra|transferência|liquidação|transferencia|liquidacao", case=False, na=False)
        ]
        .groupby("produto", as_index=False)["valor_liquido"]
        .sum()
        .rename(columns={"valor_liquido": "provento_total"})
    )

    dy = pos[["produto", "valor_abs"]].merge(recebidos, on="produto", how="left")
    dy["provento_total"] = dy["provento_total"].fillna(0)
    dy["dy_pct"] = (dy["provento_total"] / dy["valor_abs"].replace(0, pd.NA) * 100).fillna(0)
    return dy.sort_values("dy_pct", ascending=False)


def compute_preco_medio(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    if {"produto", "quantidade", "valor_operacao"}.difference(df.columns):
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    compras = df[df["quantidade"].fillna(0) > 0].copy()
    if compras.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    resumo = compras.groupby("produto", as_index=False).agg(quantidade=("quantidade", "sum"), custo_total=("valor_operacao", "sum"))
    resumo["preco_medio"] = (resumo["custo_total"] / resumo["quantidade"]).replace([float("inf"), float("-inf")], pd.NA)
    return resumo.sort_values("preco_medio", ascending=False)
