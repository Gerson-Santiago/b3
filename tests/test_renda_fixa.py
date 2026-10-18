"""Testes unitários para dashboard.metrics.renda_fixa."""
from __future__ import annotations

import pytest

from dashboard.metrics.renda_fixa import (
    METADADOS_TESOURO,
    RENDA_FIXA,
    VENCIMENTOS_RENDA_FIXA,
    filtrar_por_indexador,
)


def test_metadados_tesouro_estrutura():
    assert len(METADADOS_TESOURO) > 0
    for ativo, meta in METADADOS_TESOURO.items():
        assert "indexador" in meta
        assert "tipo" in meta
        assert "data_vencimento" in meta
        assert "vencimento_str" in meta
        assert meta["indexador"] in {"inflação", "pos-fixada", "prefixada"}


def test_renda_fixa_categorias():
    assert "inflação" in RENDA_FIXA
    assert "pos-fixada" in RENDA_FIXA
    assert "prefixada" in RENDA_FIXA

    ipca_ativos = RENDA_FIXA["inflação"]["tesouro-pos-fixado-ipca"]
    assert "Tesouro IPCA+ 2026" in ipca_ativos
    assert "Tesouro Educa+ 2026" in ipca_ativos

    selic_ativos = RENDA_FIXA["pos-fixada"]["tesouro-pos-fixado-selic"]
    assert "Tesouro Selic 2028" in selic_ativos

    prefixados = RENDA_FIXA["prefixada"]["tesouro-prefixado"]
    assert "Tesouro Prefixado com Juros Semestrais 2035" in prefixados


def test_vencimentos_renda_fixa():
    assert "tesouro-pos-fixado-ipca" in VENCIMENTOS_RENDA_FIXA
    assert "tesouro-pos-fixado-selic" in VENCIMENTOS_RENDA_FIXA
    assert "tesouro-prefixado" in VENCIMENTOS_RENDA_FIXA
    assert VENCIMENTOS_RENDA_FIXA["tesouro-pos-fixado-selic"]["Tesouro Selic 2028"] == "01 de março de 2028"


def test_filtrar_por_indexador():
    inflacao = filtrar_por_indexador("inflação")
    assert "Tesouro IPCA+ 2026" in inflacao
    assert "Tesouro IPCA+ 2032" in inflacao
    assert "Tesouro Selic 2028" not in inflacao

    pos_fixada = filtrar_por_indexador("pos-fixada")
    assert "Tesouro Selic 2028" in pos_fixada
    assert "Tesouro Selic 2031" in pos_fixada
    assert "Tesouro IPCA+ 2026" not in pos_fixada

    prefixada = filtrar_por_indexador("prefixada")
    assert "Tesouro Prefixado com Juros Semestrais 2035" in prefixada
    assert "Tesouro Selic 2028" not in prefixada

    inexistente = filtrar_por_indexador("inexistente")
    assert inexistente == []
