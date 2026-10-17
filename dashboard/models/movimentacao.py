from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from dashboard.models.texto import normalizar_texto


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


def classificar_movimentacao(texto: object) -> TipoMovimentacao:
    valor = normalizar_texto(texto)
    if not valor:
        return TipoMovimentacao.DESCONHECIDA

    if any(padrao in valor for padrao in ["dividendo", "jcp", "juros", "rendimento", "provento", "atualizacao", "atualização"]):
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


SINAL_ENTRADA_SAIDA: dict[str, int] = {
    "credito": 1,
    "crédito": 1,
    "debito": -1,
    "débito": -1,
}


def calcular_sinal(entrada_saida: object) -> int:
    """Retorna 1 para crédito, -1 para débito e 0 para desconhecido/vazio."""
    val = normalizar_texto(entrada_saida)
    if val in ("credito", "credito"):
        return 1
    if val in ("debito", "debito"):
        return -1
    return 0


def is_credito(entrada_saida: object) -> bool:
    return calcular_sinal(entrada_saida) == 1


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
        return calcular_sinal(self.entrada_saida) or -1

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
