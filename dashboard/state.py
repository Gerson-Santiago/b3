"""Fonte Única da Verdade (SSOT) dos dados calculados do Dashboard B3.

``DashboardState`` agrega todos os DataFrames derivados produzidos a partir
dos arquivos brutos. As views recebem apenas um ``DashboardState`` — nenhuma
lógica de negócio é recalculada ou duplicada na camada de apresentação.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

try:
    from dashboard.metrics.dy import compute_dy_metrics
    from dashboard.metrics.evolucao import compute_evolucao_separada
    from dashboard.metrics.position import classificar_ativo_por_mapa, compute_position, obter_mapa_categorias
    from dashboard.metrics.preco_medio import compute_preco_medio
    from dashboard.metrics.proventos import compute_proventos
    from dashboard.models.ativos import renomear_ativo
except ImportError:  # pragma: no cover
    from metrics.dy import compute_dy_metrics
    from metrics.evolucao import compute_evolucao_separada
    from metrics.position import classificar_ativo_por_mapa, compute_position, obter_mapa_categorias
    from metrics.preco_medio import compute_preco_medio
    from metrics.proventos import compute_proventos
    from models.ativos import renomear_ativo

# Categorias que compõem "Bolsa de Valores" no gráfico agrupado
_CATEGORIAS_BOLSA = {"AÇÕES", "BDR"}
_LABEL_BOLSA = "Bolsa de Valores"


def _agrupar_bolsa(pos_categoria: pd.DataFrame) -> pd.DataFrame:
    """Agrupa AÇÕES e BDR em 'Bolsa de Valores' — SSOT do agrupamento."""
    if pos_categoria.empty:
        return pos_categoria.copy()

    agrupada = pos_categoria.copy()
    agrupada["categoria"] = agrupada["categoria"].replace(
        {cat: _LABEL_BOLSA for cat in _CATEGORIAS_BOLSA}
    )
    return (
        agrupada.groupby("categoria", as_index=False)
        .agg(valor=("valor", "sum"), quantidade=("quantidade", "sum"))
        .sort_values("valor", ascending=False)
    )


def _enriquecer_pos_cards(pos: pd.DataFrame, pm_df: pd.DataFrame) -> pd.DataFrame:
    """Junta pos (valor atual do snapshot) com preco_medio/custo_total e deriva pl/variacao_pct.

    O join é feito via ticker normalizado (renomear_ativo) porque pos.produto contém
    o nome completo ("PETR4 - PETROBRAS") enquanto pm_df.produto contém o ticker
    ("PETR4") — mesma lógica de normalização de eventos.py.
    """
    if pos.empty:
        return pd.DataFrame(columns=["produto", "categoria", "quantidade", "valor_abs",
                                     "preco_medio", "custo_total", "pl", "variacao_pct"])

    cards = pos[["produto", "categoria", "quantidade", "valor_abs"]].copy()

    if not pm_df.empty:
        # Chave de join: ticker normalizado dos dois lados
        cards["_ticker"] = cards["produto"].apply(lambda p: renomear_ativo(p) or str(p).strip())
        pm = pm_df[["produto", "preco_medio", "custo_total"]].copy()
        pm = pm.rename(columns={"produto": "_ticker"})
        cards = cards.merge(pm, on="_ticker", how="left").drop(columns=["_ticker"])
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
    return cards.sort_values("valor_abs", ascending=False).reset_index(drop=True)


@dataclass
class DashboardState:
    """Contém todos os dados derivados usados pelas views.

    Instancie sempre via :meth:`build` — nunca diretamente.
    """

    # Posição consolidada com coluna ``categoria``
    pos: pd.DataFrame
    # Alocação por categoria granular (AÇÕES e BDR separados)
    pos_categoria: pd.DataFrame
    # Alocação agrupada (BDR + AÇÕES → "Bolsa de Valores") — SSOT
    pos_categoria_agrupada: pd.DataFrame
    # pos enriquecida com preco_medio, custo_total, pl e variacao_pct
    pos_cards: pd.DataFrame
    # DataFrames filtrados preservados para as views
    mov_filtered: pd.DataFrame
    pos_filtered: pd.DataFrame
    # Métricas calculadas
    proventos: pd.DataFrame
    # Curva consolidada (Bolsa + Tesouro)
    evol_dict: dict
    # Curvas segmentadas por produto — mesma estrutura de evol_dict
    evol_bolsa: dict
    evol_tesouro: dict
    dy_metrics: pd.DataFrame

    # ------------------------------------------------------------------
    # Factory method
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        *,
        pos_df: pd.DataFrame,
        mov_filtered: pd.DataFrame,
        pos_filtered: pd.DataFrame,
        end_date: date,
    ) -> "DashboardState":
        """Calcula todos os dados derivados e retorna um ``DashboardState``.

        Parameters
        ----------
        pos_df:
            Snapshot de posição completo (sem filtros de sidebar), usado
            como SSOT do mapa de categorias e para cálculo de DY.
        mov_filtered:
            Movimentações já filtradas pelos filtros de sidebar.
        pos_filtered:
            Posição já filtrada pelos filtros de sidebar.
        end_date:
            Data de corte para cálculo de métricas de DY.
        """
        # SSOT do mapa de categorias — sempre vem do pos_df sem filtro
        mapa_cat = obter_mapa_categorias(pos_df) if not pos_df.empty else {}

        # Posição consolidada
        base_pos = pos_filtered if not pos_filtered.empty else mov_filtered
        pos = compute_position(base_pos)
        if not pos.empty:
            pos = pos.copy()
            pos["categoria"] = pos["produto"].apply(
                lambda p: classificar_ativo_por_mapa(p, mapa_cat)
            )
            pos_categoria = (
                pos.groupby("categoria", as_index=False)
                .agg(valor=("valor_abs", "sum"), quantidade=("quantidade", "sum"))
                .sort_values("valor", ascending=False)
            )
        else:
            pos = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
            pos_categoria = pd.DataFrame(columns=["categoria", "valor", "quantidade"])

        pos_categoria_agrupada = _agrupar_bolsa(pos_categoria)

        # pos_cards: enriquece pos com preco_medio/custo_total/pl/variacao_pct
        pm_df = compute_preco_medio(mov_filtered)
        pos_cards = _enriquecer_pos_cards(pos, pm_df)

        proventos = compute_proventos(mov_filtered)

        pos_frames = [pos_df] if not pos_df.empty else []

        # Consolidado — mesmo padrão já existente
        evol_dict = compute_evolucao_separada(mov_filtered, pos_frames)

        # Segmentado por produto: filtra mov_filtered pela categoria via mapa_cat
        def _filtrar_mov(categorias: set[str]) -> pd.DataFrame:
            if mov_filtered.empty or not mapa_cat or "produto" not in mov_filtered.columns:
                return mov_filtered.iloc[0:0]  # DataFrame vazio com mesmas colunas
            mask = mov_filtered["produto"].apply(
                lambda p: str(mapa_cat.get(str(p or "").strip(), "")).upper()
                in {c.upper() for c in categorias}
            )
            return mov_filtered[mask]

        def _filtrar_pos(categorias: set[str]) -> list[pd.DataFrame]:
            resultado = []
            for frame in pos_frames:
                if frame is None or frame.empty or "categoria" not in frame.columns:
                    continue
                filtrado = frame[frame["categoria"].str.upper().isin({c.upper() for c in categorias})]
                if not filtrado.empty:
                    resultado.append(filtrado)
            return resultado

        evol_bolsa = compute_evolucao_separada(
            _filtrar_mov(_CATEGORIAS_BOLSA), _filtrar_pos(_CATEGORIAS_BOLSA)
        )
        evol_tesouro = compute_evolucao_separada(
            _filtrar_mov({"TESOURO"}), _filtrar_pos({"TESOURO"})
        )

        dy_metrics = compute_dy_metrics(mov_filtered, pos_df, data_referencia=end_date)

        return cls(
            pos=pos,
            pos_categoria=pos_categoria,
            pos_categoria_agrupada=pos_categoria_agrupada,
            pos_cards=pos_cards,
            mov_filtered=mov_filtered,
            pos_filtered=pos_filtered,
            proventos=proventos,
            evol_dict=evol_dict,
            evol_bolsa=evol_bolsa,
            evol_tesouro=evol_tesouro,
            dy_metrics=dy_metrics,
        )
