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
