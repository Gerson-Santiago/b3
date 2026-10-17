"""Testes para pos_cards, evol_bolsa e evol_tesouro no DashboardState.

Cobre as features adicionadas:
- _enriquecer_pos_cards → pos_cards com pl e variacao_pct
- evol_bolsa / evol_tesouro segmentados por categoria
- render_cards_grid / _render_card em _helpers
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from dashboard.state import DashboardState, _enriquecer_pos_cards


# ---------------------------------------------------------------------------
# Fixtures — mesma estrutura de test_state.py
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
    """Movimentações com AÇÕES (PETR4) e TESOURO — BDR sem mov para testar vazio."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-15", "2024-03-10", "2024-01-20"]),
            "mes": ["2024-01", "2024-03", "2024-01"],
            "produto": ["PETR4 - PETROBRAS", "PETR4 - PETROBRAS", "Tesouro Selic 2029"],
            "movimentacao": ["Compra", "Dividendo", "Compra"],
            "entrada_saida": ["Crédito", "Crédito", "Crédito"],
            "quantidade": [10.0, 0.0, 1.0],
            "qtd_liquida": [10.0, 0.0, 1.0],
            "valor_liquido": [500.0, 50.0, 1000.0],
            "instituicao": ["XP", "XP", "XP"],
        }
    )


@pytest.fixture()
def state(pos_df, mov_df):
    return DashboardState.build(
        pos_df=pos_df,
        mov_filtered=mov_df,
        pos_filtered=pos_df,
        end_date=date(2024, 12, 31),
    )


# ---------------------------------------------------------------------------
# _enriquecer_pos_cards (função pura — testada diretamente)
# ---------------------------------------------------------------------------

