"""Testes unitários para build_calendario_proventos em dashboard/metrics/proventos.py."""
from __future__ import annotations

import pandas as pd
import pytest

from dashboard.metrics.proventos import build_calendario_proventos


class TestBuildCalendarioProventos:
    def test_df_nulo_ou_vazio_retorna_dataframe_vazio(self):
        vazio_none = build_calendario_proventos(None)
        assert isinstance(vazio_none, pd.DataFrame)
        assert list(vazio_none.columns) == ["data", "ativo", "tipo_provento", "valor_liquido"]
        assert vazio_none.empty

        vazio_df = build_calendario_proventos(pd.DataFrame())
        assert isinstance(vazio_df, pd.DataFrame)
        assert vazio_df.empty

    def test_df_sem_eventos_de_provento(self):
        df = pd.DataFrame(
            {
                "data": [pd.Timestamp("2024-01-15")],
                "movimentacao": ["Compra"],
                "entrada_saida": ["Credito"],
                "produto": ["PETR4"],
                "valor_liquido": [1000.0],
            }
        )
        res = build_calendario_proventos(df)
        assert res.empty

    def test_cenario_feliz_multiplos_proventos_ordenados_descendente(self):
        df = pd.DataFrame(
            {
                "data": [
                    pd.Timestamp("2024-02-15"),
                    pd.Timestamp("2024-05-20"),
                    pd.Timestamp("2024-01-10"),
                ],
                "movimentacao": [
                    "Rendimento",
                    "Dividendo",
                    "Juros Sobre Capital Próprio",
                ],
                "entrada_saida": ["Credito", "Credito", "Credito"],
                "produto": ["HGLG11", "PETR4", "B3SA3"],
                "ticker": ["HGLG11", "PETR4", "B3SA3"],
                "valor_liquido": [50.0, 150.0, 30.0],
            }
        )
        res = build_calendario_proventos(df)
        assert len(res) == 3
        # Ordenado por data mais recente no topo
        assert list(res["data"]) == [
            pd.Timestamp("2024-05-20"),
            pd.Timestamp("2024-02-15"),
            pd.Timestamp("2024-01-10"),
        ]
        assert list(res["tipo_provento"]) == ["Dividendo", "Rendimento FII", "JCP"]
        assert list(res["ativo"]) == ["PETR4", "HGLG11", "B3SA3"]
        assert list(res["valor_liquido"]) == [150.0, 50.0, 30.0]

    def test_fallback_produto_quando_nao_ha_ticker(self):
        df = pd.DataFrame(
            {
                "data": [pd.Timestamp("2024-03-01")],
                "movimentacao": ["Dividendo"],
                "entrada_saida": ["Credito"],
                "produto": ["VALE3 - VALE S.A."],
                "valor_liquido": [200.0],
            }
        )
        res = build_calendario_proventos(df)
        assert len(res) == 1
        assert res["ativo"].iloc[0] == "VALE3 - VALE S.A."
        assert res["tipo_provento"].iloc[0] == "Dividendo"

    def test_valor_liquido_negativo_e_clipado_para_zero(self):
        df = pd.DataFrame(
            {
                "data": [pd.Timestamp("2024-03-01")],
                "movimentacao": ["Dividendo"],
                "entrada_saida": ["Credito"],
                "produto": ["ITSA4"],
                "valor_liquido": [-10.0],
            }
        )
        res = build_calendario_proventos(df)
        assert res["valor_liquido"].iloc[0] == 0.0
