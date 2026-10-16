import pandas as pd


def _is_evento_corporativo(movimentacao):
    texto = str(movimentacao or "").lower()
    padroes = [
        "transferência",
        "transferencia",
        "liquidação",
        "liquidacao",
        "bonificação",
        "bonificacao",
        "desdobramento",
        "desdobr",
        "split",
        "grupamento",
        "amortização",
        "amortizacao",
        "dividendo",
        "jcp",
        "juros",
        "rendimento",
        "provento",
    ]
    return any(padrao in texto for padrao in padroes)


def compute_preco_medio(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    base = df.copy()
    if "produto" not in base.columns or "valor_operacao" not in base.columns:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    if "qtd_liquida" not in base.columns:
        if "quantidade" not in base.columns:
            return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

        if "entrada_saida" in base.columns:
            sinal = (
                base["entrada_saida"].fillna("").astype(str).str.lower().map({"credito": 1, "crédito": 1, "debito": -1, "débito": -1}).fillna(0)
            )
            base["qtd_liquida"] = base["quantidade"].fillna(0) * sinal
        else:
            base["qtd_liquida"] = base["quantidade"].fillna(0).clip(lower=0)

    if "movimentacao" in base.columns:
        compras = base.loc[
            (base["qtd_liquida"].fillna(0) > 0)
            & ~base["movimentacao"].fillna("").astype(str).apply(_is_evento_corporativo)
        ].copy()
    else:
        compras = base.loc[base["qtd_liquida"].fillna(0) > 0].copy()

    if compras.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    resumo = compras.groupby("produto", as_index=False).agg(quantidade=("qtd_liquida", "sum"), custo_total=("valor_operacao", "sum"))
    resumo["preco_medio"] = (resumo["custo_total"] / resumo["quantidade"]).replace([float("inf"), float("-inf")], pd.NA)
    return resumo.sort_values("preco_medio", ascending=False)
