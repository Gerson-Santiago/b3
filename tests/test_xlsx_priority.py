"""
TDD - Verifica as 7 recomendacoes do loader B3 com testes rigorosos.
Usa apenas arquivos sinteticos criados em tmp_path (nenhum arquivo real).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.loaders.movimentacao import read_movimentacao_excel, read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_excel, read_posicao_file

try:
    from dashboard.loader import find_latest
except ImportError:
    find_latest = None

# ---------------------------------------------------------------------------
# helpers para criar xlsx e csv sinteticos
# ---------------------------------------------------------------------------

MOV_COLUMNS = [
    "Entrada/Saida", "Data", "Movimentacao", "Produto",
    "Instituicao", "Quantidade", "Preco unitario", "Valor da Operacao",
]

POS_ACOES_COLUMNS = [
    "Produto", "Instituicao", "Conta", "Codigo de Negociacao",
    "CNPJ da Empresa", "Codigo ISIN / Distribuicao", "Tipo",
    "Escriturador", "Quantidade", "Quantidade Disponivel",
    "Quantidade Indisponivel", "Motivo", "Preco de Fechamento",
    "Valor Atualizado",
]

POS_BDR_COLUMNS = [
    "Produto", "Instituicao", "Conta", "Codigo de Negociacao",
    "Codigo ISIN / Distribuicao", "Tipo", "Escriturador",
    "Quantidade", "Quantidade Disponivel", "Quantidade Indisponivel",
    "Motivo", "Preco de Fechamento", "Valor Atualizado",
]

POS_TESOURO_COLUMNS = [
    "Produto", "Instituicao", "Codigo ISIN", "Indexador", "Vencimento",
    "Quantidade", "Quantidade Disponivel", "Quantidade Indisponivel",
    "Motivo", "Valor Aplicado", "Valor bruto", "Valor liquido",
    "Valor Atualizado",
]


def _make_mov_xlsx(path: Path) -> None:
    rows = [
        ["Credito", "06/08/2026", "Compra", "PETR4", "Corretora X", 10, 30.0, 300.0],
        ["Credito", "07/08/2026", "Compra", "VALE3", "Corretora X",  5, 60.0, 300.0],
    ]
    cols = [
        "Entrada/Sa\xedda", "Data", "Movimenta\xe7\xe3o", "Produto",
        "Institui\xe7\xe3o", "Quantidade", "Pre\xe7o unit\xe1rio", "Valor da Opera\xe7\xe3o",
    ]
    df = pd.DataFrame(rows, columns=cols)
    df.to_excel(path, index=False, engine="openpyxl")


def _make_mov_csv(path: Path) -> None:
    rows = (
        "Entrada/Sa\xedda;Data;Movimenta\xe7\xe3o;Produto;Institui\xe7\xe3o;Quantidade;Pre\xe7o unit\xe1rio;Valor da Opera\xe7\xe3o\n"
        "Credito;06/08/2026;Compra;PETR4;Corretora X;10;30,00;300,00\n"
    )
    path.write_text(rows, encoding="utf-8-sig")


def _make_pos_xlsx(path: Path, acoes_val: float = 100.0, bdr_val: float = 200.0, tesouro_val: float = 50.0) -> None:
    """Cria xlsx de posicao com 3 abas e linha de Total ao final de cada."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # --- Acoes ---
        df_a = pd.DataFrame(
            [["PETR4 - PETROBRAS", "Corr", 12345, "PETR4", 0, "BR", "ON", "Banco",
              10, 10, 0, "-", 10.0, acoes_val]],
            columns=POS_ACOES_COLUMNS,
        )
        total_label = pd.DataFrame(
            [[None] * (len(POS_ACOES_COLUMNS) - 1) + ["Total"]], columns=POS_ACOES_COLUMNS
        )
        total_value = pd.DataFrame(
            [[None] * (len(POS_ACOES_COLUMNS) - 1) + [acoes_val]], columns=POS_ACOES_COLUMNS
        )
        pd.concat([df_a, total_label, total_value]).to_excel(writer, sheet_name="Acoes", index=False)

        # --- BDR ---
        df_b = pd.DataFrame(
            [["GOGL35 - ALPHABET", "Corr", 12345, "GOGL35", "BR", "BDR", "Banco",
              5, 5, 0, "-", 40.0, bdr_val]],
            columns=POS_BDR_COLUMNS,
        )
        total_label_b = pd.DataFrame(
            [[None] * (len(POS_BDR_COLUMNS) - 1) + ["Total"]], columns=POS_BDR_COLUMNS
        )
        total_value_b = pd.DataFrame(
            [[None] * (len(POS_BDR_COLUMNS) - 1) + [bdr_val]], columns=POS_BDR_COLUMNS
        )
        pd.concat([df_b, total_label_b, total_value_b]).to_excel(writer, sheet_name="BDR", index=False)

        # --- Tesouro Direto ---
        df_t = pd.DataFrame(
            [["Tesouro Selic 2029", "Corr", "BRSTNCLF1R91", "SELIC", "01/03/2029",
              1, 1, 0, "-", 50.0, 50.0, 50.0, tesouro_val]],
            columns=POS_TESOURO_COLUMNS,
        )
        total_label_t = pd.DataFrame(
            [[None] * (len(POS_TESOURO_COLUMNS) - 1) + ["Total"]], columns=POS_TESOURO_COLUMNS
        )
        total_value_t = pd.DataFrame(
            [[None] * (len(POS_TESOURO_COLUMNS) - 1) + [tesouro_val]], columns=POS_TESOURO_COLUMNS
        )
        pd.concat([df_t, total_label_t, total_value_t]).to_excel(writer, sheet_name="Tesouro Direto", index=False)


