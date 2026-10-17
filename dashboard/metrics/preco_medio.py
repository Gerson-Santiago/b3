import pandas as pd

from dashboard.models.eventos import aplicar_eventos_ordenados


def compute_preco_medio(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    base = df.copy()
    if "produto" not in base.columns:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    if "valor_liquido" not in base.columns:
        if "valor_operacao" not in base.columns:
            return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])
        base["valor_liquido"] = base["valor_operacao"]

    if "qtd_liquida" not in base.columns:
        if "quantidade" not in base.columns:
            return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

        if "entrada_saida" in base.columns:
            sinal = base["entrada_saida"].fillna("").astype(str).str.lower().map({"credito": 1, "crédito": 1, "debito": -1, "débito": -1}).fillna(0)
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0) * sinal
        else:
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0).clip(lower=0)

    base["qtd_liquida"] = pd.to_numeric(base["qtd_liquida"], errors="coerce").fillna(0)
    base["valor_liquido"] = pd.to_numeric(base["valor_liquido"], errors="coerce").fillna(0)

    resumo = aplicar_eventos_ordenados(base)
    if resumo.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    resumo = resumo.sort_values("preco_medio", ascending=False, kind="mergesort")
    return resumo.reset_index(drop=True)
