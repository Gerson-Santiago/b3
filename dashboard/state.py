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
    from dashboard.metrics.proventos import compute_proventos
except ImportError:  # pragma: no cover
    from metrics.dy import compute_dy_metrics
    from metrics.evolucao import compute_evolucao_separada
    from metrics.position import classificar_ativo_por_mapa, compute_position, obter_mapa_categorias
    from metrics.proventos import compute_proventos

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
    # DataFrames filtrados preservados para as views
    mov_filtered: pd.DataFrame
    pos_filtered: pd.DataFrame
    # Métricas calculadas
    proventos: pd.DataFrame
    evol_dict: dict
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

        proventos = compute_proventos(mov_filtered)
        evol_dict = compute_evolucao_separada(
            mov_filtered, [pos_df] if not pos_df.empty else []
        )
        dy_metrics = compute_dy_metrics(mov_filtered, pos_df, data_referencia=end_date)

        return cls(
            pos=pos,
            pos_categoria=pos_categoria,
            pos_categoria_agrupada=pos_categoria_agrupada,
            mov_filtered=mov_filtered,
            pos_filtered=pos_filtered,
            proventos=proventos,
            evol_dict=evol_dict,
            dy_metrics=dy_metrics,
        )
