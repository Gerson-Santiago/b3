import pandas as pd
import pytest

from dashboard.metrics.position import obter_mapa_categorias, classificar_ativo_por_mapa


def test_obter_mapa_categorias_from_pos_df():
    pos = pd.DataFrame([
        {"produto": "PETR4 - PETROLEO BRASILEIRO S.A. PETROBRAS", "categoria": "Acoes"},
        {"produto": "ROXO34 - NU HOLDINGS LTD.", "categoria": "BDR"},
        {"produto": "Tesouro Selic 2029", "categoria": "Tesouro Direto"},
    ])

    mapa = obter_mapa_categorias(pos)
    assert mapa["PETR4"] == "Acoes"
    assert mapa["ROXO34"] == "BDR"
    assert any("TESOURO" in k.upper() for k in mapa)


def test_classificar_ativo_por_mapa_sem_regex():
    mapa = {
        "PETR4": "Acoes",
        "ROXO34": "BDR",
        "XPLG11": "FII",
    }
    assert classificar_ativo_por_mapa("PETR4", mapa) == "Acoes"
    assert classificar_ativo_por_mapa("ROXO34", mapa) == "BDR"
    assert classificar_ativo_por_mapa("XPLG11", mapa) == "FII"
    # Ativo não presente no mapa de posições não deve ser adivinhado por regex
    assert classificar_ativo_por_mapa("BOVA11", mapa) == "Não classificado"
    assert classificar_ativo_por_mapa("QUALQUER12", mapa) == "Não classificado"


def test_classificar_classe_5():
    from dashboard.models.categorias import (
        CLASSE_ACOES,
        CLASSE_INTERNACIONAL,
        CLASSE_RENDA_FIXA_INFLACAO,
        CLASSE_RENDA_FIXA_POS,
        CLASSE_RENDA_FIXA_PRE,
        classificar_classe_5,
    )

    assert classificar_classe_5("PETR4", "AÇÕES") == CLASSE_ACOES
    assert classificar_classe_5("VALE3", "ACOES") == CLASSE_ACOES
    assert classificar_classe_5("AAPL34", "BDR") == CLASSE_INTERNACIONAL
    assert classificar_classe_5("Tesouro Selic 2028", "TESOURO") == CLASSE_RENDA_FIXA_POS
    assert classificar_classe_5("Tesouro Selic 2031", "TESOURO") == CLASSE_RENDA_FIXA_POS
    assert classificar_classe_5("Tesouro Prefixado com Juros Semestrais 2035", "TESOURO") == CLASSE_RENDA_FIXA_PRE
    assert classificar_classe_5("Tesouro IPCA+ 2032", "TESOURO") == CLASSE_RENDA_FIXA_INFLACAO
    assert classificar_classe_5("Tesouro Educa+ 2026", "TESOURO") == CLASSE_RENDA_FIXA_INFLACAO


def test_calcular_alocacao_5_classes_dinamica():
    from dashboard.models.categorias import calcular_alocacao_5_classes

    df = pd.DataFrame([
        {"produto": "PETR4", "categoria": "AÇÕES", "valor_abs": 389.0},
        {"produto": "AAPL34", "categoria": "BDR", "valor_abs": 347.0},
        {"produto": "Tesouro IPCA+ 2032", "categoria": "TESOURO", "valor_abs": 173.0},
        {"produto": "Tesouro Selic 2028", "categoria": "TESOURO", "valor_abs": 51.0},
        {"produto": "Tesouro Prefixado 2035", "categoria": "TESOURO", "valor_abs": 40.0},
    ])

    aloc = calcular_alocacao_5_classes(df)
    assert len(aloc) == 5
    assert aloc.loc[aloc["classe"] == "Ações", "peso_pct"].iloc[0] == pytest.approx(38.9, abs=0.1)
    assert aloc.loc[aloc["classe"] == "Internacional", "peso_pct"].iloc[0] == pytest.approx(34.7, abs=0.1)
    assert aloc.loc[aloc["classe"] == "Renda fixa inflação", "peso_pct"].iloc[0] == pytest.approx(17.3, abs=0.1)
    assert aloc.loc[aloc["classe"] == "Renda fixa pós-fixada", "peso_pct"].iloc[0] == pytest.approx(5.1, abs=0.1)
    assert aloc.loc[aloc["classe"] == "Renda fixa prefixada", "peso_pct"].iloc[0] == pytest.approx(4.0, abs=0.1)

