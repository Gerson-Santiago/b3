import pandas as pd

from dashboard.models.eventos import efeito_movimentacao


def compute_proventos(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["mes", "valor_liquido"])

    proventos = df.loc[
        df.apply(
            lambda row: bool(efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida")).provento)
            and str(row.get("entrada_saida") or "").strip().lower() in {"credito", "crédito"},
            axis=1,
        )
    ].copy()

    if proventos.empty:
        return pd.DataFrame(columns=["mes", "valor_liquido"])

    resumo = proventos.groupby("mes", as_index=False)["valor_liquido"].sum()
    resumo["mes"] = pd.to_datetime(resumo["mes"].astype(str) + "-01")
    resumo["valor_liquido"] = resumo["valor_liquido"].clip(lower=0)
    return resumo
