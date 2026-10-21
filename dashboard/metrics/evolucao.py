from __future__ import annotations

from typing import Sequence
import pandas as pd


def compute_curva_aportes(mov_df: pd.DataFrame) -> pd.DataFrame:
    if mov_df is None or mov_df.empty:
        return pd.DataFrame(columns=["data", "aporte_periodo", "custo_acumulado"])

    df = mov_df.copy()
    if "data" not in df.columns:
        return pd.DataFrame(columns=["data", "aporte_periodo", "custo_acumulado"])

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"]).sort_values("data")

    # Considerar apenas operações financeiras de compra/venda/transferencia/liquidacao
    if "valor_liquido" not in df.columns:
        df["valor_liquido"] = df.get("valor_operacao", 0.0)
    df["valor_liquido"] = pd.to_numeric(df["valor_liquido"], errors="coerce").fillna(0.0)

    # Identificar entradas/saídas operacionais de capital
    def _sinal_operacao(row):
        es = str(row.get("entrada_saida") or "").strip().lower()
        mov = str(row.get("movimentacao") or "").strip().lower()
        if any(term in mov for term in ["dividendo", "juros", "rendimento"]):
            return 0.0  # Proventos não são novo aporte externo de capital
        if "debito" in es or "débito" in es:
            return -1.0
        return 1.0

    df["sinal"] = df.apply(_sinal_operacao, axis=1)
    df["fluxo_aporte"] = df["valor_liquido"].abs() * df["sinal"]

    df["data_periodo"] = df["data"].dt.normalize()
    aportes = (
        df.groupby("data_periodo", as_index=False)["fluxo_aporte"]
        .sum()
        .rename(columns={"data_periodo": "data", "fluxo_aporte": "aporte_periodo"})
    )
    aportes["custo_acumulado"] = aportes["aporte_periodo"].cumsum()
    return aportes


def compute_curva_patrimonio(pos_frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
    if not pos_frames:
        return pd.DataFrame(columns=["data", "patrimonio_liquido"])

    pontos = []
    for pos in pos_frames:
        if pos is None or pos.empty:
            continue
        dt = None
        if "data" in pos.columns:
            dts = pd.to_datetime(pos["data"], errors="coerce").dropna()
            if not dts.empty:
                dt = dts.iloc[0].normalize()
        if dt is None and "data_posicao" in pos.columns:
            dts = pd.to_datetime(pos["data_posicao"], errors="coerce").dropna()
            if not dts.empty:
                dt = dts.iloc[0].normalize()
        if dt is None:
            continue

        col_val = "valor_atualizado" if "valor_atualizado" in pos.columns else ("valor_operacao" if "valor_operacao" in pos.columns else "valor_liquido")
        val = pd.to_numeric(pos[col_val], errors="coerce").fillna(0.0).sum()
        pontos.append({"data": dt, "patrimonio_liquido": round(float(val), 2)})

    if not pontos:
        return pd.DataFrame(columns=["data", "patrimonio_liquido"])

    df_pat = pd.DataFrame(pontos).drop_duplicates(subset=["data"]).sort_values("data").reset_index(drop=True)
    return df_pat


def compute_evolucao_separada(mov_df: pd.DataFrame, pos_frames: Sequence[pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    aportes = compute_curva_aportes(mov_df)
    patrimonio = compute_curva_patrimonio(pos_frames or [])
    return {
        "curva_aportes": aportes,
        "curva_patrimonio": patrimonio,
    }


def compute_evolucao(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["data", "patrimonio"])

    evol = df.groupby("data", as_index=False)["valor_liquido"].sum()
    evol["patrimonio"] = evol["valor_liquido"].cumsum()
    return evol
