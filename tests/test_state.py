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


# ---------------------------------------------------------------------------
# R10: Filtro de data não pode corromper Preço Médio nem Quantidade
# ---------------------------------------------------------------------------

class TestR10PrecoMedioQuantidadeFiltroData:
    @pytest.fixture()
    def mov_historico_completo(self):
        """Histórico com compras antigas (2023) e recentes (2024) para PETR4 e GOGL35."""
        return pd.DataFrame(
            {
                "data": pd.to_datetime(["2023-01-15", "2023-06-10", "2024-08-20", "2024-09-01"]),
                "mes": ["2023-01", "2023-06", "2024-08", "2024-09"],
                "produto": ["PETR4", "GOGL35", "PETR4", "GOGL35"],
                "movimentacao": ["Compra", "Compra", "Compra", "Dividendo"],
                "entrada_saida": ["Crédito", "Crédito", "Crédito", "Crédito"],
                "quantidade": [10.0, 20.0, 10.0, 0.0],
                "qtd_liquida": [10.0, 20.0, 10.0, 0.0],
                "valor_liquido": [300.0, 1000.0, 400.0, 50.0],
                "instituicao": ["XP", "XP", "XP", "XP"],
            }
        )

    def test_start_date_diferente_preserva_mesmo_preco_medio_e_quantidade(self, mov_historico_completo):
        """(a) start_date no início vs start_date 6 meses atrás devolve o MESMO PM e MESMA quantidade para GOGL35 e PETR4."""
        pos_df = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        pos_filtered = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        end_date = date(2024, 12, 31)

        # Filtro 1: start_date no início (2023-01-01) -> pega tudo
        mov_inicio = mov_historico_completo[mov_historico_completo["data"] >= pd.Timestamp("2023-01-01")].copy()

        # Filtro 2: start_date 6 meses atrás (2024-06-01) -> corta compras de 2023
        mov_6meses = mov_historico_completo[mov_historico_completo["data"] >= pd.Timestamp("2024-06-01")].copy()

        state_inicio = DashboardState.build(
            pos_df=pos_df,
            mov_df=mov_historico_completo,
            mov_filtered=mov_inicio,
            pos_filtered=pos_filtered,
            end_date=end_date,
        )

        state_6meses = DashboardState.build(
            pos_df=pos_df,
            mov_df=mov_historico_completo,
            mov_filtered=mov_6meses,
            pos_filtered=pos_filtered,
            end_date=end_date,
        )

        # Checar PETR4
        petr_inicio = state_inicio.pos_cards[state_inicio.pos_cards["produto"] == "PETR4"].iloc[0]
        petr_6m = state_6meses.pos_cards[state_6meses.pos_cards["produto"] == "PETR4"].iloc[0]
        assert petr_6m["quantidade"] == pytest.approx(petr_inicio["quantidade"])
        assert petr_6m["preco_medio"] == pytest.approx(petr_inicio["preco_medio"])

        # Checar GOGL35 (cuja compra foi em 2023; em 2024 só houve dividendo)
        gogl_inicio = state_inicio.pos_cards[state_inicio.pos_cards["produto"] == "GOGL35"].iloc[0]
        gogl_6m = state_6meses.pos_cards[state_6meses.pos_cards["produto"] == "GOGL35"].iloc[0]
        assert gogl_6m["quantidade"] == pytest.approx(gogl_inicio["quantidade"])
        assert gogl_6m["preco_medio"] == pytest.approx(gogl_inicio["preco_medio"])

    def test_filtro_de_produto_continua_restringindo_resultado(self, mov_historico_completo):
        """(b) o filtro de produto continua restringindo o resultado de pos e pos_cards."""
        pos_df = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        pos_filtered = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        end_date = date(2024, 12, 31)

        mov_petr4_only = mov_historico_completo[mov_historico_completo["produto"] == "PETR4"].copy()

        state = DashboardState.build(
            pos_df=pos_df,
            mov_df=mov_petr4_only,
            mov_filtered=mov_petr4_only,
            pos_filtered=pos_filtered,
            end_date=end_date,
        )

        assert set(state.pos["produto"].unique()) == {"PETR4"}
        assert set(state.pos_cards["produto"].unique()) == {"PETR4"}

    def test_ativo_sintetico_compra_2023_preserva_quantidade_e_preco_medio_com_start_date_recente(self):
        """Ativo sintético XYZ3 com compra única em 2023 mantém quantidade 100 e PM 10.0 com start_date de 6 meses atrás."""
        mov_df = pd.DataFrame(
            {
                "data": pd.to_datetime(["2023-01-10", "2024-08-01"]),
                "mes": ["2023-01", "2024-08"],
                "produto": ["XYZ3", "PETR4"],
                "movimentacao": ["Compra", "Compra"],
                "entrada_saida": ["Crédito", "Crédito"],
                "quantidade": [100.0, 10.0],
                "qtd_liquida": [100.0, 10.0],
                "valor_liquido": [1000.0, 300.0],
                "instituicao": ["XP", "XP"],
            }
        )
        pos_df = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        pos_filtered = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        end_date = date(2024, 12, 31)

        # Usuário selecionou start_date = 2024-06-01 (6 meses atrás), SEM filtrar produto (produtos_selecionados=[])
        mov_6m = mov_df[mov_df["data"] >= pd.Timestamp("2024-06-01")].copy()

        state = DashboardState.build(
            pos_df=pos_df,
            mov_df=mov_df,
            mov_filtered=mov_6m,
            pos_filtered=pos_filtered,
            end_date=end_date,
            produtos_selecionados=[],
            instituicoes_selecionadas=[],
        )

        # XYZ3 deve existir em pos_cards com quantidade 100.0 e preço médio 10.0
        assert "XYZ3" in state.pos_cards["produto"].values, "XYZ3 sumiu dos cards devido a inferência incorreta de filtro!"
        xyz = state.pos_cards[state.pos_cards["produto"] == "XYZ3"].iloc[0]
        assert xyz["quantidade"] == pytest.approx(100.0)
        assert xyz["preco_medio"] == pytest.approx(10.0)


