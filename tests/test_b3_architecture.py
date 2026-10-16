import unittest
from pathlib import Path

import pandas as pd

from dashboard.columns import ALIASES_POS, normaliza_colunas
from dashboard.loader import read_b3_file
from dashboard.loaders.movimentacao import parse_money, read_movimentacao_file
from dashboard.loaders.posicao import _categorizar_sheet, read_posicao_file
from dashboard.metrics import (
    compute_dy,
    compute_position,
    compute_position_categoria,
    compute_preco_medio,
    compute_proventos,
)


class B3ArchitectureTest(unittest.TestCase):
    def test_movimentacao_has_expected_columns(self):
        file_path = Path(__file__).resolve().parents[1] / "csv" / "movimentacao-2026-10-16-18-13-17.csv"
        df = read_movimentacao_file(file_path)
        self.assertIn("entrada_saida", df.columns)
        self.assertIn("data", df.columns)
        self.assertIn("produto", df.columns)
        self.assertIn("valor_operacao", df.columns)

    def test_posicao_has_expected_columns(self):
        file_path = sorted((Path(__file__).resolve().parents[1] / "xlsx" / "posicao").glob("*.xlsx"))[-1]
        df = read_posicao_file(file_path)
        self.assertIn("produto", df.columns)
        self.assertIn("quantidade", df.columns)
        self.assertIn("categoria", df.columns)
        self.assertTrue(df["produto"].notna().all())
        self.assertFalse(df["produto"].astype(str).str.lower().str.contains("total").any())


class B3ColumnsAndParsingTest(unittest.TestCase):
    def test_normaliza_colunas_maps_aliases(self):
        df = pd.DataFrame({"Produto": ["PETR4"], "Quantidade Disponível": [5], "Valor Atualizado": [123.45]})
        out = normaliza_colunas(df, ALIASES_POS)
        self.assertIn("produto", out.columns)
        self.assertIn("quantidade_disponivel", out.columns)
        self.assertIn("valor_atualizado", out.columns)

    def test_parse_money_handles_brazilian_formats(self):
        self.assertEqual(parse_money("R$ 1.234,56"), 1234.56)
        self.assertEqual(parse_money("1.000,00"), 1000.0)
        self.assertTrue(pd.isna(parse_money("")))


class B3LoaderAndMetricsTest(unittest.TestCase):
    def test_categorizar_sheet_classifies_by_sheet(self):
        self.assertEqual(_categorizar_sheet("Tesouro Direto"), "TESOURO")
        self.assertEqual(_categorizar_sheet("BDR"), "BDR")
        self.assertEqual(_categorizar_sheet("Acoes"), "ACOES")

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
                "produto": ["PETR4", "GOGL35 BDR", "Tesouro Selic 2028"],
                "qtd_liquida": [10, 5, 1],
                "valor_liquido": [100, 80, 50],
            }
        )
        result = compute_position_categoria(df)
        resumo = dict(zip(result["categoria"], result["valor"]))
        self.assertEqual(resumo["ACOES"], 100)
        self.assertEqual(resumo["BDR"], 80)
        self.assertEqual(resumo["TESOURO"], 50)

    def test_compute_proventos_keeps_only_credits_not_purchases(self):
        df = pd.DataFrame(
            {
                "mes": ["2026-10", "2026-10", "2026-10", "2026-11"],
                "entrada_saida": ["credito", "credito", "debito", "credito"],
                "movimentacao": ["juros", "compra", "venda", "dividendo"],
                "valor_liquido": [150, -500, 100, 70],
            }
        )
        result = compute_proventos(df)
        self.assertEqual(result["valor_liquido"].sum(), 220)

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

    def test_compute_preco_medio_uses_buy_volume(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "PETR4", "VALE3", "VALE3"],
                "quantidade": [10, 5, 2, -1],
                "valor_operacao": [200, 100, 40, -10],
            }
        )
        result = compute_preco_medio(df)
        petr = result[result["produto"] == "PETR4"].iloc[0]
        self.assertAlmostEqual(petr["preco_medio"], 20.0)
        self.assertAlmostEqual(petr["custo_total"], 300.0)

    def test_read_b3_file_dispatches_csv_and_xlsx(self):
        csv_path = Path(__file__).resolve().parents[1] / "csv" / "movimentacao-2026-10-16-18-13-17.csv"
        xlsx_path = sorted((Path(__file__).resolve().parents[1] / "xlsx" / "posicao").glob("*.xlsx"))[-1]

        csv_df = read_b3_file(csv_path)
        xlsx_df = read_b3_file(xlsx_path)

        self.assertIn("produto", csv_df.columns)
        self.assertIn("categoria", xlsx_df.columns)
        self.assertIn("valor_operacao", csv_df.columns)


if __name__ == "__main__":
    unittest.main()
