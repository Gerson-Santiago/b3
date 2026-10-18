"""Testes complementares para cobrir 100% de dashboard.metrics.position."""
from __future__ import annotations

import pandas as pd
import pytest

from dashboard.metrics.position import (
    classificar_ativo,
    classificar_ativo_por_mapa,
    compute_position,
    compute_position_categoria,
    compute_position_por_categoria,
    obter_mapa_categorias,
    _normalize_positions,
)


def test_obter_mapa_categorias_casos_borda():
    assert obter_mapa_categorias(None) == {}
    assert obter_mapa_categorias(pd.DataFrame()) == {}
    assert obter_mapa_categorias(pd.DataFrame({"produto": ["A"]})) == {}

    df = pd.DataFrame(
        {
            "produto": ["", "  ", "PETR4"],
            "categoria": ["Ações", "Ações", "Ações"],
        }
    )
    mapa = obter_mapa_categorias(df)
    assert "PETR4" in mapa
    assert mapa["PETR4"] == "Ações"


def test_classificar_ativo_casos():
    assert classificar_ativo("") == "Não classificado"
    assert classificar_ativo(None) == "Não classificado"
    assert classificar_ativo("ATIVO_DESCONHECIDO_XYZ") == "Não classificado"

    mapa = {"XPTO": "Outros"}
    assert classificar_ativo("XPTO", mapa_categorias=mapa) == "Outros"
    assert classificar_ativo_por_mapa("", mapa_categorias=mapa) == "Não classificado"
    assert classificar_ativo_por_mapa("NAO_EXISTE", mapa_categorias=mapa) == "Não classificado"
    assert classificar_ativo_por_mapa("xpto", mapa_categorias=mapa) == "Outros"


def test_normalize_positions_casos():
    assert _normalize_positions(None).empty
    assert _normalize_positions(pd.DataFrame()).empty
    assert _normalize_positions(pd.DataFrame({"outra": [1, 2]})).empty

    # Suporta fallback de valor_operacao e quantidade
    df = pd.DataFrame(
        {
            "produto": ["VALE3"],
            "quantidade": [100],
            "valor_operacao": [6500.0],
        }
    )
    norm = _normalize_positions(df)
    assert "qtd_liquida" in norm.columns
    assert "valor_liquido" in norm.columns
    assert norm["qtd_liquida"].iloc[0] == 100
    assert norm["valor_liquido"].iloc[0] == 6500.0


def test_compute_position_casos():
    assert compute_position(None).empty
    assert compute_position(pd.DataFrame()).empty

    df = pd.DataFrame(
        {
            "produto": ["VALE3", "PETR4"],
            "quantidade": [0, 50],
            "valor_operacao": [0.0, 1500.0],
        }
    )
    pos = compute_position(df)
    # Apenas itens com quantidade > 0 permanecem
    assert len(pos) == 1
    assert pos["produto"].iloc[0] == "PETR4"


def test_compute_position_categoria_casos():
    assert compute_position_categoria(None).empty
    assert compute_position_categoria(pd.DataFrame()).empty

    df = pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3"],
            "quantidade": [10, 20],
            "valor_operacao": [300.0, 1200.0],
        }
    )
    resumo = compute_position_categoria(df)
    assert not resumo.empty
    assert "categoria" in resumo.columns


def test_compute_position_por_categoria():
    assert compute_position_por_categoria(None, "Ações").empty

    df = pd.DataFrame(
        {
            "produto": ["PETR4", "Tesouro Selic 2029"],
            "categoria": ["Ações", "Tesouro Direto"],
            "quantidade": [100, 2],
            "valor_operacao": [3500.0, 2000.0],
        }
    )
    pos_acoes = compute_position_por_categoria(df, "Ações")
    assert len(pos_acoes) == 1
    assert pos_acoes["produto"].iloc[0] == "PETR4"

    pos_sem_cat = compute_position_por_categoria(
        pd.DataFrame(
            {
                "produto": ["PETR4"],
                "quantidade": [100],
                "valor_operacao": [3500.0],
            }
        ),
        "AÇÕES",
    )
    assert len(pos_sem_cat) == 1

