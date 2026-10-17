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


def test_semantica_quantidade_enum():
    from dashboard.models.efeitos import SemanticaQuantidade
    assert set(SemanticaQuantidade.__members__.keys()) == {"DELTA", "TOTAL", "SNAPSHOT", "NENHUMA"}


def test_efeito_movimentacao_campos_novos():
    from dashboard.models.efeitos import SemanticaQuantidade
    from dashboard.models.movimentacao import TipoMovimentacao
    efeito = efeito_movimentacao("compra", "credito")
    assert efeito.tipo == TipoMovimentacao.COMPRA
    assert efeito.sentido == "credito"
    assert efeito.semantica_quantidade == SemanticaQuantidade.DELTA
    assert efeito.efeito_custo == "soma"
    assert efeito.eh_provento is False
    assert efeito.status == "definido"


def test_todo_par_tipo_sentido_das_fixtures_tem_efeito():
    from pathlib import Path
    from dashboard.loaders.movimentacao import read_movimentacao_file
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx"
    df = read_movimentacao_file(fixture_path)
    for _, row in df.iterrows():
        mov = row.get("movimentacao")
        es = row.get("entrada_saida")
        efeito = efeito_movimentacao(mov, es)
        assert efeito.status == "definido", f"Par sem efeito: {mov} / {es}"


def test_par_desconhecido_gera_aviso_em_relatorio_qualidade():
    from dashboard.models.qualidade import RelatorioQualidade
    rel = RelatorioQualidade()
    with pytest.warns(RuntimeWarning):
        efeito = efeito_movimentacao("evento_inexistente", "credito", qualidade=rel)
    assert efeito.status == "pendente"
    assert not rel.vazio
    assert any(a.tipo == "EVENTO_DESCONHECIDO" for a in rel.avisos)

