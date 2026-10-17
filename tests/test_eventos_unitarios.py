"""Cobertura do comportamento atual da SSOT de eventos corporativos."""
from __future__ import annotations

import pandas as pd
import pytest

from dashboard.models.eventos import (
    aplicar_eventos_ordenados,
    efeito_movimentacao,
    listar_movimentacoes_pendentes,
    tem_efeito_pendente,
)


def test_efeito_compra_e_venda_sao_definidos():
    compra = efeito_movimentacao("Compra", "Crédito")
    venda = efeito_movimentacao("Venda", "Débito")
    assert compra.status == "definido"
    assert compra.quantidade == "soma"
    assert venda.quantidade == "subtrai"
    assert compra.provento is False


def test_efeito_dividendo_e_provento_e_ignorado_na_quantidade():
    efeito = efeito_movimentacao("Dividendo", "Crédito")
    assert efeito.provento is True
    assert efeito.quantidade == "ignora"


def test_efeito_desconhecido_fica_pendente():
    with pytest.warns(RuntimeWarning):
        efeito = efeito_movimentacao("evento inventado xyz", "credito")
    assert efeito.status == "pendente"
    assert efeito.quantidade == "pendente"


def test_aplicar_eventos_compra_venda_e_bonificacao():
    df = pd.DataFrame(
        {
            "produto": ["PETR4", "PETR4", "PETR4", "PETR4"],
            "data": ["2024-01-10", "2024-02-10", "2024-03-10", "2024-03-15"],
            "qtd_liquida": [10, 5, -3, 2],
            "valor_liquido": [200, 100, -60, 0],
            "movimentacao": ["compra", "compra", "venda", "bonificação"],
            "entrada_saida": ["credito", "credito", "debito", "credito"],
        }
    )
    result = aplicar_eventos_ordenados(df)
    petr = result[result["produto"] == "PETR4"].iloc[0]
    assert petr["quantidade"] == pytest.approx(14.0)
    assert petr["custo_total"] == pytest.approx(240.0)
    assert petr["preco_medio"] == pytest.approx(240.0 / 14.0)


def test_aplicar_eventos_vazio_retorna_colunas():
    vazio = aplicar_eventos_ordenados(pd.DataFrame())
    assert list(vazio.columns) == ["produto", "quantidade", "custo_total", "preco_medio"]
    assert vazio.empty


def test_listar_pendentes_e_flag():
    df = pd.DataFrame(
        {
            "movimentacao": ["compra", "evento novo"],
            "entrada_saida": ["credito", "credito"],
        }
    )
    with pytest.warns(RuntimeWarning):
        pendentes = listar_movimentacoes_pendentes(df)
    assert pendentes == ["evento novo|credito"]
    with pytest.warns(RuntimeWarning):
        assert tem_efeito_pendente(df) is True
    assert tem_efeito_pendente(pd.DataFrame()) is False
