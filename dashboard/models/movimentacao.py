from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Movimentacao:
    data: date
    produto: str
    entrada_saida: str
    quantidade: float
    preco_unitario: float
    valor_operacao: float
    instituicao: str
    movimentacao: str

    @property
    def sinal(self) -> int:
        return 1 if str(self.entrada_saida).strip().lower() in {"credito", "crédito"} else -1

    @property
    def valor_liquido(self) -> float:
        return self.valor_operacao * self.sinal

    @property
    def qtd_liquida(self) -> float:
        return self.quantidade * self.sinal

    @classmethod
    def from_row(cls, row: dict) -> "Movimentacao":
        return cls(
            data=row.get("data"),
            produto=str(row.get("produto") or "").strip(),
            entrada_saida=str(row.get("entrada_saida") or "").strip(),
            quantidade=float(row.get("quantidade") or 0.0),
            preco_unitario=float(row.get("preco_unitario") or 0.0),
            valor_operacao=float(row.get("valor_operacao") or 0.0),
            instituicao=str(row.get("instituicao") or "").strip(),
            movimentacao=str(row.get("movimentacao") or "").strip(),
        )
