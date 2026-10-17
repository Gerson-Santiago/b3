import tempfile
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


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class B3ArchitectureTest(unittest.TestCase):
    def test_movimentacao_has_expected_columns(self):
        df = read_movimentacao_file(FIXTURES_DIR / "movimentacao_7_ativos.xlsx")
        self.assertIn("entrada_saida", df.columns)
        self.assertIn("data", df.columns)
        self.assertIn("produto", df.columns)
        self.assertIn("valor_operacao", df.columns)

    def test_posicao_has_expected_columns(self):
        df = read_posicao_file(FIXTURES_DIR / "posicao_7_ativos.xlsx")
        self.assertIn("produto", df.columns)
        self.assertIn("quantidade", df.columns)
        self.assertIn("categoria", df.columns)
        self.assertTrue(df["produto"].notna().all())
        self.assertFalse(df["produto"].astype(str).str.lower().str.contains("total").any())

    def test_default_data_prefers_xlsx_files(self):
        movimentacao_xlsx = FIXTURES_DIR / "movimentacao_7_ativos.xlsx"
        posicao_xlsx = FIXTURES_DIR / "posicao_7_ativos.xlsx"

        with patch.object(app, "find_latest", side_effect=lambda folder, prefix: movimentacao_xlsx if "movimentacao" in prefix else posicao_xlsx), patch.object(app, "read_movimentacao_file", side_effect=lambda path: pd.DataFrame({"data": [pd.Timestamp("2026-10-16")], "valor_operacao": [1.0]})) as mock_mov:
            app.load_default_movimentacao()
            self.assertTrue(any(str(call.args[0]).endswith(str(movimentacao_xlsx)) for call in mock_mov.call_args_list))

        with patch.object(app, "find_latest", side_effect=lambda folder, prefix: posicao_xlsx), patch.object(app, "read_posicao_file", side_effect=lambda path: pd.DataFrame({"produto": ["PETR4"], "categoria": ["ACOES"], "data": [pd.Timestamp("2026-10-16")]})) as mock_pos:
            app.load_default_posicao()
            self.assertTrue(any(str(call.args[0]).endswith(str(posicao_xlsx)) for call in mock_pos.call_args_list))

    def test_dashboard_uses_stretch_width(self):
        source = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
        rendered = source.read_text(encoding="utf-8")
        self.assertIn('width="stretch"', rendered)
        self.assertNotIn("use_container_width=True", rendered)


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
        self.assertTrue(pd.isna(parse_money("")))

    def test_aliases_match_real_b3_headers(self):
        self.assertIn("Entrada/Saída", ALIASES_MOV["entrada_saida"])
        self.assertIn("Data", ALIASES_MOV["data"])
        self.assertIn("Produto", ALIASES_POS["produto"])
        self.assertIn("Código de Negociação", ALIASES_POS["codigo_negociacao"])
        self.assertIn("Valor Atualizado", ALIASES_POS["valor_atualizado"])


class B3LoaderDispatchTest(unittest.TestCase):
    def test_categorizar_sheet_classifies_by_sheet(self):
        self.assertEqual(_categorizar_sheet("Tesouro Direto"), "TESOURO")
        self.assertEqual(_categorizar_sheet("BDR"), "BDR")
        self.assertEqual(_categorizar_sheet("Acoes"), "AÇÕES")

    def test_read_b3_file_dispatches_csv_and_xlsx(self):
        xlsx_df = read_b3_file(FIXTURES_DIR / "posicao_7_ativos.xlsx")
        self.assertIn("categoria", xlsx_df.columns)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8-sig") as f:
            f.write(
                "Entrada/Saída;Data;Movimentação;Produto;Instituição;Quantidade;Preço unitário;Valor da Operação\n"
                "Credito;06/08/2026;Compra;PETR4;Corretora X;10;30,00;300,00\n"
            )
            temp_csv = Path(f.name)
        try:
            csv_df = read_b3_file(temp_csv)
            self.assertIn("produto", csv_df.columns)
            self.assertIn("valor_operacao", csv_df.columns)
        finally:
            temp_csv.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
