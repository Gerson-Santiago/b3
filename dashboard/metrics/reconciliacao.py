from __future__ import annotations

import re
from typing import Any

import pandas as pd

from dashboard.models.ativos import resolver_ativo_seguro
from dashboard.models.eventos import aplicar_eventos_ordenados


def _normalizar_qtd_df(df: Any, *, nome: str = "qtd") -> pd.DataFrame:
    if df is None:
        return pd.DataFrame(columns=["ativo_id", "ativo", "quantidade"])

    if isinstance(df, dict):
        payload = pd.DataFrame({"produto": list(df.keys()), "quantidade": list(df.values())})
    elif isinstance(df, pd.Series):
        payload = df.reset_index()
        payload.columns = ["produto", "quantidade"]
    elif isinstance(df, pd.DataFrame):
        payload = df.copy()
    else:
        raise TypeError(f"Tipo não suportado para {nome}: {type(df)!r}")

    col_prod = None
    for candidate in ["ativo_id", "produto", "ativo", "ticker"]:
        if candidate in payload.columns:
            col_prod = candidate
            break

    if col_prod is None:
        raise ValueError(f"DataFrame de {nome} sem coluna 'produto' ou 'ativo'.")

    if "quantidade" not in payload.columns:
        for coluna in ["qtd", "qtd_liquida", "qtd_pos", "posicao"]:
            if coluna in payload.columns:
                payload = payload.rename(columns={coluna: "quantidade"})
                break

    if "ativo_id" not in payload.columns:
        payload["ativo_id"] = payload[col_prod].map(resolver_ativo_seguro)

    payload["ativo"] = payload["ativo_id"].apply(lambda a: a.codigo if hasattr(a, "codigo") else str(a))
    payload["quantidade"] = pd.to_numeric(payload["quantidade"], errors="coerce").fillna(0.0)
    return payload[["ativo_id", "ativo", "quantidade"]].copy()


def quantidade_ate(mov_df, data_corte, inclusive: bool = True, aplicar_define: bool = True):
    if mov_df is None or mov_df.empty:
        return {}

    base = mov_df.copy()
    if "data" in base.columns:
        base["data"] = pd.to_datetime(base["data"], errors="coerce")
        limite = pd.Timestamp(data_corte)
        if inclusive:
            base = base[base["data"] <= limite]
        else:
            base = base[base["data"] < limite]

    resumo = aplicar_eventos_ordenados(base, aplicar_define=aplicar_define)
    if resumo.empty:
        return {}

    total = resumo.groupby("ativo_id", as_index=False)["quantidade"].sum()
    return {
        aid.codigo if hasattr(aid, "codigo") else str(aid): qtd
        for aid, qtd in zip(total["ativo_id"], total["quantidade"])
    }


def comparar(qtd_mov, pos_df, mov_df=None, data_corte=None):
    mov = _normalizar_qtd_df(qtd_mov, nome="movimentação")
    pos = _normalizar_qtd_df(pos_df, nome="posição")

    mov_agg = mov.groupby("ativo_id", as_index=False)["quantidade"].sum()
    pos_agg = pos.groupby("ativo_id", as_index=False)["quantidade"].sum()
    tabela = mov_agg.merge(pos_agg, on="ativo_id", how="outer")
    tabela = tabela.rename(columns={"quantidade_x": "qtd_mov", "quantidade_y": "qtd_pos"})
    tabela["qtd_mov"] = pd.to_numeric(tabela["qtd_mov"], errors="coerce").fillna(0.0)
    tabela["qtd_pos"] = pd.to_numeric(tabela["qtd_pos"], errors="coerce").fillna(0.0)
    tabela["delta"] = tabela["qtd_pos"] - tabela["qtd_mov"]
    tabela["ativo"] = tabela["ativo_id"].apply(lambda a: a.codigo if hasattr(a, "codigo") else str(a))
    tabela = tabela[["ativo", "qtd_mov", "qtd_pos", "delta"]].copy()

    if mov_df is not None:
        corte = data_corte if data_corte is not None else "2099-12-31"
        qtd_sem_define = quantidade_ate(mov_df, corte, aplicar_define=False)
        tabela["observacao"] = tabela.apply(
            lambda r: "ajuste por atualização"
            if abs(qtd_sem_define.get(r["ativo"], r["qtd_mov"]) - r["qtd_mov"]) > 1e-4
            else "",
            axis=1,
        )

    return tabela.sort_values("ativo", kind="mergesort").reset_index(drop=True)


def data_do_arquivo(nome):
    text = str(nome or "")
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match is None:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
