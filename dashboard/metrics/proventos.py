import pandas as pd


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
