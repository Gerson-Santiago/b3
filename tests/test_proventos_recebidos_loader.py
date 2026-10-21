"""Testes unitários para o loader de proventos recebidos (Issue 6.3)."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest

from dashboard.loaders.proventos_recebidos import (
    read_proventos_recebidos_csv,
    read_proventos_recebidos_excel,
    read_proventos_recebidos_file,
)

REAL_XLSX = Path(__file__).resolve().parents[1] / "xlsx" / "proventos-recebidos" / "proventos-recebidos-2026-09-16-a-2026-10-16.xlsx"


class TestProventosRecebidosLoader:
    def test_file_source_none_lanca_value_error(self):
        with pytest.raises(ValueError, match="não informado"):
            read_proventos_recebidos_file(None)

    def test_colunas_ausentes_lanca_value_error(self, tmp_path):
        csv_file = tmp_path / "invalido.csv"
        csv_file.write_text("Produto;Data\nPETR4;01/01/2026\n", encoding="utf-8-sig")
        with pytest.raises(ValueError, match="Colunas ausentes em proventos recebidos"):
            read_proventos_recebidos_file(csv_file)

    def test_leitura_arquivo_real_xlsx(self):
        if not REAL_XLSX.exists():
            pytest.skip("Arquivo real de proventos recebidos não encontrado.")

        df = read_proventos_recebidos_file(REAL_XLSX)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == 57

        # Linhas de total e vazias devem ter sido descartadas
        assert not df["produto"].str.lower().str.contains("total").any()
        assert not df["valor_liquido"].astype(str).str.lower().str.contains("total").any()

        # Colunas obrigatórias e enriquecidas presentes
        cols = set(df.columns)
        for expected in [
            "produto",
            "data_pagamento",
            "data",
            "tipo_evento",
            "tipo_provento",
            "quantidade",
            "preco_unitario",
            "valor_liquido",
            "mes",
            "ano",
            "ativo",
        ]:
            assert expected in cols, f"Coluna esperada {expected} não encontrada"

        # Tipagem correta
        assert pd.api.types.is_datetime64_any_dtype(df["data_pagamento"])
        assert pd.api.types.is_datetime64_any_dtype(df["data"])
        assert pd.api.types.is_float_dtype(df["quantidade"])
        assert pd.api.types.is_float_dtype(df["preco_unitario"])
        assert pd.api.types.is_float_dtype(df["valor_liquido"])

        # Soma total dos 57 proventos confere com o totalizador da B3 (R$ 313,15)
        assert round(float(df["valor_liquido"].sum()), 2) == 313.15

    def test_leitura_csv_in_memory(self):
        csv_content = (
            "Produto;Pagamento;Tipo de Evento;Instituição;Quantidade;Preço unitário;Valor líquido\n"
            "PETR4;21/09/2026;Dividendo;Corretora XP;10;0,50;5,00\n"
            "Tesouro Educa+ 2026;15/10/2026;Amortização;Corretora XP;0,13;79,44;10,33\n"
            ";;;;;;Total\n"
            ";;;;;;15,33\n"
        )
        buffer = io.BytesIO(csv_content.encode("utf-8-sig"))
        setattr(buffer, "name", "proventos.csv")

        df = read_proventos_recebidos_file(buffer)
        assert len(df) == 2
        assert list(df["tipo_provento"]) == ["Dividendo", "Outros"]
        assert list(df["quantidade"]) == [10.0, 0.13]
        assert list(df["valor_liquido"]) == [5.0, 10.33]
        assert list(df["ativo"]) == ["PETR4", "Tesouro Educa+ 2026"]

    def test_planilha_apenas_com_totais_retorna_vazio(self, tmp_path):
        csv_file = tmp_path / "somente_totais.csv"
        csv_file.write_text(
            "Produto;Pagamento;Tipo de Evento;Instituição;Quantidade;Preço unitário;Valor líquido\n"
            ";;;;;;Total\n"
            ";;;;;;313,15\n",
            encoding="utf-8-sig",
        )
        df = read_proventos_recebidos_csv(csv_file)
        assert df.empty
