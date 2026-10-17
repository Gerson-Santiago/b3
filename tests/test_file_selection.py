import re
from pathlib import Path

import pandas as pd

from dashboard import app
from dashboard.utils import find_latest


def test_find_latest_chooses_newest_xlsx(tmp_path):
    old = tmp_path / "movimentacao-2026-10-10.xlsx"
    new = tmp_path / "movimentacao-2026-10-20.xlsx"
    pd.DataFrame({"produto": ["PETR4"], "quantidade": [1]}).to_excel(old, index=False, engine="openpyxl")
    pd.DataFrame({"produto": ["VALE3"], "quantidade": [2]}).to_excel(new, index=False, engine="openpyxl")

    selected = find_latest(tmp_path, "movimentacao")

    assert selected == new


def test_find_latest_prefers_xlsx_over_csv(tmp_path):
    csv_file = tmp_path / "movimentacao-2026-10-20.csv"
    xlsx_file = tmp_path / "movimentacao-2026-10-18.xlsx"
    csv_file.write_text("produto;quantidade\nPETR4;10\n", encoding="utf-8")
    pd.DataFrame({"produto": ["VALE3"], "quantidade": [2]}).to_excel(xlsx_file, index=False, engine="openpyxl")

    selected = find_latest(tmp_path, "movimentacao")

    assert selected == xlsx_file


def test_load_default_movimentacao_shows_read_error(monkeypatch):
    calls = []

    monkeypatch.setattr(app, "find_latest", lambda folder, prefix: Path("/tmp/movimentacao.xlsx"))
    monkeypatch.setattr(app, "read_movimentacao_file", lambda path: (_ for _ in ()).throw(ValueError("arquivo corrompido")))
    monkeypatch.setattr(app.st, "error", lambda msg: calls.append(msg))

    try:
        app.load_default_movimentacao()
        assert False, "esperava exceção"
    except ValueError as exc:
        assert "arquivo corrompido" in str(exc)

    assert any("arquivo corrompido" in message for message in calls)


def test_app_py_has_no_hardcoded_dates():
    app_src = (Path(__file__).resolve().parents[1] / "dashboard" / "app.py").read_text(encoding="utf-8")
    assert not re.search(r"(movimentacao|posicao)-\d{4}-\d{2}-\d{2}", app_src)
