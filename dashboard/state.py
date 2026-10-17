"""Fonte Única da Verdade (SSOT) dos dados calculados do Dashboard B3.

``DashboardState`` agrega todos os DataFrames derivados produzidos a partir
dos arquivos brutos. As views recebem apenas um ``DashboardState`` — nenhuma
lógica de negócio é recalculada ou duplicada na camada de apresentação.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from dashboard.metrics.dy import compute_dy_metrics
from dashboard.metrics.proventos import compute_proventos
from dashboard.models.qualidade import RelatorioQualidade
from dashboard.state_pipeline import enriquecer_pos_cards, montar_derivados

# Reexportado para testes que importam o helper puro.
_enriquecer_pos_cards = enriquecer_pos_cards


@dataclass
class DashboardState:
    """Contém todos os dados derivados usados pelas views.

    Instancie sempre via :meth:`build` — nunca diretamente.
    """

    pos: pd.DataFrame
    pos_categoria: pd.DataFrame
    pos_categoria_agrupada: pd.DataFrame
    pos_cards: pd.DataFrame
    mov_filtered: pd.DataFrame
    pos_filtered: pd.DataFrame
    proventos: pd.DataFrame
    evol_dict: dict
    evol_bolsa: dict
    evol_tesouro: dict
    dy_metrics: pd.DataFrame
    qualidade: RelatorioQualidade = field(default_factory=RelatorioQualidade)

    @classmethod
    def build(
        cls,
        *,
        pos_df: pd.DataFrame,
        mov_filtered: pd.DataFrame,
        pos_filtered: pd.DataFrame,
        end_date: date,
        mov_df: pd.DataFrame | None = None,
        produtos_selecionados: list[str] | None = None,
        instituicoes_selecionadas: list[str] | None = None,
        qualidade: RelatorioQualidade | None = None,
    ) -> "DashboardState":
        """Calcula todos os dados derivados e retorna um ``DashboardState``."""
        derivados = montar_derivados(
            pos_df=pos_df,
            mov_filtered=mov_filtered,
            pos_filtered=pos_filtered,
            end_date=end_date,
            mov_df=mov_df,
            produtos_selecionados=produtos_selecionados,
            instituicoes_selecionadas=instituicoes_selecionadas,
        )
        return cls(
            **derivados,
            mov_filtered=mov_filtered,
            pos_filtered=pos_filtered,
            proventos=compute_proventos(mov_filtered),
            dy_metrics=compute_dy_metrics(mov_filtered, pos_df, data_referencia=end_date),
            qualidade=qualidade if qualidade is not None else RelatorioQualidade(),
        )
