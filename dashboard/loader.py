from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

try:
    from dashboard.loaders.movimentacao import read_movimentacao_file as read_b3_csv
    from dashboard.loaders.posicao import read_posicao_file as read_b3_excel
except ImportError:  # pragma: no cover
    from loaders.movimentacao import read_movimentacao_file as read_b3_csv
    from loaders.posicao import read_posicao_file as read_b3_excel


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
