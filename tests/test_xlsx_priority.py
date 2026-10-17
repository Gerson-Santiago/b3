"""
TDD - Verifica as 7 recomendacoes do loader B3 com testes rigorosos.
Usa apenas arquivos sinteticos criados em tmp_path (nenhum arquivo real).
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from dashboard.loaders.movimentacao import read_movimentacao_excel, read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_excel, read_posicao_file
from tests.xlsx_builders import make_mov_csv, make_mov_xlsx, make_pos_xlsx

try:
    from dashboard.loader import find_latest
except ImportError:
    find_latest = None

ROOT = Path(__file__).resolve().parents[1]


class TestFindLatest:
    def test_find_latest_prefers_xlsx_over_csv(self, tmp_path):
        assert find_latest is not None, "find_latest nao implementada em dashboard.loader"
        csv_file = tmp_path / "movimentacao-2026-10-16.csv"
        xlsx_file = tmp_path / "movimentacao-2026-10-16.xlsx"
        make_mov_csv(csv_file)
        make_mov_xlsx(xlsx_file)

        selected = find_latest(tmp_path, "movimentacao")
        assert selected == xlsx_file
        assert selected.suffix.lower() == ".xlsx"

    def test_find_latest_two_xlsx_different_dates(self, tmp_path):
        assert find_latest is not None, "find_latest nao implementada em dashboard.loader"
        old_file = tmp_path / "movimentacao-2026-10-15.xlsx"
        new_file = tmp_path / "movimentacao-2026-10-17.xlsx"
        make_mov_xlsx(old_file)
        make_mov_xlsx(new_file)

        selected = find_latest(tmp_path, "movimentacao")
        assert selected == new_file

    def test_find_latest_fallback_to_csv_when_no_xlsx(self, tmp_path):
        assert find_latest is not None, "find_latest nao implementada em dashboard.loader"
        csv_file = tmp_path / "movimentacao-2026-10-16.csv"
        make_mov_csv(csv_file)

        selected = find_latest(tmp_path, "movimentacao")
        assert selected == csv_file


class TestOpenpyxlEngine:
    def test_posicao_passes_openpyxl_engine(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        make_pos_xlsx(xlsx)
        with patch("pandas.ExcelFile", wraps=pd.ExcelFile) as mock_excel:
            read_posicao_excel(xlsx)
            _, kwargs = mock_excel.call_args
            assert kwargs.get("engine") == "openpyxl"

    def test_movimentacao_passes_openpyxl_engine(self, tmp_path):
        xlsx = tmp_path / "movimentacao.xlsx"
        make_mov_xlsx(xlsx)
        with patch("pandas.ExcelFile", wraps=pd.ExcelFile) as mock_excel:
            read_movimentacao_excel(xlsx)
            _, kwargs = mock_excel.call_args
            assert kwargs.get("engine") == "openpyxl"


class TestAllSheetsPosicao:
    def test_reads_acoes_bdr_tesouro(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        make_pos_xlsx(xlsx)
        cats = set(read_posicao_file(xlsx)["categoria"].unique())
        assert {"AÇÕES", "BDR", "TESOURO"} <= cats

    def test_row_count_without_total_rows(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        make_pos_xlsx(xlsx)
        assert len(read_posicao_file(xlsx)) == 3


class TestNoTotalOrEmptyRows:
    def _pos(self, tmp_path):
        xlsx = tmp_path / "posicao.xlsx"
        make_pos_xlsx(xlsx)
        return read_posicao_file(xlsx)

    def test_no_total_string_in_produto(self, tmp_path):
        df = self._pos(tmp_path)
        assert not df["produto"].astype(str).str.lower().str.contains("total").any()

    def test_no_all_nan_rows(self, tmp_path):
        df = self._pos(tmp_path)
        assert not df.isnull().all(axis=1).any()

    def test_produto_not_null(self, tmp_path):
        df = self._pos(tmp_path)
        assert df["produto"].notna().all()


class TestMostRecentFileViaGlob:
    def test_app_py_has_no_hardcoded_dates(self):
        app_src = (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8")
        assert not re.search(r"(movimentacao|posicao)-\d{4}-\d{2}-\d{2}", app_src)


class TestAppLevelErrors:
    def test_app_movimentacao_raises_on_corrupt_file(self, monkeypatch):
        import dashboard.app as app

        def fake_read(path):
            raise ValueError("Arquivo de movimentacao corrompido")

        monkeypatch.setattr(app, "read_movimentacao_file", fake_read)
        with pytest.raises(Exception):
            app.load_default_movimentacao()

    def test_app_posicao_raises_on_corrupt_file(self, monkeypatch):
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


class TestNoDependencyCalamine:
    def test_calamine_not_in_requirements(self):
        req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
        assert "calamine" not in req

    def test_calamine_not_used_in_loaders(self):
        for py in (ROOT / "dashboard" / "loaders").glob("*.py"):
            assert "calamine" not in py.read_text(encoding="utf-8")
