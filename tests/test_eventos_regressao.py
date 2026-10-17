import json
from pathlib import Path

import pytest

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.metrics.preco_medio import compute_preco_medio


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "ativos_7_preco_medio.json"


def _normalizar_produto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    if " - " in texto:
        texto = texto.split(" - ", 1)[0]
    return texto.strip().upper()


def test_regressao_preco_medio_7_ativos_base_real():
    mov_path = sorted((Path(__file__).resolve().parents[1] / "xlsx" / "movimentacao").glob("*.xlsx"))[-1]
    mov = read_movimentacao_file(mov_path)

    atual = compute_preco_medio(mov).copy()
    atual["produto_norm"] = atual["produto"].map(_normalizar_produto)

    esperado = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for codigo, valores in esperado.items():
        linha = atual[atual["produto_norm"] == codigo]
        assert not linha.empty, f"Produto ausente no cálculo atual: {codigo}"
        atual_linha = linha.iloc[0]

        assert float(atual_linha["quantidade"]) == pytest.approx(float(valores["quantidade"]), abs=1e-9)
        assert float(atual_linha["preco_medio"]) == pytest.approx(float(valores["preco_medio"]), rel=1e-9, abs=1e-9)
