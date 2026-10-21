from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

from dashboard.utils import find_latest

try:
    from dashboard.loaders.movimentacao import read_movimentacao_file
    from dashboard.loaders.posicao import read_posicao_file
except ImportError:  # pragma: no cover
    from loaders.movimentacao import read_movimentacao_file
    from loaders.posicao import read_posicao_file


def read_b3_file(file_source: Union[str, Path, BytesIO]):
    if file_source is None:
        raise ValueError("Arquivo B3 não informado.")

    if hasattr(file_source, "read"):
        name = str(getattr(file_source, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            try:
                return read_posicao_file(file_source)
            except Exception:
                return read_movimentacao_file(file_source)
        return read_movimentacao_file(file_source)

    path = Path(file_source)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            return read_posicao_file(path)
        except Exception:
            return read_movimentacao_file(path)
    return read_movimentacao_file(path)
