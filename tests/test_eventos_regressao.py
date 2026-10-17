import json
from pathlib import Path

import pandas as pd
import pytest

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.metrics.preco_medio import compute_preco_medio


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "ativos_7_preco_medio.json"
MOV_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx"
POS_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "posicao_7_ativos.xlsx"


def _normalizar_produto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    if " - " in texto:
        texto = texto.split(" - ", 1)[0]
    return texto.strip().upper()


@pytest.mark.parametrize(
    "codigo, valores",
    [
        pytest.param("B3SA3", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["B3SA3"], id="B3SA3"),
        pytest.param("PETR4", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["PETR4"], id="PETR4"),
        pytest.param("VALE3", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["VALE3"], id="VALE3"),
        pytest.param("CPFE3", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["CPFE3"], id="CPFE3"),
        pytest.param("MSFT34", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["MSFT34"], id="MSFT34"),
        pytest.param("GOGL35", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["GOGL35"], id="GOGL35"),
        pytest.param("ROXO34", json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["ROXO34"], id="ROXO34"),
    ],
)
def test_regressao_preco_medio_7_ativos_base_real(codigo, valores):
    mov = read_movimentacao_file(MOV_FIXTURE_PATH)

    atual = compute_preco_medio(mov).copy()
    atual["produto_norm"] = atual["produto"].map(_normalizar_produto)

    linha = atual[atual["produto_norm"] == codigo]
    assert not linha.empty, f"Produto ausente no cálculo atual: {codigo}"
    atual_linha = linha.iloc[0]

    assert float(atual_linha["quantidade"]) == pytest.approx(float(valores["quantidade"]), abs=1e-9)
    if valores["preco_medio"] is None:
        import numpy as np
        assert pd.isna(atual_linha["preco_medio"]) or np.isnan(atual_linha["preco_medio"])
    else:
        assert float(atual_linha["preco_medio"]) == pytest.approx(float(valores["preco_medio"]), rel=1e-9, abs=1e-9)

