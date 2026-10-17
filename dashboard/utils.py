from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


def _parse_file_date(path: Path):
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", path.name)
    if match:
        return tuple(int(part) for part in match.groups())
    return (0, 0, 0)


def find_latest(folder, prefix: str):
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

    xlsx = [path for path in candidates if path.suffix.lower() in {".xlsx", ".xls"}]
    if xlsx:
        candidates = xlsx

    return max(candidates, key=lambda path: (_parse_file_date(path), path.stat().st_mtime, path.name))


def parse_money(value: Any):
    if value is None or pd.isna(value):
        return pd.NA

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if not text:
        return pd.NA

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = text.replace("R$", "").replace(" ", "")
    text = text.replace("USD", "").replace("BRL", "")
    text = text.replace("(", "").replace(")", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if len(text.split(",")[-1]) <= 2:
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "." in text:
        if text.count(".") > 1:
            parts = text.split(".")
            if len(parts[-1]) <= 2:
                text = "".join(parts[:-1]) + "." + parts[-1]
            else:
                text = "".join(parts)
        elif len(text.split(".")[-1]) > 2:
            text = text.replace(".", "")

    try:
        number = float(text)
        return -number if negative else number
    except ValueError:
        return pd.NA


def parse_qtd(value: Any):
    if value is None or pd.isna(value):
        return pd.NA

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip().replace(" ", "")
    if not text:
        return pd.NA

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    elif "." in text and text.count(".") > 1:
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return pd.NA