# ===========================================================================
# REC 1 & REC 5 - Escolha de arquivo com find_latest (XLSX prioritario e mais recente)
# ===========================================================================
class TestFindLatest:
    def test_find_latest_prefers_xlsx_over_csv(self, tmp_path):
        """REC 1: Quando ha XLSX e CSV na pasta, find_latest escolhe o XLSX."""
        assert find_latest is not None, "find_latest nao implementada em dashboard.loader"
        csv_file = tmp_path / "movimentacao-2026-10-16.csv"
        xlsx_file = tmp_path / "movimentacao-2026-10-16.xlsx"
        _make_mov_csv(csv_file)
        _make_mov_xlsx(xlsx_file)

        selected = find_latest(tmp_path, "movimentacao")
        assert selected is not None, "Nenhum arquivo retornado"
        assert selected.suffix.lower() == ".xlsx", (
            f"Esperado .xlsx prioritario, mas retornou: {selected}"
        )
        assert selected == xlsx_file

    def test_find_latest_two_xlsx_different_dates(self, tmp_path):
        """REC 5: Quando ha dois XLSX de datas diferentes, escolhe o mais recente."""
        assert find_latest is not None, "find_latest nao implementada em dashboard.loader"
        old_file = tmp_path / "movimentacao-2026-10-15.xlsx"
        new_file = tmp_path / "movimentacao-2026-10-17.xlsx"
        _make_mov_xlsx(old_file)
        _make_mov_xlsx(new_file)

        selected = find_latest(tmp_path, "movimentacao")
        assert selected is not None, "Nenhum arquivo retornado"
        assert selected == new_file, (
            f"Esperado arquivo mais recente '{new_file.name}', mas selecionou '{selected.name}'"
        )

    def test_find_latest_fallback_to_csv_when_no_xlsx(self, tmp_path):
        """REC 1: Quando so ha CSV na pasta, faz fallback para o CSV."""
        assert find_latest is not None, "find_latest nao implementada em dashboard.loader"
        csv_file = tmp_path / "movimentacao-2026-10-16.csv"
        _make_mov_csv(csv_file)

        selected = find_latest(tmp_path, "movimentacao")
        assert selected is not None, "Nenhum arquivo retornado"
        assert selected == csv_file


# ===========================================================================
# REC 2 - engine="openpyxl" explicito (verificado com mock em pd.ExcelFile)
# ===========================================================================
class TestOpenpyxlEngine:
    def test_posicao_passes_openpyxl_engine(self, tmp_path):
        """REC 2: Ler Excel com engine='openpyxl' explicito em posicao."""
        xlsx = tmp_path / "posicao.xlsx"
        _make_pos_xlsx(xlsx)
        with patch("pandas.ExcelFile", wraps=pd.ExcelFile) as mock_excel:
            read_posicao_excel(xlsx)
            assert mock_excel.called, "pd.ExcelFile nao foi chamado"
            _, kwargs = mock_excel.call_args
            assert kwargs.get("engine") == "openpyxl", (
                f"Esperado engine='openpyxl', obtido: {kwargs.get('engine')}"
            )

    def test_movimentacao_passes_openpyxl_engine(self, tmp_path):
        """REC 2: Ler Excel com engine='openpyxl' explicito em movimentacao."""
        xlsx = tmp_path / "movimentacao.xlsx"
        _make_mov_xlsx(xlsx)
        with patch("pandas.ExcelFile", wraps=pd.ExcelFile) as mock_excel:
            read_movimentacao_excel(xlsx)
            assert mock_excel.called, "pd.ExcelFile nao foi chamado"
            _, kwargs = mock_excel.call_args
            assert kwargs.get("engine") == "openpyxl", (
                f"Esperado engine='openpyxl', obtido: {kwargs.get('engine')}"
            )


