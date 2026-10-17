"""Normalização de texto — SSOT usada por catálogo, eventos e classificação."""
from __future__ import annotations

import re
import unicodedata
from typing import Any


def sem_acentos(texto: Any) -> str:
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = t.encode("ascii", "ignore").decode("ascii")
    return t.replace("\u2013", "-").replace("\u2014", "-")


def compactar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_texto(texto: Any) -> str:
    """Minúsculas sem acento — chaves de evento e tipo de movimentação."""
    return compactar_espacos(sem_acentos(texto).lower())


def normalizar_nome(produto: Any) -> str:
    """Maiúsculas canônicas de produto (S/A → S.A., hífen de PETROBRAS)."""
    t = compactar_espacos(sem_acentos(produto).upper())
    t = re.sub(r"\bS/A\b", "S.A.", t)
    t = re.sub(r"-\s*PETROBRAS", "PETROBRAS", t)
    return compactar_espacos(t)
