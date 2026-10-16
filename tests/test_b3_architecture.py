import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import dashboard.app as app
from dashboard.aliases.movimentacao import ALIASES_MOV
from dashboard.aliases.posicao import ALIASES_POS
from dashboard.columns import normaliza_colunas
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

    def test_default_data_prefers_xlsx_files(self):
        base_dir = Path(__file__).resolve().parents[1]
        movimentacao_xlsx = sorted((base_dir / "xlsx" / "movimentacao").glob("*.xlsx"))[-1]
        posicao_xlsx = sorted((base_dir / "xlsx" / "posicao").glob("*.xlsx"))[-1]

        with patch.object(app, "read_movimentacao_file", side_effect=lambda path: pd.DataFrame({"data": [pd.Timestamp("2026-10-16")], "valor_operacao": [1.0]})) as mock_mov:
            app.load_default_movimentacao()
            self.assertTrue(any(str(call.args[0]).endswith(str(movimentacao_xlsx)) for call in mock_mov.call_args_list))

        with patch.object(app, "read_posicao_file", side_effect=lambda path: pd.DataFrame({"produto": ["PETR4"], "categoria": ["ACOES"], "data": [pd.Timestamp("2026-10-16")]})) as mock_pos:
            app.load_default_posicao()
            self.assertTrue(any(str(call.args[0]).endswith(str(posicao_xlsx)) for call in mock_pos.call_args_list))


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
        self.assertEqual(parse_money(30.78), 30.78)
        self.assertEqual(parse_money(92.34), 92.34)
        self.assertEqual(parse_money(102.5), 102.5)
        self.assertTrue(pd.isna(parse_money("")))

    def test_aliases_match_real_b3_headers(self):
        self.assertIn("Entrada/Saída", ALIASES_MOV["entrada_saida"])
        self.assertIn("Data", ALIASES_MOV["data"])
        self.assertIn("Produto", ALIASES_POS["produto"])
        self.assertIn("Código de Negociação", ALIASES_POS["codigo_negociacao"])
        self.assertIn("Valor Atualizado", ALIASES_POS["valor_atualizado"])


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

    def test_compute_preco_medio_keeps_liquidacao_rows_and_matches_broker_reference(self):
        df = pd.DataFrame(
            {
                "produto": ["GOGL35", "GOGL35", "CPFE3", "CPFE3", "PETR4", "PETR4"],
                "data": [
                    "2021-11-10",
                    "2021-11-26",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "qtd_liquida": [5, 12, 1, 2, 10, 13],
                "valor_liquido": [318.90, 765.36, 30.78, 61.56, 326.13, 423.96],
                "movimentacao": [
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "compra",
                    "compra",
                    "compra",
                    "compra",
                ],
                "entrada_saida": ["credito", "credito", "credito", "credito", "credito", "credito"],
            }
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

    def test_classificacao_movimentacao_distinguishes_proventos_e_ajustes(self):
        from dashboard.models.movimentacao import TipoMovimentacao, classificar_movimentacao

        self.assertEqual(classificar_movimentacao("dividendo"), TipoMovimentacao.PROVENTO)
        self.assertEqual(classificar_movimentacao("desdobro de ações"), TipoMovimentacao.DESDOBRAMENTO)
        self.assertEqual(classificar_movimentacao("grupamento"), TipoMovimentacao.GRUPAMENTO)
        self.assertEqual(classificar_movimentacao("compra"), TipoMovimentacao.COMPRA)
        self.assertEqual(classificar_movimentacao("venda"), TipoMovimentacao.VENDA)
        self.assertEqual(classificar_movimentacao("leilão de fração"), TipoMovimentacao.AJUSTE_QUANTIDADE)

    def test_compute_preco_medio_googl35_handles_corporate_events(self):
        df = pd.DataFrame(
            {
                "produto": ["GOGL35"] * 8,
                "data": [
                    "2021-11-10",
                    "2021-11-26",
                    "2021-11-30",
                    "2022-01-07",
                    "2022-01-24",
                    "2022-01-25",
                    "2022-01-28",
                    "2022-09-09",
                ],
                "movimentacao": [
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "transferência - liquidação",
                    "leilão de fração",
                ],
                "entrada_saida": ["credito"] * 8,
                "qtd_liquida": [1, 1, 1, 2, 2, 3, 1, 0.6],
                "valor_liquido": [111.52, 109.07, 107.25, 214.06, 198.60, 288.00, 94.00, 27.62],
            }
        )

        split_df = pd.DataFrame(
            {
                "produto": ["GOGL35", "GOGL35", "GOGL35"],
                "data": ["2022-07-19", "2022-08-30", "2022-08-31"],
                "movimentacao": ["desdobro", "grupamento", "fração em ativos"],
                "entrada_saida": ["credito", "credito", "debito"],
                "qtd_liquida": [209.0, 17.6, -0.6],
                "valor_liquido": [None, None, None],
            }
        )

        df = pd.concat([df, split_df], ignore_index=True)
        result = compute_preco_medio(df)
        googl = result[result["produto"] == "GOGL35"].iloc[0]

        self.assertAlmostEqual(googl["quantidade"], 17.6, places=5)
        self.assertAlmostEqual(googl["custo_total"], 1150.12, places=2)
        self.assertAlmostEqual(googl["preco_medio"], 65.35, places=2)

    def test_compute_position_categoria_uses_sheet_category_when_available(self):
        df = pd.DataFrame(
            {
                "produto": ["GOGL35", "MSFT34", "TESOURO SELIC 2028"],
                "qtd_liquida": [17, 11, 1],
                "valor_liquido": [2489.48, 1256.2, 200.88],
                "categoria": ["BDR", "BDR", "TESOURO"],
            }
        )
        result = compute_position_categoria(df)
        resumo = dict(zip(result["categoria"], result["valor"]))
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

    def test_compute_preco_medio_uses_chronological_average_cost(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "PETR4", "PETR4", "PETR4", "VALE3", "VALE3"],
                "data": [
                    "2024-01-10",
                    "2024-02-10",
                    "2024-03-10",
                    "2024-03-15",
                    "2024-01-20",
                    "2024-02-20",
                ],
                "qtd_liquida": [10, 5, -3, 2, 4, -1],
                "valor_liquido": [200, 100, -60, 0, 80, -20],
                "movimentacao": ["compra", "compra", "venda", "bonificação", "compra", "venda"],
                "entrada_saida": ["credito", "credito", "debito", "credito", "credito", "debito"],
            }
        )
        result = compute_preco_medio(df)
        petr = result[result["produto"] == "PETR4"].iloc[0]
        self.assertAlmostEqual(petr["quantidade"], 14.0)
        self.assertAlmostEqual(petr["custo_total"], 240.0)
        self.assertAlmostEqual(petr["preco_medio"], 17.142857142857142, places=5)

        vale = result[result["produto"] == "VALE3"].iloc[0]
        self.assertAlmostEqual(vale["quantidade"], 3.0)
        self.assertAlmostEqual(vale["custo_total"], 60.0)
        self.assertAlmostEqual(vale["preco_medio"], 20.0)

    def test_compute_preco_medio_restarts_after_position_zero(self):
        df = pd.DataFrame(
            {
                "produto": ["PETR4", "PETR4", "PETR4"],
                "data": ["2024-01-01", "2024-02-01", "2024-03-01"],
                "qtd_liquida": [10, -10, 5],
                "valor_liquido": [200, -200, 100],
                "movimentacao": ["compra", "venda", "compra"],
                "entrada_saida": ["credito", "debito", "credito"],
            }
        )
        result = compute_preco_medio(df)
        petr = result[result["produto"] == "PETR4"].iloc[0]
        self.assertAlmostEqual(petr["quantidade"], 5.0)
        self.assertAlmostEqual(petr["custo_total"], 100.0)
        self.assertAlmostEqual(petr["preco_medio"], 20.0)

    def test_read_b3_file_dispatches_csv_and_xlsx(self):
        base_dir = Path(__file__).resolve().parents[1]
        csv_path = sorted((base_dir / "csv").glob("*.csv"))[-1]
        xlsx_path = sorted((base_dir / "xlsx" / "posicao").glob("*.xlsx"))[-1]

        csv_df = read_b3_file(csv_path)
        xlsx_df = read_b3_file(xlsx_path)

        self.assertIn("produto", csv_df.columns)
        self.assertIn("categoria", xlsx_df.columns)
        self.assertIn("valor_operacao", csv_df.columns)


if __name__ == "__main__":
    unittest.main()