# ===========================================================================
# REC 3 - Le todas as 3 abas da posicao
# ===========================================================================
class TestAllSheetsPosicao:
    def test_reads_acoes_bdr_tesouro(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        _make_pos_xlsx(xlsx)

        df = read_posicao_file(xlsx)
        cats = set(df["categoria"].unique())
        assert "AÇÕES"   in cats, "Aba Acoes nao foi lida"
        assert "BDR"     in cats, "Aba BDR nao foi lida"
        assert "TESOURO" in cats, "Aba Tesouro Direto nao foi lida"

    def test_row_count_without_total_rows(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        _make_pos_xlsx(xlsx)
        df = read_posicao_file(xlsx)
        assert len(df) == 3, f"Esperado 3 linhas de dados, obtido {len(df)}"


# ===========================================================================
# REC 4 - Sem linhas de Total nem linhas vazias
# ===========================================================================
class TestNoTotalOrEmptyRows:
    def test_no_total_string_in_produto(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        _make_pos_xlsx(xlsx)
        df = read_posicao_file(xlsx)

        has_total = df["produto"].astype(str).str.lower().str.contains("total").any()
        assert not has_total, "Linha de 'Total' encontrada no DataFrame final"

    def test_no_all_nan_rows(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        _make_pos_xlsx(xlsx)
        df = read_posicao_file(xlsx)
        assert not df.isnull().all(axis=1).any(), "Ha linhas completamente vazias"

    def test_produto_not_null(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        _make_pos_xlsx(xlsx)
        df = read_posicao_file(xlsx)
        assert df["produto"].notna().all(), "Ha produtos nulos no DataFrame final"


# ===========================================================================
# REC 5 - Sem nomes de arquivo com data fixa no app.py
# ===========================================================================
class TestMostRecentFileViaGlob:
    def test_app_py_has_no_hardcoded_dates(self):
        """REC 5: app.py nao deve conter nomes com data fixa hardcoded."""
        app_src = (
            Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
        ).read_text(encoding="utf-8")
        assert not re.search(r"(movimentacao|posicao)-\d{4}-\d{2}-\d{2}", app_src), (
            "app.py contem nomes de arquivo com datas fixas hardcoded."
        )


# ===========================================================================
# REC 6 - Sem 'except Exception: continue' silencioso - erro visivel no app
# ===========================================================================
class TestAppLevelErrors:
    def test_app_movimentacao_raises_on_corrupt_file(self, monkeypatch):
        """REC 6: load_default_movimentacao nao deve engolir erro e retornar DataFrame vazio."""
        import dashboard.app as app

        def fake_read(path):
            raise ValueError("Arquivo de movimentacao corrompido")

        monkeypatch.setattr(app, "read_movimentacao_file", fake_read)

        with pytest.raises(Exception):
            app.load_default_movimentacao()

    def test_app_posicao_raises_on_corrupt_file(self, monkeypatch):
        """REC 6: load_default_posicao nao deve engolir erro e retornar DataFrame vazio."""
        import dashboard.app as app

        def fake_read(path):
            raise ValueError("Arquivo de posicao corrompido")

        monkeypatch.setattr(app, "read_posicao_file", fake_read)

        with pytest.raises(Exception):
            app.load_default_posicao()

    def test_loader_corrupt_posicao_xlsx_raises(self, tmp_path):
        bad = tmp_path / "corrompido.xlsx"
        bad.write_bytes(b"isso nao e um xlsx valido")
        with pytest.raises(Exception):
            read_posicao_file(bad)

    def test_loader_corrupt_movimentacao_xlsx_raises(self, tmp_path):
        bad = tmp_path / "corrompido.xlsx"
        bad.write_bytes(b"garbage data not excel")
        with pytest.raises(Exception):
            read_movimentacao_file(bad)


# ===========================================================================
# REC 7 - Sem calamine
# ===========================================================================
class TestNoDependencyCalamine:
    def test_calamine_not_in_requirements(self):
        req = (
            Path(__file__).resolve().parents[1] / "requirements.txt"
        ).read_text(encoding="utf-8").lower()
        assert "calamine" not in req, "calamine esta no requirements.txt sem justificativa"

    def test_calamine_not_used_in_loaders(self):
        loaders_dir = Path(__file__).resolve().parents[1] / "dashboard" / "loaders"
        for py in loaders_dir.glob("*.py"):
            src = py.read_text(encoding="utf-8")
            assert "calamine" not in src, f"calamine encontrado em {py.name}"