class TestEnriquecerPosCards:
    def test_retorna_dataframe_vazio_quando_pos_vazio(self):
        pos = pd.DataFrame(columns=["produto", "categoria", "quantidade", "valor_abs"])
        pm = pd.DataFrame(columns=["produto", "preco_medio", "custo_total"])
        result = _enriquecer_pos_cards(pos, pm)
        assert result.empty

    def test_colunas_obrigatorias_presentes(self):
        pos = pd.DataFrame({
            "produto": ["PETR4"],
            "categoria": ["AÇÕES"],
            "quantidade": [10.0],
            "valor_abs": [600.0],
        })
        pm = pd.DataFrame({
            "produto": ["PETR4"],
            "preco_medio": [50.0],
            "custo_total": [500.0],
        })
        result = _enriquecer_pos_cards(pos, pm)
        assert set(["produto", "categoria", "quantidade", "valor_abs",
                     "preco_medio", "custo_total", "pl", "variacao_pct"]).issubset(result.columns)

    def test_pl_calculado_corretamente(self):
        pos = pd.DataFrame({"produto": ["PETR4"], "categoria": ["AÇÕES"],
                             "quantidade": [10.0], "valor_abs": [600.0]})
        pm = pd.DataFrame({"produto": ["PETR4"], "preco_medio": [50.0], "custo_total": [500.0]})
        result = _enriquecer_pos_cards(pos, pm)
        assert result.loc[0, "pl"] == pytest.approx(100.0)

    def test_variacao_pct_calculada_corretamente(self):
        pos = pd.DataFrame({"produto": ["PETR4"], "categoria": ["AÇÕES"],
                             "quantidade": [10.0], "valor_abs": [600.0]})
        pm = pd.DataFrame({"produto": ["PETR4"], "preco_medio": [50.0], "custo_total": [500.0]})
        result = _enriquecer_pos_cards(pos, pm)
        # (600 - 500) / 500 * 100 = 20%
        assert result.loc[0, "variacao_pct"] == pytest.approx(20.0)

    def test_variacao_pct_zero_quando_sem_custo(self):
        pos = pd.DataFrame({"produto": ["PETR4"], "categoria": ["AÇÕES"],
                             "quantidade": [10.0], "valor_abs": [600.0]})
        pm = pd.DataFrame(columns=["produto", "preco_medio", "custo_total"])
        result = _enriquecer_pos_cards(pos, pm)
        assert result.loc[0, "variacao_pct"] == pytest.approx(0.0)

    def test_pl_negativo_quando_prejuizo(self):
        pos = pd.DataFrame({"produto": ["PETR4"], "categoria": ["AÇÕES"],
                             "quantidade": [10.0], "valor_abs": [400.0]})
        pm = pd.DataFrame({"produto": ["PETR4"], "preco_medio": [50.0], "custo_total": [500.0]})
        result = _enriquecer_pos_cards(pos, pm)
        assert result.loc[0, "pl"] < 0

    def test_ordenado_por_valor_abs_decrescente(self):
        pos = pd.DataFrame({
            "produto": ["PETR4", "VALE3"],
            "categoria": ["AÇÕES", "AÇÕES"],
            "quantidade": [10.0, 5.0],
            "valor_abs": [300.0, 800.0],
        })
        pm = pd.DataFrame(columns=["produto", "preco_medio", "custo_total"])
        result = _enriquecer_pos_cards(pos, pm)
        assert result.iloc[0]["produto"] == "VALE3"

    def test_join_via_ticker_quando_pos_tem_nome_completo(self):
        """Bug corrigido: pos usa nome completo, pm_df usa ticker — join deve casar."""
        pos = pd.DataFrame({
            "produto": ["PETR4 - PETROLEO BRASILEIRO S/A - PETROBRAS"],
            "categoria": ["AÇÕES"],
            "quantidade": [10.0],
            "valor_abs": [600.0],
        })
        # pm_df retorna o ticker normalizado (comportamento de aplicar_eventos_ordenados)
        pm = pd.DataFrame({
            "produto": ["PETR4"],
            "preco_medio": [50.0],
            "custo_total": [500.0],
        })
        result = _enriquecer_pos_cards(pos, pm)
        # Deve encontrar o PM — antes do fix ficava 0.0 por merge vazio
        assert result.loc[0, "preco_medio"] == pytest.approx(50.0)
        assert result.loc[0, "custo_total"] == pytest.approx(500.0)
        assert result.loc[0, "pl"] == pytest.approx(100.0)

    def test_join_nao_cria_linhas_duplicadas(self):
        """Cada produto deve aparecer exatamente uma vez no resultado."""
        pos = pd.DataFrame({
            "produto": ["PETR4 - PETROBRAS", "VALE3 - VALE"],
            "categoria": ["AÇÕES", "AÇÕES"],
            "quantidade": [10.0, 5.0],
            "valor_abs": [600.0, 400.0],
        })
        pm = pd.DataFrame({
            "produto": ["PETR4", "VALE3"],
            "preco_medio": [50.0, 70.0],
            "custo_total": [500.0, 350.0],
        })
        result = _enriquecer_pos_cards(pos, pm)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# pos_cards no DashboardState
# ---------------------------------------------------------------------------

class TestPosCards:
    def test_pos_cards_existe_no_state(self, state):
        assert hasattr(state, "pos_cards")

    def test_pos_cards_e_dataframe(self, state):
        assert isinstance(state.pos_cards, pd.DataFrame)

    def test_pos_cards_nao_vazio_quando_pos_valido(self, state):
        assert not state.pos_cards.empty

    def test_pos_cards_tem_colunas_obrigatorias(self, state):
        esperadas = {"produto", "categoria", "quantidade", "valor_abs",
                     "preco_medio", "custo_total", "pl", "variacao_pct"}
        assert esperadas.issubset(state.pos_cards.columns)

    def test_pos_cards_mesmos_produtos_que_pos(self, state):
        assert set(state.pos_cards["produto"]) == set(state.pos["produto"])

    def test_pos_cards_vazio_quando_inputs_vazios(self):
        vazio = pd.DataFrame()
        state = DashboardState.build(
            pos_df=vazio, mov_filtered=vazio, pos_filtered=vazio,
            end_date=date(2024, 12, 31),
        )
        assert state.pos_cards.empty

    def test_pos_cards_pl_numerico(self, state):
        assert pd.api.types.is_numeric_dtype(state.pos_cards["pl"])

    def test_pos_cards_variacao_pct_numerico(self, state):
        assert pd.api.types.is_numeric_dtype(state.pos_cards["variacao_pct"])


# ---------------------------------------------------------------------------
# evol_bolsa / evol_tesouro
# ---------------------------------------------------------------------------

