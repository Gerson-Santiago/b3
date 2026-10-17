import pandas as pd

from dashboard.models.eventos import efeito_movimentacao
from dashboard.models.movimentacao import is_credito


def compute_proventos(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["mes", "valor_liquido"])

    proventos = df.loc[
        df.apply(
            lambda row: bool(efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida")).provento)
            and is_credito(row.get("entrada_saida")),
            axis=1,
        )
    ].copy()

    if proventos.empty:
        return pd.DataFrame(columns=["mes", "valor_liquido"])

    resumo = proventos.groupby("mes", as_index=False)["valor_liquido"].sum()
    resumo["mes"] = pd.to_datetime(resumo["mes"].astype(str) + "-01")
    resumo["valor_liquido"] = resumo["valor_liquido"].clip(lower=0)
    return resumo
