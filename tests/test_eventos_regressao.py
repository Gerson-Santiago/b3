import json
from pathlib import Path

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


def test_regressao_preco_medio_7_ativos_base_real():
    mov = read_movimentacao_file(MOV_FIXTURE_PATH)

    atual = compute_preco_medio(mov).copy()
    atual["produto_norm"] = atual["produto"].map(_normalizar_produto)

    esperado = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for codigo, valores in esperado.items():
        if codigo == "ROXO34":
            pytest.xfail(reason="saldo sem origem no histórico")

        linha = atual[atual["produto_norm"] == codigo]
        assert not linha.empty, f"Produto ausente no cálculo atual: {codigo}"
        atual_linha = linha.iloc[0]

        assert float(atual_linha["quantidade"]) == pytest.approx(float(valores["quantidade"]), abs=1e-9)
        assert float(atual_linha["preco_medio"]) == pytest.approx(float(valores["preco_medio"]), rel=1e-9, abs=1e-9)
