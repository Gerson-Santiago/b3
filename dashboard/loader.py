from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Union

try:
    from dashboard.loaders.movimentacao import read_movimentacao_file as read_b3_csv
    from dashboard.loaders.posicao import read_posicao_file as read_b3_excel
except ImportError:  # pragma: no cover
    from loaders.movimentacao import read_movimentacao_file as read_b3_csv
    from loaders.posicao import read_posicao_file as read_b3_excel


def _parse_file_date(path: Path):
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", path.name)
    if match:
        return tuple(int(part) for part in match.groups())
    return (0, 0, 0)


def find_latest(folder: Union[str, Path], prefix: str):
    base_dir = Path(folder)
    if not base_dir.exists():
        return None

    candidates = []
    for path in sorted(base_dir.iterdir()):
        if not path.is_file() or path.name.startswith("~$"):
            continue
        if prefix.lower() not in path.name.lower():
            continue
        if path.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
            continue
        candidates.append(path)

    if not candidates:
        return None

    xlsx = [p for p in candidates if p.suffix.lower() in {".xlsx", ".xls"}]
    if xlsx:
        candidates = xlsx

    return max(candidates, key=lambda p: (_parse_file_date(p), p.stat().st_mtime))


def read_b3_file(file_source: Union[str, Path, BytesIO]):
    if file_source is None:
        raise ValueError("Arquivo B3 não informado.")

    if hasattr(file_source, "read"):
        name = str(getattr(file_source, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            try:
                return read_b3_excel(file_source)
            except Exception:
                return read_b3_csv(file_source)
        return read_b3_csv(file_source)

    path = Path(file_source)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            return read_b3_excel(path)
        except Exception:
            return read_b3_csv(path)
    return read_b3_csv(path)
