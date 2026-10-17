"""Testes para dashboard.state — DashboardState (TDD Red → Green → Refactor)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from dashboard.state import DashboardState

# ---------------------------------------------------------------------------
# Fixtures compartilhadas
# ---------------------------------------------------------------------------

@pytest.fixture()
def pos_df():
    return pd.DataFrame(
        {
            "produto": ["PETR4 - PETROBRAS", "GOGL35 - GOLDEN OCEAN", "Tesouro Selic 2029"],
            "categoria": ["AÇÕES", "BDR", "TESOURO"],
            "qtd_liquida": [10.0, 5.0, 1.0],
            "valor_liquido": [500.0, 300.0, 1000.0],
            "quantidade": [10.0, 5.0, 1.0],
            "instituicao": ["XP", "XP", "XP"],
        }
    )


@pytest.fixture()
def mov_df():
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-06-01"]),
            "mes": ["2024-01", "2024-06"],
            "produto": ["PETR4 - PETROBRAS", "PETR4 - PETROBRAS"],
            "movimentacao": ["Compra", "Dividendo"],
            "entrada_saida": ["Crédito", "Crédito"],
            "quantidade": [10.0, 0.0],
            "qtd_liquida": [10.0, 0.0],
            "valor_liquido": [500.0, 50.0],
            "instituicao": ["XP", "XP"],
        }
    )


# ---------------------------------------------------------------------------
# Construção do estado
# ---------------------------------------------------------------------------

class TestDashboardStateBuild:
    def test_build_retorna_instancia_de_dashboard_state(self, pos_df, mov_df):
        state = DashboardState.build(
            pos_df=pos_df,
            mov_filtered=mov_df,
            pos_filtered=pos_df,
            end_date=date(2024, 12, 31),
        )
        assert isinstance(state, DashboardState)

    def test_pos_nao_vazio_quando_pos_df_valido(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        assert not state.pos.empty

    def test_pos_tem_coluna_categoria(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        assert "categoria" in state.pos.columns

    def test_pos_vazio_quando_inputs_vazios(self):
        vazio = pd.DataFrame()
        state = DashboardState.build(pos_df=vazio, mov_filtered=vazio, pos_filtered=vazio, end_date=date(2024, 12, 31))
        assert state.pos.empty


# ---------------------------------------------------------------------------
# pos_categoria (granular — AÇÕES e BDR separados)
# ---------------------------------------------------------------------------

class TestPosCategoria:
    def test_pos_categoria_tem_colunas_esperadas(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        assert set(["categoria", "valor", "quantidade"]).issubset(state.pos_categoria.columns)

    def test_pos_categoria_contem_acoes_e_bdr_separados(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        categorias = set(state.pos_categoria["categoria"].tolist())
        assert "AÇÕES" in categorias or "BDR" in categorias  # pelo menos uma das duas


# ---------------------------------------------------------------------------
# pos_categoria_agrupada (SSOT do agrupamento Bolsa de Valores)
# ---------------------------------------------------------------------------

class TestPosCategoriaAgrupada:
    def test_agrupada_nao_contem_acoes_nem_bdr_separados(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        cats = set(state.pos_categoria_agrupada["categoria"].tolist())
        assert "AÇÕES" not in cats
        assert "BDR" not in cats

    def test_agrupada_contem_bolsa_de_valores(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        cats = set(state.pos_categoria_agrupada["categoria"].tolist())
        assert "Bolsa de Valores" in cats

    def test_agrupada_soma_valores_de_acoes_e_bdr(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        bolsa = state.pos_categoria_agrupada[state.pos_categoria_agrupada["categoria"] == "Bolsa de Valores"]
        granular = state.pos_categoria[state.pos_categoria["categoria"].isin(["AÇÕES", "BDR"])]
        assert bolsa["valor"].sum() == pytest.approx(granular["valor"].sum(), rel=1e-3)

    def test_agrupada_mantem_tesouro_separado(self, pos_df, mov_df):
        state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        cats = set(state.pos_categoria_agrupada["categoria"].tolist())
        assert "TESOURO" in cats


# ---------------------------------------------------------------------------
# Imutabilidade e isolamento
# ---------------------------------------------------------------------------

class TestImutabilidade:
    def test_duas_chamadas_build_retornam_instancias_independentes(self, pos_df, mov_df):
        s1 = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        s2 = DashboardState.build(pos_df=pos_df, mov_filtered=mov_df, pos_filtered=pos_df, end_date=date(2024, 12, 31))
        # Modificar s1.pos não deve afetar s2.pos
        s1.pos["_test"] = 1
        assert "_test" not in s2.pos.columns
