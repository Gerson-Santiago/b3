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


CATALOGO_MOVIMENTACOES: dict[str, TipoMovimentacao] = {
    # Proventos
    "dividendo": TipoMovimentacao.PROVENTO,
    "dividendo - cancelado": TipoMovimentacao.PROVENTO,
    "juros": TipoMovimentacao.PROVENTO,
    "juros sobre capital proprio": TipoMovimentacao.PROVENTO,
    "jcp": TipoMovimentacao.PROVENTO,
    "rendimento": TipoMovimentacao.PROVENTO,
    "provento": TipoMovimentacao.PROVENTO,
    "atualizacao": TipoMovimentacao.PROVENTO,
    # Desdobramentos / Grupamentos
    "desdobro": TipoMovimentacao.DESDOBRAMENTO,
    "desdobro de acoes": TipoMovimentacao.DESDOBRAMENTO,
    "split": TipoMovimentacao.DESDOBRAMENTO,
    "grupamento": TipoMovimentacao.GRUPAMENTO,
    "agrupamento": TipoMovimentacao.GRUPAMENTO,
    # Bonificações
    "bonificacao": TipoMovimentacao.BONIFICACAO,
    "bonificacao em ativos": TipoMovimentacao.BONIFICACAO,
    # Operações e Transferências
    "compra": TipoMovimentacao.COMPRA,
    "venda": TipoMovimentacao.VENDA,
    "transferencia": TipoMovimentacao.TRANSFERENCIA,
    "transferencia - liquidacao": TipoMovimentacao.TRANSFERENCIA,
    "liquidacao": TipoMovimentacao.TRANSFERENCIA,
    "resgate": TipoMovimentacao.TRANSFERENCIA,
    "amortizacao": TipoMovimentacao.TRANSFERENCIA,
    # Ajustes e frações
    "fracao em ativos": TipoMovimentacao.AJUSTE_QUANTIDADE,
    "leilao de fracao": TipoMovimentacao.AJUSTE_QUANTIDADE,
    "direito de subscricao": TipoMovimentacao.AJUSTE_QUANTIDADE,
    "direitos de subscricao - nao exercido": TipoMovimentacao.AJUSTE_QUANTIDADE,
    "ajuste": TipoMovimentacao.AJUSTE_QUANTIDADE,
}


def classificar_movimentacao(texto: object) -> TipoMovimentacao:
    valor = normalizar_texto(texto)
    if not valor:
        return TipoMovimentacao.DESCONHECIDA

    tipo = CATALOGO_MOVIMENTACOES.get(valor)
    if tipo is not None:
        return tipo

    for chave in sorted(CATALOGO_MOVIMENTACOES, key=len, reverse=True):
        if valor.startswith(chave):
            return CATALOGO_MOVIMENTACOES[chave]

    return TipoMovimentacao.DESCONHECIDA


def is_provento(movimentacao: object) -> bool:
    return classificar_movimentacao(movimentacao) == TipoMovimentacao.PROVENTO


def classificar_tipo_provento(texto: object) -> str:
    """Classifica a movimentação em 'Dividendo', 'JCP', 'Rendimento FII' ou 'Outros'."""
    val = normalizar_texto(texto)
    if "juros" in val or "jcp" in val:
        return "JCP"
    if "dividendo" in val:
        return "Dividendo"
    if "rendimento" in val or "fii" in val:
        return "Rendimento FII"
    return "Outros"


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
