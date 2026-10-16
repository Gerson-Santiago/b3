from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


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
