from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_file
from dashboard.metrics.preco_medio import compute_preco_medio
from dashboard.metrics.reconciliacao import quantidade_ate, comparar
from dashboard.models.ativos import resolver_ativo
from dashboard.metrics.position import obter_mapa_categorias, classificar_ativo_por_mapa, compute_position_categoria
from dashboard.metrics.dy import compute_dy_metrics
from dashboard.metrics.evolucao import compute_evolucao_separada


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MOV_FIXTURE = FIXTURES_DIR / "movimentacao_7_ativos.xlsx"
POS_FIXTURE = FIXTURES_DIR / "posicao_7_ativos.xlsx"


def test_tdd_quantidade_ate_petr4_vale3_e_roxo34_valores_exatos():
    mov = read_movimentacao_file(MOV_FIXTURE)
    res = quantidade_ate(mov, "2026-10-16")
    
    assert res.get("PETR4") == pytest.approx(23.0)
    assert res.get("VALE3") == pytest.approx(12.0)
    assert res.get("B3SA3") == pytest.approx(57.0)
    assert res.get("ROXO34") == pytest.approx(20.0)


def test_tdd_migracao_nubank_fechamento_20_cotas_sem_somar_atualizacao():
    mov = read_movimentacao_file(MOV_FIXTURE)
    metricas = compute_preco_medio(mov)
    metricas["ticker"] = metricas["produto"].map(lambda p: resolver_ativo(p).codigo)
    
    roxo = metricas[metricas["ticker"] == "ROXO34"]
    assert not roxo.empty
    assert roxo["quantidade"].iloc[0] == pytest.approx(20.0)

    # Garante que B3SA3, VALE3 e PETR4 não dobraram suas quantidades
    b3sa = metricas[metricas["ticker"] == "B3SA3"].iloc[0]
    vale = metricas[metricas["ticker"] == "VALE3"].iloc[0]
    petr = metricas[metricas["ticker"] == "PETR4"].iloc[0]
    assert b3sa["quantidade"] == pytest.approx(57.0)
    assert vale["quantidade"] == pytest.approx(12.0)
    assert petr["quantidade"] == pytest.approx(23.0)


def test_tdd_consulta_categoria_via_posicao_sem_regex():
    pos = read_posicao_file(POS_FIXTURE)
    mapa = obter_mapa_categorias(pos)
    
    assert classificar_ativo_por_mapa("PETR4", mapa) == "AÇÕES"
    assert classificar_ativo_por_mapa("GOGL35", mapa) == "BDR"
    assert classificar_ativo_por_mapa("MSFT34", mapa) == "BDR"
    
    # Ativo com final 11 que NÃO está na posição não deve ser forçado para BDR por regex
    assert classificar_ativo_por_mapa("XPML11", mapa) == "Não classificado"
    assert classificar_ativo_por_mapa("TAEE11", mapa) == "Não classificado"


def test_tdd_dy_ltm_e_yield_on_cost():
    mov = read_movimentacao_file(MOV_FIXTURE)
    pos = read_posicao_file(POS_FIXTURE)
    
    dy_df = compute_dy_metrics(mov, pos, data_referencia="2026-10-16")
    
    assert "ticker" in dy_df.columns
    assert "dy_ltm_pct" in dy_df.columns
    assert "yield_on_cost_pct" in dy_df.columns
    
    # Nenhum ativo com valor de posição deve ter 100% artificial gerado por provento / provento
    assert not (dy_df["dy_ltm_pct"] == 100.0).any()


def test_tdd_evolucao_patrimonio_vs_custo_acumulado():
    mov = read_movimentacao_file(MOV_FIXTURE)
    pos = read_posicao_file(POS_FIXTURE)
    
    evol = compute_evolucao_separada(mov, [pos])
    
    assert "curva_aportes" in evol
    assert "curva_patrimonio" in evol
    assert not evol["curva_aportes"].empty
    assert len(evol["curva_patrimonio"]) >= 1
