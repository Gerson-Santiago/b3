from __future__ import annotations

import re
import unicodedata
from typing import Any


RENOMEACAO_ATIVOS: dict[str, str] = {
    "NUBR33": "ROXO34",
    "NUBR33 - NU HOLDINGS LTD.": "ROXO34",
    "NUBR35": "ROXO34",
    "NUBR35 - NU HOLDINGS LTD.": "ROXO34",
}


def ticker(valor: Any) -> str:
    if valor is None:
        return ""

    text = str(valor).strip()
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.upper()
    text = re.sub(r"\s+", " ", text).strip()

    primeira_parte = text.split(" - ", 1)[0].strip() if " - " in text else text
    match = re.search(r"\b([A-Z]{2,5}\d{1,2}[A-Z]?|B3SA\d{1,2})\b", primeira_parte)
    if match:
        return match.group(0)

    match = re.search(r"\b([A-Z]{2,5}\d{1,2}[A-Z]?|B3SA\d{1,2})\b", text)
    if match:
        return match.group(0)

    match = re.search(r"\b[A-Z0-9]{4,6}\b", primeira_parte)
    if match:
        return match.group(0)

    return text


def renomear_ativo(valor: Any) -> str:
    valor_ticker = ticker(valor)
    if not valor_ticker:
        return ""
    return RENOMEACAO_ATIVOS.get(valor_ticker, valor_ticker)
