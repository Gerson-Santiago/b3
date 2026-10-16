import pandas as pd


def compute_evolucao(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["data", "patrimonio"])

    evol = df.groupby("data", as_index=False)["valor_liquido"].sum()
    evol["patrimonio"] = evol["valor_liquido"].cumsum()
    return evol
