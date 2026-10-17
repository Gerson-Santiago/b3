"""Testes para dashboard.filters — filtrar_dataframe (TDD Red → Green → Refactor)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from dashboard.filters import filtrar_dataframe


@pytest.fixture()
def df_movimentacao():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-03-15", "2024-06-30", "2024-12-01"]),
            "produto": ["PETR4", "VALE3", "PETR4", "BBAS3"],
            "instituicao": ["XP", "XP", "Nu", "Nu"],
            "valor_liquido": [100.0, 200.0, -50.0, 300.0],
        }
    )


@pytest.fixture()
def df_posicao():
    return pd.DataFrame(
        {
            "produto": ["PETR4", "VALE3", "BBAS3"],
            "instituicao": ["XP", "XP", "Nu"],
            "quantidade": [10.0, 5.0, 20.0],
            "valor_liquido": [500.0, 200.0, 1000.0],
        }
    )


# ---------------------------------------------------------------------------
# Casos: filtros vazios (sem efeito)
# ---------------------------------------------------------------------------

class TestSemFiltros:
    def test_retorna_df_intacto_quando_filtros_vazios(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=[], produtos=[])
        pd.testing.assert_frame_equal(resultado.reset_index(drop=True), df_movimentacao.reset_index(drop=True))

    def test_df_vazio_retorna_vazio(self):
        vazio = pd.DataFrame(columns=["data", "produto", "instituicao", "valor_liquido"])
        resultado = filtrar_dataframe(vazio, instituicoes=[], produtos=[])
        assert resultado.empty

    def test_sem_coluna_data_nao_aplica_filtro_de_data(self, df_posicao):
        """pos_df não tem coluna 'data' — filtro de data deve ser ignorado."""
        resultado = filtrar_dataframe(
            df_posicao,
            instituicoes=[],
            produtos=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
        )
        assert len(resultado) == len(df_posicao)


# ---------------------------------------------------------------------------
# Casos: filtro por instituição
# ---------------------------------------------------------------------------

class TestFiltroInstituicao:
    def test_filtra_por_uma_instituicao(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=["XP"], produtos=[])
        assert set(resultado["instituicao"].unique()) == {"XP"}
        assert len(resultado) == 2

    def test_filtra_por_multiplas_instituicoes(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=["XP", "Nu"], produtos=[])
        assert len(resultado) == len(df_movimentacao)

    def test_instituicao_inexistente_retorna_vazio(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=["BTG"], produtos=[])
        assert resultado.empty


# ---------------------------------------------------------------------------
# Casos: filtro por produto
# ---------------------------------------------------------------------------

class TestFiltroProduto:
    def test_filtra_por_um_produto(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=[], produtos=["PETR4"])
        assert list(resultado["produto"].unique()) == ["PETR4"]
        assert len(resultado) == 2

    def test_filtra_por_multiplos_produtos(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=[], produtos=["PETR4", "VALE3"])
        assert set(resultado["produto"].unique()) == {"PETR4", "VALE3"}

    def test_produto_inexistente_retorna_vazio(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=[], produtos=["XPTO3"])
        assert resultado.empty


# ---------------------------------------------------------------------------
# Casos: filtro por data
# ---------------------------------------------------------------------------

class TestFiltroPorData:
    def test_filtra_intervalo_de_data_inclusive(self, df_movimentacao):
        resultado = filtrar_dataframe(
            df_movimentacao,
            instituicoes=[],
            produtos=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 15),
        )
        assert len(resultado) == 2
        assert all(resultado["data"] >= pd.Timestamp("2024-01-01"))
        assert all(resultado["data"] <= pd.Timestamp("2024-03-15"))

    def test_data_unica_retorna_apenas_aquele_dia(self, df_movimentacao):
        resultado = filtrar_dataframe(
            df_movimentacao,
            instituicoes=[],
            produtos=[],
            start_date=date(2024, 6, 30),
            end_date=date(2024, 6, 30),
        )
        assert len(resultado) == 1
        assert resultado.iloc[0]["produto"] == "PETR4"

    def test_sem_start_e_end_date_nao_filtra_data(self, df_movimentacao):
        resultado = filtrar_dataframe(df_movimentacao, instituicoes=[], produtos=[])
        assert len(resultado) == len(df_movimentacao)


# ---------------------------------------------------------------------------
# Casos: filtros combinados
# ---------------------------------------------------------------------------

class TestFiltrosCombinados:
    def test_instituicao_e_produto_combinados(self, df_movimentacao):
        resultado = filtrar_dataframe(
            df_movimentacao,
            instituicoes=["XP"],
            produtos=["PETR4"],
        )
        assert len(resultado) == 1
        assert resultado.iloc[0]["instituicao"] == "XP"
        assert resultado.iloc[0]["produto"] == "PETR4"

    def test_todos_os_filtros_combinados(self, df_movimentacao):
        resultado = filtrar_dataframe(
            df_movimentacao,
            instituicoes=["Nu"],
            produtos=["BBAS3"],
            start_date=date(2024, 11, 1),
            end_date=date(2024, 12, 31),
        )
        assert len(resultado) == 1
        assert resultado.iloc[0]["produto"] == "BBAS3"

    def test_filtros_sem_resultado_retorna_vazio(self, df_movimentacao):
        resultado = filtrar_dataframe(
            df_movimentacao,
            instituicoes=["XP"],
            produtos=["BBAS3"],  # BBAS3 só existe em Nu
        )
        assert resultado.empty
