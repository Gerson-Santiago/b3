"""Modelos e cálculos de resumo consolidado da carteira (SSoT)."""
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from dashboard.models.categorias import (
    CATEGORIA_TESOURO,
    CATEGORIAS_BOLSA,
    LABEL_BOLSA,
    LABEL_TESOURO,
)


@dataclass(frozen=True)
class ResumoMacro:
    """Subtotal consolidado de um grande grupo macro (Bolsa de Valores ou Tesouro Direto)."""

    nome: str
    patrimonio: float = 0.0
    custo: float = 0.0
    pl: float = 0.0
    pl_pct: float = 0.0
    peso_pct: float = 0.0


@dataclass(frozen=True)
class ResumoCarteira:
    """Métricas agregadas da carteira completa e de suas divisões macro."""

    patrimonio_total: float = 0.0
    custo_total: float = 0.0
    pl_total: float = 0.0
    pl_pct: float = 0.0
    proventos_total: float = 0.0
    bolsa: ResumoMacro = ResumoMacro(nome=LABEL_BOLSA)
    tesouro: ResumoMacro = ResumoMacro(nome=LABEL_TESOURO)


# Alias para retrocompatibilidade semântica
ResumoAlocacao = ResumoCarteira


def _calcular_macro(
    df_cards: pd.DataFrame,
    nome: str,
    filtro_categorias: set[str] | frozenset[str],
    patrimonio_total: float,
) -> ResumoMacro:
    if df_cards.empty or "categoria" not in df_cards.columns:
        return ResumoMacro(nome=nome)

    mask = df_cards["categoria"].astype(str).str.upper().isin({c.upper() for c in filtro_categorias})
    sub = df_cards[mask]
    if sub.empty:
        return ResumoMacro(nome=nome)

    pat = float(sub["valor_abs"].sum())
    custo = float(sub["custo_total"].sum())
    pl = float(sub["pl"].sum())
    pl_pct = round((pl / custo) * 100, 2) if custo > 0 else 0.0
    peso_pct = round((pat / patrimonio_total) * 100, 2) if patrimonio_total > 0 else 0.0

    return ResumoMacro(
        nome=nome,
        patrimonio=round(pat, 2),
        custo=round(custo, 2),
        pl=round(pl, 2),
        pl_pct=pl_pct,
        peso_pct=peso_pct,
    )


def calcular_resumo_carteira(
    pos_cards: pd.DataFrame,
    proventos: pd.DataFrame | None = None,
) -> ResumoCarteira:
    """Calcula o resumo consolidado da carteira a partir de pos_cards e proventos."""
    proventos_total = 0.0
    if proventos is not None and not proventos.empty and "valor_liquido" in proventos.columns:
        proventos_total = round(float(proventos["valor_liquido"].sum()), 2)

    if pos_cards is None or pos_cards.empty:
        return ResumoCarteira(
            patrimonio_total=0.0,
            custo_total=0.0,
            pl_total=0.0,
            pl_pct=0.0,
            proventos_total=proventos_total,
            bolsa=ResumoMacro(nome=LABEL_BOLSA),
            tesouro=ResumoMacro(nome=LABEL_TESOURO),
        )

    patrimonio_total = round(float(pos_cards["valor_abs"].sum()), 2)
    custo_total = round(float(pos_cards["custo_total"].sum()), 2)
    pl_total = round(float(pos_cards["pl"].sum()), 2)
    pl_pct = round((pl_total / custo_total) * 100, 2) if custo_total > 0 else 0.0

    bolsa = _calcular_macro(pos_cards, LABEL_BOLSA, CATEGORIAS_BOLSA, patrimonio_total)
    tesouro = _calcular_macro(pos_cards, LABEL_TESOURO, {CATEGORIA_TESOURO}, patrimonio_total)

    return ResumoCarteira(
        patrimonio_total=patrimonio_total,
        custo_total=custo_total,
        pl_total=pl_total,
        pl_pct=pl_pct,
        proventos_total=proventos_total,
        bolsa=bolsa,
        tesouro=tesouro,
    )
