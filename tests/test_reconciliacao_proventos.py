"""Testes unitários para a reconciliação cruzada de proventos (Issue 6.4)."""
from __future__ import annotations

import pandas as pd
import pytest

from dashboard.metrics.reconciliacao_proventos import reconciliar_proventos


class TestReconciliarProventos:
    def test_ambos_none_ou_vazios_retorna_dataframe_vazio(self):
        res_none = reconciliar_proventos(None, None)
        assert isinstance(res_none, pd.DataFrame)
        assert list(res_none.columns) == [
            "ativo",
            "total_movimentacao",
            "total_extrato_proventos",
            "delta",
            "status",
        ]
        assert res_none.empty

        res_vazio = reconciliar_proventos(pd.DataFrame(), pd.DataFrame())
        assert res_vazio.empty

    def test_cenario_conciliado_perfeito(self):
        mov_df = pd.DataFrame(
            {
                "data": [pd.Timestamp("2026-09-20"), pd.Timestamp("2026-09-21")],
                "movimentacao": ["Dividendo", "Juros Sobre Capital Próprio"],
                "entrada_saida": ["Credito", "Credito"],
                "produto": ["PETR4", "PETR4"],
                "valor_liquido": [10.0, 15.0],
            }
        )
        prov_df = pd.DataFrame(
            {
                "data_pagamento": [pd.Timestamp("2026-09-21")],
                "tipo_evento": ["Dividendo"],
                "produto": ["PETR4"],
                "valor_liquido": [25.0],
            }
        )

        res = reconciliar_proventos(mov_df, prov_df)
        assert len(res) == 1
        row = res.iloc[0]
        assert row["ativo"] == "PETR4"
        assert row["total_movimentacao"] == 25.0
        assert row["total_extrato_proventos"] == 25.0
        assert row["delta"] == 0.0
        assert row["status"] == "OK"

    def test_diferenca_de_centavo_dentro_da_tolerancia(self):
        mov_df = pd.DataFrame(
            {
                "movimentacao": ["Dividendo"],
                "entrada_saida": ["Credito"],
                "produto": ["VALE3"],
                "valor_liquido": [100.00],
            }
        )
        prov_df = pd.DataFrame(
            {
                "tipo_evento": ["Dividendo"],
                "produto": ["VALE3"],
                "valor_liquido": [100.01],
            }
        )
        res = reconciliar_proventos(mov_df, prov_df, tolerancia=0.01)
        assert res.iloc[0]["status"] == "OK"
        assert abs(res.iloc[0]["delta"]) <= 0.01

    def test_divergencia_real(self):
        mov_df = pd.DataFrame(
            {
                "movimentacao": ["Dividendo"],
                "entrada_saida": ["Credito"],
                "produto": ["ITSA4"],
                "valor_liquido": [50.0],
            }
        )
        prov_df = pd.DataFrame(
            {
                "tipo_evento": ["Dividendo"],
                "produto": ["ITSA4"],
                "valor_liquido": [40.0],
            }
        )
        res = reconciliar_proventos(mov_df, prov_df)
        assert res.iloc[0]["status"] == "Divergente"
        assert res.iloc[0]["delta"] == -10.0

    def test_ativo_apenas_em_um_dos_lados(self):
        mov_df = pd.DataFrame(
            {
                "movimentacao": ["Dividendo"],
                "entrada_saida": ["Credito"],
                "produto": ["B3SA3"],
                "valor_liquido": [30.0],
            }
        )
        prov_df = pd.DataFrame(
            {
                "tipo_evento": ["Dividendo"],
                "produto": ["CPFE3"],
                "valor_liquido": [20.0],
            }
        )
        res = reconciliar_proventos(mov_df, prov_df)
        assert len(res) == 2
        b3 = res[res["ativo"] == "B3SA3"].iloc[0]
        assert b3["total_movimentacao"] == 30.0
        assert b3["total_extrato_proventos"] == 0.0
        assert b3["status"] == "Divergente"

        cpf = res[res["ativo"] == "CPFE3"].iloc[0]
        assert cpf["total_movimentacao"] == 0.0
        assert cpf["total_extrato_proventos"] == 20.0
        assert cpf["status"] == "Divergente"

    def test_ignora_operacoes_que_nao_sao_proventos_na_movimentacao(self):
        mov_df = pd.DataFrame(
            {
                "movimentacao": ["Compra", "Venda", "Dividendo"],
                "entrada_saida": ["Debito", "Credito", "Credito"],
                "produto": ["PETR4", "PETR4", "PETR4"],
                "valor_liquido": [1000.0, 500.0, 15.0],
            }
        )
        prov_df = pd.DataFrame(
            {
                "tipo_evento": ["Dividendo"],
                "produto": ["PETR4"],
                "valor_liquido": [15.0],
            }
        )
        res = reconciliar_proventos(mov_df, prov_df)
        assert len(res) == 1
        assert res.iloc[0]["total_movimentacao"] == 15.0
        assert res.iloc[0]["status"] == "OK"
