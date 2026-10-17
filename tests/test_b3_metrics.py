import unittest
from pathlib import Path

import pandas as pd

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.metrics import (
    classificar_ativo,
    compute_dy,
    compute_position,
    compute_position_categoria,
    compute_preco_medio,
    compute_proventos,
)
from dashboard.models.movimentacao import TipoMovimentacao, classificar_movimentacao


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _mov(produtos, datas, qtds, valores, movs, sentidos):
    return pd.DataFrame(
        {
            "produto": produtos,
            "data": datas,
            "qtd_liquida": qtds,
            "valor_liquido": valores,
            "movimentacao": movs,
            "entrada_saida": sentidos,
        }
    )


class B3LoaderAndMetricsTest(unittest.TestCase):
    def test_classificar_ativo_recognizes_bdr_tickers_without_bdr_word(self):
        self.assertEqual(classificar_ativo("GOGL35"), "BDR")
        self.assertEqual(classificar_ativo("MSFT34"), "BDR")
        self.assertEqual(classificar_ativo("PETR4"), "AÇÕES")

    def test_compute_position_groups_by_product(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "PETR4", "VALE3"],
                "qtd_liquida": [5, 3, 2],
                "valor_liquido": [90, 60, 40],
            }
        )
        result = compute_position(df)
        self.assertEqual(result[result["produto"] == "PETR4"]["quantidade"].iloc[0], 8)
        self.assertEqual(result[result["produto"] == "PETR4"]["valor"].iloc[0], 150)
        self.assertEqual(result[result["produto"] == "VALE3"]["quantidade"].iloc[0], 2)

    def test_compute_position_categoria_aggregates_by_category(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "GOGL35 - ALPHABET INC.", "Tesouro Selic 2028"],
                "qtd_liquida": [10, 5, 1],
                "valor_liquido": [100, 80, 50],
            }
        )
        result = compute_position_categoria(df)
        resumo = dict(zip(result["categoria"], result["valor"]))
        self.assertEqual(resumo["AÇÕES"], 100)
        self.assertEqual(resumo["BDR"], 80)
        self.assertEqual(resumo["TESOURO"], 50)

    def test_compute_preco_medio_keeps_liquidacao_rows_and_matches_broker_reference(self):
        df = _mov(
            ["GOGL35", "GOGL35", "CPFE3", "CPFE3", "PETR4", "PETR4"],
            ["2021-11-10", "2021-11-26", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            [5, 12, 1, 2, 10, 13],
            [318.90, 765.36, 30.78, 61.56, 326.13, 423.96],
            ["transferência - liquidação"] * 2 + ["compra"] * 4,
            ["credito"] * 6,
        )
        result = compute_preco_medio(df)
        googl = result[result["produto"] == "GOGL35"].iloc[0]
        cpfe = result[result["produto"] == "CPFE3"].iloc[0]
        petr = result[result["produto"] == "PETR4"].iloc[0]
        self.assertAlmostEqual(googl["quantidade"], 17.0)
        self.assertAlmostEqual(googl["custo_total"], 1084.26)
        self.assertAlmostEqual(googl["preco_medio"], 63.78, places=2)
        self.assertAlmostEqual(cpfe["preco_medio"], 30.78, places=2)
        self.assertAlmostEqual(petr["preco_medio"], 32.61, places=2)

    def test_compute_preco_medio_googl35_uses_real_xlsx_fixture_and_corporate_events(self):
        df = read_movimentacao_file(FIXTURES_DIR / "movimentacao_7_ativos.xlsx")
        googl = df[df["produto"].astype(str).str.contains("GOGL35", case=False, na=False)].copy()
        googl_result = compute_preco_medio(googl.sort_values("data", kind="mergesort"))
        googl_result = googl_result[googl_result["produto"].astype(str).str.contains("GOGL35", case=False, na=False)].iloc[0]
        self.assertAlmostEqual(googl_result["quantidade"], 17.0, places=5)
        self.assertAlmostEqual(googl_result["preco_medio"], 63.78, places=2)

    def test_classificacao_movimentacao_distinguishes_proventos_e_ajustes(self):
        self.assertEqual(classificar_movimentacao("dividendo"), TipoMovimentacao.PROVENTO)
        self.assertEqual(classificar_movimentacao("atualização"), TipoMovimentacao.PROVENTO)
        self.assertEqual(classificar_movimentacao("desdobro de ações"), TipoMovimentacao.DESDOBRAMENTO)
        self.assertEqual(classificar_movimentacao("grupamento"), TipoMovimentacao.GRUPAMENTO)
        self.assertEqual(classificar_movimentacao("compra"), TipoMovimentacao.COMPRA)
        self.assertEqual(classificar_movimentacao("venda"), TipoMovimentacao.VENDA)
        self.assertEqual(classificar_movimentacao("leilão de fração"), TipoMovimentacao.AJUSTE_QUANTIDADE)

    def test_compute_preco_medio_ignores_sell_events_without_masking_cost(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "PETR4", "PETR4"],
                "data": ["2024-01-10", "2024-01-15", "2024-01-20"],
                "movimentacao": ["compra", "venda", "compra"],
                "entrada_saida": ["credito", "debito", "credito"],
                "quantidade": [10, 3, 2],
                "valor_operacao": [300, 90, 70],
            }
        )
        df["qtd_liquida"] = df["quantidade"] * df["entrada_saida"].map({"credito": 1, "debito": -1})
        df["valor_liquido"] = df["valor_operacao"] * df["entrada_saida"].map({"credito": 1, "debito": -1})
        result = compute_preco_medio(df)
        petr = result[result["produto"] == "PETR4"].iloc[0]
        self.assertAlmostEqual(petr["quantidade"], 9.0)
        self.assertAlmostEqual(petr["custo_total"], 280.0)
        self.assertAlmostEqual(petr["preco_medio"], 31.11111111111111, places=4)

    def test_compute_preco_medio_googl35_handles_corporate_events(self):
        df = _mov(
            ["GOGL35"] * 8,
            ["2021-11-10", "2021-11-26", "2021-11-30", "2022-01-07", "2022-01-24", "2022-01-25", "2022-01-28", "2022-09-09"],
            [1, 1, 1, 2, 2, 3, 1, 0.6],
            [111.52, 109.07, 107.25, 214.06, 198.60, 288.00, 94.00, 27.62],
            ["transferência - liquidação"] * 7 + ["leilão de fração"],
            ["credito"] * 8,
        )
        split_df = _mov(
            ["GOGL35"] * 3,
            ["2022-07-19", "2022-08-30", "2022-08-31"],
            [209.0, 17.6, -0.6],
            [None, None, None],
            ["desdobro", "grupamento", "fração em ativos"],
            ["credito", "credito", "debito"],
        )
        googl = compute_preco_medio(pd.concat([df, split_df], ignore_index=True)).iloc[0]
        self.assertAlmostEqual(googl["quantidade"], 17.0, places=5)
        self.assertAlmostEqual(googl["custo_total"], 1084.23, places=2)
        self.assertAlmostEqual(googl["preco_medio"], 63.78, places=2)

    def test_compute_position_categoria_uses_sheet_category_when_available(self):
        df = pd.DataFrame(
            {
                "produto": ["GOGL35", "MSFT34", "TESOURO SELIC 2028"],
                "qtd_liquida": [17, 11, 1],
                "valor_liquido": [2489.48, 1256.2, 200.88],
                "categoria": ["BDR", "BDR", "TESOURO"],
            }
        )
        resumo = dict(zip(*[compute_position_categoria(df)[c] for c in ("categoria", "valor")]))
        self.assertEqual(resumo["BDR"], 3745.68)
        self.assertEqual(resumo["TESOURO"], 200.88)

    def test_compute_proventos_keeps_only_credits_not_purchases(self):
        df = pd.DataFrame(
            {
                "mes": ["2026-10", "2026-10", "2026-10", "2026-11"],
                "entrada_saida": ["credito", "credito", "debito", "credito"],
                "movimentacao": ["juros", "compra", "venda", "dividendo"],
                "valor_liquido": [150, -500, 100, 70],
            }
        )
        self.assertEqual(compute_proventos(df)["valor_liquido"].sum(), 220)

    def test_compute_proventos_classifica_tipos_corretamente(self):
        df = pd.DataFrame(
            {
                "mes": ["2026-10", "2026-10", "2026-10"],
                "entrada_saida": ["credito", "credito", "credito"],
                "movimentacao": ["dividendo", "juros sobre capital proprio", "rendimento"],
                "valor_liquido": [100.0, 50.0, 30.0],
            }
        )
        res = compute_proventos(df)
        self.assertIn("tipo_provento", res.columns)
        self.assertEqual(len(res), 3)
        tipos = dict(zip(res["tipo_provento"], res["valor_liquido"]))
        self.assertEqual(tipos["Dividendo"], 100.0)
        self.assertEqual(tipos["JCP"], 50.0)
        self.assertEqual(tipos["Rendimento FII"], 30.0)

    def test_compute_dy_uses_position_and_received_proceeds(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "VALE3"],
                "qtd_liquida": [10, 5],
                "valor_liquido": [500, 200],
                "entrada_saida": ["credito", "credito"],
                "movimentacao": ["juros", "juros"],
                "valor_operacao": [500, 200],
            }
        )
        result = compute_dy(df)
        pet = result[result["produto"] == "PETR4"].iloc[0]
        self.assertAlmostEqual(pet["dy_pct"], 100.0)

    def test_compute_preco_medio_uses_chronological_average_cost(self):
        df = _mov(
            ["PETR4", "PETR4", "PETR4", "PETR4", "VALE3", "VALE3"],
            ["2024-01-10", "2024-02-10", "2024-03-10", "2024-03-15", "2024-01-20", "2024-02-20"],
            [10, 5, -3, 2, 4, -1],
            [200, 100, -60, 0, 80, -20],
            ["compra", "compra", "venda", "bonificação", "compra", "venda"],
            ["credito", "credito", "debito", "credito", "credito", "debito"],
        )
        result = compute_preco_medio(df)
        petr = result[result["produto"] == "PETR4"].iloc[0]
        vale = result[result["produto"] == "VALE3"].iloc[0]
        self.assertAlmostEqual(petr["quantidade"], 14.0)
        self.assertAlmostEqual(petr["custo_total"], 240.0)
        self.assertAlmostEqual(petr["preco_medio"], 17.142857142857142, places=5)
        self.assertAlmostEqual(vale["quantidade"], 3.0)
        self.assertAlmostEqual(vale["custo_total"], 60.0)
        self.assertAlmostEqual(vale["preco_medio"], 20.0)

    def test_compute_preco_medio_restarts_after_position_zero(self):
        df = _mov(
            ["PETR4"] * 3,
            ["2024-01-01", "2024-02-01", "2024-03-01"],
            [10, -10, 5],
            [200, -200, 100],
            ["compra", "venda", "compra"],
            ["credito", "debito", "credito"],
        )
        petr = compute_preco_medio(df).iloc[0]
        self.assertAlmostEqual(petr["quantidade"], 5.0)
        self.assertAlmostEqual(petr["custo_total"], 100.0)
        self.assertAlmostEqual(petr["preco_medio"], 20.0)


if __name__ == "__main__":
    unittest.main()
