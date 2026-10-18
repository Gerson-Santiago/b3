import pandas as pd

from dashboard.models.eventos import efeito_movimentacao
from dashboard.models.movimentacao import classificar_tipo_provento, is_credito


_COLUNAS_CALENDARIO = ["data", "ativo", "tipo_provento", "valor_liquido"]


def compute_proventos(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["mes", "tipo_provento", "valor_liquido"])

    proventos = df.loc[
        df.apply(
            lambda row: bool(efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida")).provento)
            and is_credito(row.get("entrada_saida")),
            axis=1,
        )
    ].copy()

    if proventos.empty:
        return pd.DataFrame(columns=["mes", "tipo_provento", "valor_liquido"])

    proventos["tipo_provento"] = proventos["movimentacao"].map(classificar_tipo_provento)
    resumo = proventos.groupby(["mes", "tipo_provento"], as_index=False)["valor_liquido"].sum()
    resumo["mes"] = pd.to_datetime(resumo["mes"].astype(str) + "-01")
    resumo["valor_liquido"] = resumo["valor_liquido"].clip(lower=0)
    return resumo


def build_calendario_proventos(df: pd.DataFrame | None) -> pd.DataFrame:
    """Retorna tabela granular de proventos recebidos: uma linha por evento de crédito.

    Colunas: data | ativo | tipo_provento | valor_liquido
    Ordenada por data descendente (mais recente no topo).
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=_COLUNAS_CALENDARIO)

    mask = df.apply(
        lambda row: bool(efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida")).provento)
        and is_credito(row.get("entrada_saida")),
        axis=1,
    )
    proventos = df.loc[mask].copy()

    if proventos.empty:
        return pd.DataFrame(columns=_COLUNAS_CALENDARIO)

    proventos["tipo_provento"] = proventos["movimentacao"].map(classificar_tipo_provento)

    # Coluna de ativo: preferir "ticker" se existir, senão "produto"
    col_ativo = "ticker" if "ticker" in proventos.columns else "produto"
    proventos["ativo"] = proventos[col_ativo].astype(str).str.strip()

    proventos["valor_liquido"] = pd.to_numeric(proventos["valor_liquido"], errors="coerce").clip(lower=0).fillna(0.0)

    cal = proventos[["data", "ativo", "tipo_provento", "valor_liquido"]].copy()
    if pd.api.types.is_datetime64_any_dtype(cal["data"]):
        cal = cal.sort_values("data", ascending=False).reset_index(drop=True)
    return cal
