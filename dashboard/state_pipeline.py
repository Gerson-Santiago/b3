"""Cálculos derivados do DashboardState — posição, cards e curvas por categoria."""
from __future__ import annotations

from datetime import date

import pandas as pd

from dashboard.filters import filtrar_dataframe
from dashboard.metrics.evolucao import compute_evolucao_separada
from dashboard.metrics.position import classificar_ativo_por_mapa, compute_position, obter_mapa_categorias
from dashboard.metrics.preco_medio import compute_preco_medio
from dashboard.models.ativos import resolver_ativo_seguro
from dashboard.models.categorias import CATEGORIA_TESOURO, CATEGORIAS_BOLSA, agrupar_bolsa
from dashboard.models.eventos import aplicar_eventos_ordenados

_COLUNAS_POS_VAZIA = ["produto", "quantidade", "valor", "valor_abs", "categoria"]
_COLUNAS_POS_CATEGORIA = ["categoria", "valor", "quantidade"]
_COLUNAS_CARDS_VAZIA = [
    "produto",
    "categoria",
    "quantidade",
    "valor_abs",
    "preco_medio",
    "custo_total",
    "pl",
    "variacao_pct",
    "peso_pct",
]


def movimentacao_ate_end_date(
    mov_df: pd.DataFrame | None,
    mov_filtered: pd.DataFrame,
    end_date: date,
    produtos_selecionados: list[str] | None,
    instituicoes_selecionadas: list[str] | None,
) -> pd.DataFrame:
    if mov_df is not None and not mov_df.empty:
        return filtrar_dataframe(
            mov_df,
            instituicoes=instituicoes_selecionadas or [],
            produtos=produtos_selecionados or [],
            start_date=None,
            end_date=end_date,
        )
    return mov_filtered