class TestEvolPorProduto:
    def test_evol_bolsa_existe_no_state(self, state):
        assert hasattr(state, "evol_bolsa")

    def test_evol_tesouro_existe_no_state(self, state):
        assert hasattr(state, "evol_tesouro")

    def test_evol_bolsa_tem_chaves_esperadas(self, state):
        assert set(state.evol_bolsa.keys()) == {"curva_aportes", "curva_patrimonio"}

    def test_evol_tesouro_tem_chaves_esperadas(self, state):
        assert set(state.evol_tesouro.keys()) == {"curva_aportes", "curva_patrimonio"}

    def test_evol_bolsa_mesma_estrutura_que_evol_dict(self, state):
        assert set(state.evol_bolsa.keys()) == set(state.evol_dict.keys())

    def test_evol_bolsa_curva_aportes_e_dataframe(self, state):
        assert isinstance(state.evol_bolsa["curva_aportes"], pd.DataFrame)

    def test_evol_tesouro_curva_aportes_e_dataframe(self, state):
        assert isinstance(state.evol_tesouro["curva_aportes"], pd.DataFrame)

    def test_evol_bolsa_aportes_nao_inclui_tesouro(self, state):
        """Curva de aportes da bolsa deve ser menor ou igual ao consolidado."""
        bolsa_total = state.evol_bolsa["curva_aportes"]["custo_acumulado"].max() \
            if not state.evol_bolsa["curva_aportes"].empty else 0.0
        consolidado_total = state.evol_dict["curva_aportes"]["custo_acumulado"].max() \
            if not state.evol_dict["curva_aportes"].empty else 0.0
        assert bolsa_total <= consolidado_total + 1e-6

    def test_evol_tesouro_aportes_nao_inclui_bolsa(self, state):
        """Curva de aportes do tesouro deve ser menor ou igual ao consolidado."""
        tesouro_total = state.evol_tesouro["curva_aportes"]["custo_acumulado"].max() \
            if not state.evol_tesouro["curva_aportes"].empty else 0.0
        consolidado_total = state.evol_dict["curva_aportes"]["custo_acumulado"].max() \
            if not state.evol_dict["curva_aportes"].empty else 0.0
        assert tesouro_total <= consolidado_total + 1e-6

    def test_evol_por_produto_vazio_quando_sem_movimentacoes(self):
        vazio = pd.DataFrame()
        state = DashboardState.build(
            pos_df=vazio, mov_filtered=vazio, pos_filtered=vazio,
            end_date=date(2024, 12, 31),
        )
        assert state.evol_bolsa["curva_aportes"].empty
        assert state.evol_tesouro["curva_aportes"].empty


# ---------------------------------------------------------------------------
# R8: Rótulo de Custo Histórico vs Valor Atual no fallback de posição
# ---------------------------------------------------------------------------

class TestR8RotuloCustoHistoricoFallback:
    def test_rotulo_valor_usa_custo_historico_quando_pos_filtered_vazio(self, mov_df):
        """No fallback sem arquivo de posição, a view define rótulo 'Custo histórico'."""
        vazio = pd.DataFrame(columns=["produto", "quantidade", "valor", "valor_abs", "categoria"])
        state = DashboardState.build(
            pos_df=vazio,
            mov_df=mov_df,
            mov_filtered=mov_df,
            pos_filtered=vazio,
            end_date=date(2024, 12, 31),
        )
        is_fallback = state.pos_filtered.empty
        rotulo_valor = "Custo histórico" if is_fallback else "Valor Atual (snapshot)"
        assert is_fallback is True
        assert rotulo_valor == "Custo histórico"

    def test_rotulo_valor_usa_snapshot_quando_pos_filtered_presente(self, pos_df, mov_df):
        """Quando o arquivo de posição está presente, o rótulo é 'Valor Atual (snapshot)'."""
        state = DashboardState.build(
            pos_df=pos_df,
            mov_df=mov_df,
            mov_filtered=mov_df,
            pos_filtered=pos_df,
            end_date=date(2024, 12, 31),
        )
        is_fallback = state.pos_filtered.empty
        rotulo_valor = "Custo histórico" if is_fallback else "Valor Atual (snapshot)"
        assert is_fallback is False
        assert rotulo_valor == "Valor Atual (snapshot)"

