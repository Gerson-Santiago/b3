from __future__ import annotations

import re
from typing import Any

import pandas as pd

from dashboard.models.ativos import renomear_ativo
from dashboard.models.eventos import aplicar_eventos_ordenados


def _normalizar_ativo(valor: Any) -> str:
    return renomear_ativo(valor)


def _normalizar_qtd_df(df: Any, *, nome: str = "qtd") -> pd.DataFrame:
    if df is None:
        return pd.DataFrame(columns=["produto", "quantidade"])

    if isinstance(df, dict):
        payload = pd.DataFrame({"produto": list(df.keys()), "quantidade": list(df.values())})
    elif isinstance(df, pd.Series):
        payload = df.reset_index()
        payload.columns = ["produto", "quantidade"]
    elif isinstance(df, pd.DataFrame):
        payload = df.copy()
    else:
        raise TypeError(f"Tipo não suportado para {nome}: {type(df)!r}")

    if "produto" not in payload.columns:
        if "ativo" in payload.columns:
            payload = payload.rename(columns={"ativo": "produto"})
        elif "ticker" in payload.columns:
            payload = payload.rename(columns={"ticker": "produto"})
        else:
            raise ValueError(f"DataFrame de {nome} sem coluna 'produto' ou 'ativo'.")

    if "quantidade" not in payload.columns:
        for coluna in ["qtd", "qtd_liquida", "qtd_pos", "posicao"]:
            if coluna in payload.columns:
                payload = payload.rename(columns={coluna: "quantidade"})
                break

    payload = payload[["produto", "quantidade"]].copy()
    payload["produto"] = payload["produto"].map(_normalizar_ativo)
    payload["quantidade"] = pd.to_numeric(payload["quantidade"], errors="coerce").fillna(0.0)
    return payload


def quantidade_ate(mov_df, data_corte, inclusive: bool = True):
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

    resumo = aplicar_eventos_ordenados(base)
    if resumo.empty:
        return {}

    total = resumo[["produto", "quantidade"]].copy()
    total["produto"] = total["produto"].map(_normalizar_ativo)
    total = total.groupby("produto", as_index=False)["quantidade"].sum()
    return dict(zip(total["produto"], total["quantidade"]))


def comparar(qtd_mov, pos_df):
    mov = _normalizar_qtd_df(qtd_mov, nome="movimentação")
    pos = _normalizar_qtd_df(pos_df, nome="posição")

    mov_agg = mov.groupby("produto", as_index=False)["quantidade"].sum()
    pos_agg = pos.groupby("produto", as_index=False)["quantidade"].sum()
    tabela = mov_agg.merge(pos_agg, on="produto", how="outer")
    tabela = tabela.rename(columns={"quantidade_x": "qtd_mov", "quantidade_y": "qtd_pos"})
    tabela["qtd_mov"] = tabela["qtd_mov"].fillna(0.0)
    tabela["qtd_pos"] = tabela["qtd_pos"].fillna(0.0)
    tabela["delta"] = tabela["qtd_pos"] - tabela["qtd_mov"]
    tabela = tabela[["produto", "qtd_mov", "qtd_pos", "delta"]].rename(columns={"produto": "ativo"})
    tabela["qtd_mov"] = pd.to_numeric(tabela["qtd_mov"], errors="coerce").fillna(0.0)
    tabela["qtd_pos"] = pd.to_numeric(tabela["qtd_pos"], errors="coerce").fillna(0.0)
    tabela["delta"] = pd.to_numeric(tabela["delta"], errors="coerce").fillna(0.0)
    return tabela.sort_values("ativo", kind="mergesort").reset_index(drop=True)


def data_do_arquivo(nome):
    text = str(nome or "")
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match is None:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