def consolidar_posicao(
    pos_filtered: pd.DataFrame,
    mov_ate_end_date: pd.DataFrame,
    mapa_cat: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not pos_filtered.empty:
        pos = compute_position(pos_filtered)
    else:
        resumo_mov = aplicar_eventos_ordenados(mov_ate_end_date)
        if not resumo_mov.empty:
            pos = resumo_mov[resumo_mov["quantidade"].abs() > 0].copy()
            pos["valor"] = pos["custo_total"].round(2)
            pos["valor_abs"] = pos["valor"].abs().round(2)
        else:
            pos = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs"])

    if pos.empty:
        return (
            pd.DataFrame(columns=_COLUNAS_POS_VAZIA),
            pd.DataFrame(columns=_COLUNAS_POS_CATEGORIA),
        )

    pos = pos.copy()
    pos["categoria"] = pos["produto"].apply(lambda p: classificar_ativo_por_mapa(p, mapa_cat))
    pos_categoria = (
        pos.groupby("categoria", as_index=False)
        .agg(valor=("valor_abs", "sum"), quantidade=("quantidade", "sum"))
        .sort_values("valor", ascending=False)
    )
    return pos, pos_categoria


def enriquecer_pos_cards(pos: pd.DataFrame, pm_df: pd.DataFrame) -> pd.DataFrame:
    """Junta pos (valor atual) com preco_medio/custo_total e deriva pl/variacao_pct."""
    if pos.empty:
        return pd.DataFrame(columns=_COLUNAS_CARDS_VAZIA)

    cards = pos.copy()
    colunas_base = [c for c in ["produto", "categoria", "quantidade", "valor_abs"] if c in cards.columns]
    cards = cards[colunas_base].copy()

    if not pm_df.empty:
        if "ativo_id" in pos.columns:
            cards["_join_key"] = pos["ativo_id"]
        else:
            cards["_join_key"] = cards["produto"].map(resolver_ativo_seguro)

        if "ativo_id" in pm_df.columns:
            pm = pm_df[["ativo_id", "preco_medio", "custo_total"]].copy()
            pm = pm.rename(columns={"ativo_id": "_join_key"})
        else:
            pm = pm_df[["produto", "preco_medio", "custo_total"]].copy()
            pm["_join_key"] = pm["produto"].map(resolver_ativo_seguro)
            pm = pm.drop(columns=["produto"])

        cards = cards.merge(pm, on="_join_key", how="left").drop(columns=["_join_key"])
    else:
        cards["preco_medio"] = float("nan")
        cards["custo_total"] = float("nan")

    cards["preco_medio"] = pd.to_numeric(cards["preco_medio"], errors="coerce").fillna(0.0)
    cards["custo_total"] = pd.to_numeric(cards["custo_total"], errors="coerce").fillna(0.0)
    cards["pl"] = (cards["valor_abs"] - cards["custo_total"]).round(2)
    cards["variacao_pct"] = cards.apply(
        lambda r: round((r["pl"] / r["custo_total"]) * 100, 2) if r["custo_total"] else 0.0,
        axis=1,
    )
    total_patrimonio = float(cards["valor_abs"].sum())
    if total_patrimonio > 0:
        cards["peso_pct"] = (cards["valor_abs"] / total_patrimonio * 100).round(2)
    else:
        cards["peso_pct"] = 0.0
    return cards.sort_values("valor_abs", ascending=False).reset_index(drop=True)


def filtrar_mov_por_categorias(
    mov_filtered: pd.DataFrame,
    mapa_cat: dict[str, str],
    categorias: set[str],
) -> pd.DataFrame:
    if mov_filtered.empty or not mapa_cat or "produto" not in mov_filtered.columns:
        return mov_filtered.iloc[0:0]
    alvos = {c.upper() for c in categorias}
    mask = mov_filtered["produto"].apply(
        lambda p: str(mapa_cat.get(str(p or "").strip(), "")).upper() in alvos
    )
    return mov_filtered[mask]


def filtrar_pos_por_categorias(
    pos_frames: list[pd.DataFrame],
    categorias: set[str],
) -> list[pd.DataFrame]:
    alvos = {c.upper() for c in categorias}
    resultado = []
    for frame in pos_frames:
        if frame is None or frame.empty or "categoria" not in frame.columns:
            continue
        filtrado = frame[frame["categoria"].str.upper().isin(alvos)]
        if not filtrado.empty:
            resultado.append(filtrado)
    return resultado


def curvas_segmentadas(
    mov_filtered: pd.DataFrame,
    pos_frames: list[pd.DataFrame],
    mapa_cat: dict[str, str],
) -> tuple[dict, dict, dict]:
    evol_dict = compute_evolucao_separada(mov_filtered, pos_frames)
    evol_bolsa = compute_evolucao_separada(
        filtrar_mov_por_categorias(mov_filtered, mapa_cat, set(CATEGORIAS_BOLSA)),
        filtrar_pos_por_categorias(pos_frames, set(CATEGORIAS_BOLSA)),
    )
    evol_tesouro = compute_evolucao_separada(
        filtrar_mov_por_categorias(mov_filtered, mapa_cat, {CATEGORIA_TESOURO}),
        filtrar_pos_por_categorias(pos_frames, {CATEGORIA_TESOURO}),
    )
    return evol_dict, evol_bolsa, evol_tesouro


def montar_derivados(
    *,
    pos_df: pd.DataFrame,
    mov_filtered: pd.DataFrame,
    pos_filtered: pd.DataFrame,
    end_date: date,
    mov_df: pd.DataFrame | None,
    produtos_selecionados: list[str] | None,
    instituicoes_selecionadas: list[str] | None,
) -> dict:
    mapa_cat = obter_mapa_categorias(pos_df) if not pos_df.empty else {}
    mov_ate = movimentacao_ate_end_date(
        mov_df, mov_filtered, end_date, produtos_selecionados, instituicoes_selecionadas
    )
    pos, pos_categoria = consolidar_posicao(pos_filtered, mov_ate, mapa_cat)
    pos_cards = enriquecer_pos_cards(pos, compute_preco_medio(mov_ate))
    pos_frames = [pos_df] if not pos_df.empty else []
    evol_dict, evol_bolsa, evol_tesouro = curvas_segmentadas(mov_filtered, pos_frames, mapa_cat)
    return {
        "pos": pos,
        "pos_categoria": pos_categoria,
        "pos_categoria_agrupada": agrupar_bolsa(pos_categoria),
        "pos_cards": pos_cards,
        "evol_dict": evol_dict,
        "evol_bolsa": evol_bolsa,
        "evol_tesouro": evol_tesouro,
    }
