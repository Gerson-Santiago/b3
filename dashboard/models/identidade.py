from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Optional


class Classe(str, Enum):
    ACOES = "AÇÕES"
    BDR = "BDR"
    ETF = "ETF"
    FII = "FII"
    TESOURO = "TESOURO"
    DESCONHECIDO = "DESCONHECIDO"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.upper().strip()
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
                if val_upper in ("ACOES", "AÇÃO", "ACAO", "AÇÕES"):
                    return cls.ACOES
        return cls.DESCONHECIDO


class AtivoDesconhecido(ValueError):
    def __init__(self, produto: Any = None, mensagem: str | None = None):
        self.produto = str(produto) if produto is not None else ""
        msg = mensagem or f"Produto desconhecido: {produto!r}"
        super().__init__(msg)


@dataclass(frozen=True, order=True)
class AtivoId:
    classe: Classe
    codigo: str

    def __post_init__(self) -> None:
        if isinstance(self.classe, str) and not isinstance(self.classe, Classe):
            object.__setattr__(self, "classe", Classe(self.classe))

    def __str__(self) -> str:
        return self.codigo


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
    def classe(self) -> Classe:
        return Classe(self.categoria)

    @property
    def eh_bdr(self) -> bool:
        return self.classe == Classe.BDR

    @property
    def eh_acao(self) -> bool:
        return self.classe == Classe.ACOES

    @property
    def eh_tesouro(self) -> bool:
        return self.classe == Classe.TESOURO

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
