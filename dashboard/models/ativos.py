from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Optional
import unicodedata


@dataclass
class Ativo:
    produto: str
    categoria: str
    instituicao: str
    quantidade: float = 0.0
    valor_atualizado: float = 0.0
    valor_liquido: float = 0.0
    preco_fechamento: float = 0.0
    codigo_negociacao: Optional[str] = None
    codigo_isin: Optional[str] = None
    data_posicao: Optional[date] = None

    @property
    def eh_bdr(self) -> bool:
        return self.categoria.upper() == "BDR"

    @property
    def eh_acao(self) -> bool:
        return self.categoria.upper() == "ACOES"

    @property
    def eh_tesouro(self) -> bool:
        return self.categoria.upper() == "TESOURO"

    @classmethod
    def from_row(cls, row: dict) -> "Ativo":
        return cls(
            produto=str(row.get("produto") or "").strip(),
            categoria=str(row.get("categoria") or "").strip().upper(),
            instituicao=str(row.get("instituicao") or "").strip(),
            quantidade=float(row.get("quantidade") or 0.0),
            valor_atualizado=float(row.get("valor_atualizado") or row.get("valor_operacao") or 0.0),
            valor_liquido=float(row.get("valor_liquido") or row.get("valor_operacao") or 0.0),
            preco_fechamento=float(row.get("preco_fechamento") or 0.0),
            codigo_negociacao=row.get("codigo_negociacao"),
            codigo_isin=row.get("codigo_isin"),
            data_posicao=row.get("data_posicao"),
        )


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
