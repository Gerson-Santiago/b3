import pandas as pd

from .position import compute_position


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
