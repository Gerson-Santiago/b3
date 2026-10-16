from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from enum import Enum


class TipoMovimentacao(str, Enum):
    COMPRA = "compra"
    VENDA = "venda"
    PROVENTO = "provento"
    AJUSTE_QUANTIDADE = "ajuste_quantidade"
    DESDOBRAMENTO = "desdobramento"
    GRUPAMENTO = "grupamento"
    BONIFICACAO = "bonificacao"
    TRANSFERENCIA = "transferencia"
    DESCONHECIDA = "desconhecida"


def _normalizar_texto(texto: object) -> str:
    text = unicodedata.normalize("NFKD", str(texto or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classificar_movimentacao(texto: object) -> TipoMovimentacao:
    valor = _normalizar_texto(texto)
    if not valor:
        return TipoMovimentacao.DESCONHECIDA

    if any(padrao in valor for padrao in ["dividendo", "jcp", "juros", "rendimento", "provento"]):
        return TipoMovimentacao.PROVENTO

    if any(padrao in valor for padrao in ["desdobro", "split"]):
        return TipoMovimentacao.DESDOBRAMENTO

    if any(padrao in valor for padrao in ["grupamento", "agrupamento"]):
        return TipoMovimentacao.GRUPAMENTO

    if "bonific" in valor:
        return TipoMovimentacao.BONIFICACAO

    if any(padrao in valor for padrao in ["fracao", "fração", "leilao", "leilão", "ajuste", "facao"]):
        return TipoMovimentacao.AJUSTE_QUANTIDADE

    if "compra" in valor:
        return TipoMovimentacao.COMPRA

    if "venda" in valor:
        return TipoMovimentacao.VENDA

    if any(padrao in valor for padrao in ["liquidacao", "liquidação", "transferencia", "transferência"]):
        return TipoMovimentacao.TRANSFERENCIA

    return TipoMovimentacao.DESCONHECIDA


def is_provento(movimentacao: object) -> bool:
    return classificar_movimentacao(movimentacao) == TipoMovimentacao.PROVENTO


def is_ajuste_quantidade(movimentacao: object) -> bool:
    tipo = classificar_movimentacao(movimentacao)
    return tipo in {
        TipoMovimentacao.AJUSTE_QUANTIDADE,
        TipoMovimentacao.DESDOBRAMENTO,
        TipoMovimentacao.GRUPAMENTO,
        TipoMovimentacao.BONIFICACAO,
    }


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
    def tipo(self) -> TipoMovimentacao:
        return classificar_movimentacao(self.movimentacao)

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
