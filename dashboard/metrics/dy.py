from datetime import timedelta
import pandas as pd

from dashboard.metrics.preco_medio import compute_preco_medio
from dashboard.models.ativos import resolver_ativo_seguro
from dashboard.models.eventos import efeito_movimentacao
from dashboard.models.movimentacao import is_credito
from .position import compute_position


def _extrair_codigo_ativo(df: pd.DataFrame) -> pd.Series:
    if "ativo" in df.columns:
        return df["ativo"]
    if "ativo_id" in df.columns:
        return df["ativo_id"].apply(lambda a: a.codigo if hasattr(a, "codigo") else str(a))
    return df["produto"].map(lambda p: resolver_ativo_seguro(p).codigo)


def compute_dy_metrics(mov_df: pd.DataFrame, pos_df: pd.DataFrame | None = None, data_referencia: object = None) -> pd.DataFrame:
    if mov_df is None or mov_df.empty:
        return pd.DataFrame(columns=["ticker", "produto", "valor_atual", "custo_total", "proventos_12m", "dy_ltm_pct", "yield_on_cost_pct"])

    df = mov_df.copy()
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    else:
        df["data"] = pd.NaT

    datas_validas = df["data"].dropna()
    if data_referencia is not None:
        ref_dt = pd.Timestamp(data_referencia)
        limite_12m = ref_dt - timedelta(days=365)
        df_12m = df[(df["data"] >= limite_12m) & (df["data"] <= ref_dt)].copy()
    elif not datas_validas.empty:
        ref_dt = datas_validas.max()
        limite_12m = ref_dt - timedelta(days=365)
        df_12m = df[(df["data"] >= limite_12m) & (df["data"] <= ref_dt)].copy()
    else:
        df_12m = df.copy()

    # Proventos creditados nos últimos 12 meses
    proventos = df_12m.loc[
        df_12m.apply(
            lambda row: bool(efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida")).provento)
            and is_credito(row.get("entrada_saida")),
            axis=1,
        )
    ].copy()

    proventos["ticker"] = _extrair_codigo_ativo(proventos)
    prov_12m = proventos.groupby("ticker", as_index=False)["valor_liquido"].sum().rename(columns={"valor_liquido": "proventos_12m"})

    # Custo total calculado via preco_medio
    pm_df = compute_preco_medio(df)
    pm_df["ticker"] = _extrair_codigo_ativo(pm_df)
    custos = pm_df.groupby("ticker", as_index=False).agg(
        quantidade=("quantidade", "sum"),
        custo_total=("custo_total", "sum"),
    )

    # Valor atual vindo da posição real se disponível, senão compute_position(df) ou custo
    if pos_df is not None and not pos_df.empty:
        pos_base = pos_df.copy()
        pos_base["ticker"] = _extrair_codigo_ativo(pos_base)
        col_val = next((c for c in ["valor_atualizado", "valor_operacao", "valor_liquido", "valor"] if c in pos_base.columns), None)
        if col_val is not None:
            val_pos = pos_base.groupby("ticker", as_index=False)[col_val].sum().rename(columns={col_val: "valor_atual"})
        else:
            val_pos = pd.DataFrame(columns=["ticker", "valor_atual"])
    else:
        pos_mov = compute_position(df)
        if not pos_mov.empty:
            pos_mov["ticker"] = _extrair_codigo_ativo(pos_mov)
            val_pos = pos_mov.groupby("ticker", as_index=False)["valor_abs"].sum().rename(columns={"valor_abs": "valor_atual"})
        else:
            val_pos = pd.DataFrame(columns=["ticker", "valor_atual"])

    res = custos.merge(val_pos, on="ticker", how="outer").merge(prov_12m, on="ticker", how="outer")
    res["quantidade"] = res["quantidade"].fillna(0.0)
    res["custo_total"] = res["custo_total"].fillna(0.0)
    res["valor_atual"] = res["valor_atual"].fillna(res["custo_total"])
    res["proventos_12m"] = res["proventos_12m"].fillna(0.0)

    # Filtrar ativos com alguma relevância (quantidade > 0, valor_atual > 0 ou provento recebido)
    res = res[(res["quantidade"] > 0) | (res["valor_atual"] > 0) | (res["proventos_12m"] > 0)].copy()

    # Cálculo seguro das taxas percentuais
    def calc_pct(num, den):
        if pd.isna(den) or den <= 0:
            return 0.0
        return float((num / den) * 100.0)

    res["dy_ltm_pct"] = [calc_pct(n, d) for n, d in zip(res["proventos_12m"], res["valor_atual"])]
    res["yield_on_cost_pct"] = [calc_pct(n, d) for n, d in zip(res["proventos_12m"], res["custo_total"])]
    res["dy_pct"] = res["dy_ltm_pct"]
    res["produto"] = res["ticker"]

    return res.sort_values("dy_ltm_pct", ascending=False).reset_index(drop=True)


def compute_dy(df, pos_df: pd.DataFrame | None = None):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "valor_abs", "provento_total", "dy_pct"])

    metrics = compute_dy_metrics(df, pos_df)
    metrics["valor_abs"] = metrics["valor_atual"]
    metrics["provento_total"] = metrics["proventos_12m"]
    return metrics[["produto", "valor_abs", "provento_total", "dy_pct", "dy_ltm_pct", "yield_on_cost_pct"]]
