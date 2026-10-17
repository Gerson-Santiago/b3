"""Tabela canônica de eventos da B3 e determinação de efeito sobre posição e provento."""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

from dashboard.models.movimentacao import TipoMovimentacao, classificar_movimentacao
from dashboard.models.texto import normalizar_texto


class SemanticaQuantidade(str, Enum):
    DELTA = "DELTA"
    TOTAL = "TOTAL"
    SNAPSHOT = "SNAPSHOT"
    NENHUMA = "NENHUMA"


@dataclass(frozen=True)
class EfeitoMovimentacao:
    tipo: TipoMovimentacao
    sentido: str
    semantica_quantidade: SemanticaQuantidade
    efeito_custo: str
    eh_provento: bool = False
    status: str = "definido"
    movimentacao_nome: str = ""

    @property
    def movimentacao(self) -> str:
        return self.movimentacao_nome or self.tipo.value

    @property
    def entrada_saida(self) -> str:
        return self.sentido

    @property
    def provento(self) -> bool:
        return self.eh_provento

    @property
    def custo(self) -> str:
        return self.efeito_custo

    @property
    def quantidade(self) -> str:
        if self.status == "pendente":
            return "pendente"
        if self.semantica_quantidade == SemanticaQuantidade.NENHUMA:
            return "ignora"
        if self.semantica_quantidade in (SemanticaQuantidade.TOTAL, SemanticaQuantidade.SNAPSHOT):
            return "define"
        if self.semantica_quantidade == SemanticaQuantidade.DELTA:
            return "soma" if self.sentido in ("credito", "crédito") else "subtrai"
        return "ignora"


EVENTOS: dict[tuple[Any, str], EfeitoMovimentacao] = {
    (TipoMovimentacao.COMPRA, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.COMPRA,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="soma",
        eh_provento=False,
        movimentacao_nome="compra",
    ),
    (TipoMovimentacao.VENDA, "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.VENDA,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="subtrai",
        eh_provento=False,
        movimentacao_nome="venda",
    ),
    (TipoMovimentacao.DESDOBRAMENTO, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.DESDOBRAMENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="desdobro",
    ),
    (TipoMovimentacao.GRUPAMENTO, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.GRUPAMENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.TOTAL,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="grupamento",
    ),
    (TipoMovimentacao.BONIFICACAO, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.BONIFICACAO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="bonificacao",
    ),
    (TipoMovimentacao.TRANSFERENCIA, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.TRANSFERENCIA,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="soma",
        eh_provento=False,
        movimentacao_nome="transferencia",
    ),
    (TipoMovimentacao.TRANSFERENCIA, "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.TRANSFERENCIA,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="subtrai",
        eh_provento=False,
        movimentacao_nome="transferencia",
    ),
    (TipoMovimentacao.AJUSTE_QUANTIDADE, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.AJUSTE_QUANTIDADE,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="leilao de fracao",
    ),
    (TipoMovimentacao.AJUSTE_QUANTIDADE, "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.AJUSTE_QUANTIDADE,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="fracao em ativos",
    ),
    (TipoMovimentacao.PROVENTO, "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="ignora",
        eh_provento=True,
        movimentacao_nome="dividendo",
    ),
    (TipoMovimentacao.PROVENTO, "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="ignora",
        eh_provento=False,
        movimentacao_nome="dividendo - cancelado",
    ),
}

# Mapeamentos 1:1 específicos por string para preservar compatibilidade exata de histórico
_EFEITOS_ESPECIFICOS: dict[tuple[str, str], EfeitoMovimentacao] = {
    ("amortizacao", "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.TRANSFERENCIA,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="subtrai",
        eh_provento=False,
        movimentacao_nome="amortizacao",
    ),
    ("atualizacao", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.TOTAL,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="atualizacao",
    ),
    ("atualizacao", "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.TOTAL,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="atualizacao",
    ),
    ("bonificacao", "credito"): EVENTOS[(TipoMovimentacao.BONIFICACAO, "credito")],
    ("bonificacao em ativos", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.BONIFICACAO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="bonificacao em ativos",
    ),
    ("compra", "credito"): EVENTOS[(TipoMovimentacao.COMPRA, "credito")],
    ("desdobro", "credito"): EVENTOS[(TipoMovimentacao.DESDOBRAMENTO, "credito")],
    ("direito de subscricao", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.AJUSTE_QUANTIDADE,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="direito de subscricao",
    ),
    ("direitos de subscricao - nao exercido", "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.AJUSTE_QUANTIDADE,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="nenhum",
        eh_provento=False,
        movimentacao_nome="direitos de subscricao - nao exercido",
    ),
    ("dividendo", "credito"): EVENTOS[(TipoMovimentacao.PROVENTO, "credito")],
    ("dividendo - cancelado", "debito"): EVENTOS[(TipoMovimentacao.PROVENTO, "debito")],
    ("fracao em ativos", "debito"): EVENTOS[(TipoMovimentacao.AJUSTE_QUANTIDADE, "debito")],
    ("grupamento", "credito"): EVENTOS[(TipoMovimentacao.GRUPAMENTO, "credito")],
    ("juros", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="ignora",
        eh_provento=True,
        movimentacao_nome="juros",
    ),
    ("juros sobre capital proprio", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="ignora",
        eh_provento=True,
        movimentacao_nome="juros sobre capital proprio",
    ),
    ("leilao de fracao", "credito"): EVENTOS[(TipoMovimentacao.AJUSTE_QUANTIDADE, "credito")],
    ("rendimento", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.PROVENTO,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="ignora",
        eh_provento=True,
        movimentacao_nome="rendimento",
    ),
    ("resgate", "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.TRANSFERENCIA,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="subtrai",
        eh_provento=False,
        movimentacao_nome="resgate",
    ),
    ("transferencia", "credito"): EVENTOS[(TipoMovimentacao.TRANSFERENCIA, "credito")],
    ("transferencia", "debito"): EVENTOS[(TipoMovimentacao.TRANSFERENCIA, "debito")],
    ("transferencia - liquidacao", "credito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.TRANSFERENCIA,
        sentido="credito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="soma",
        eh_provento=False,
        movimentacao_nome="transferencia - liquidacao",
    ),
    ("transferencia - liquidacao", "debito"): EfeitoMovimentacao(
        tipo=TipoMovimentacao.TRANSFERENCIA,
        sentido="debito",
        semantica_quantidade=SemanticaQuantidade.DELTA,
        efeito_custo="subtrai",
        eh_provento=False,
        movimentacao_nome="transferencia - liquidacao",
    ),
    ("venda", "debito"): EVENTOS[(TipoMovimentacao.VENDA, "debito")],
}

EVENTOS.update(_EFEITOS_ESPECIFICOS)


def normalizar_chave_evento(movimentacao: object, entrada_saida: object) -> tuple[str, str]:
    return normalizar_texto(movimentacao), normalizar_texto(entrada_saida)


def efeito_movimentacao(
    tipo_ou_movimentacao: object,
    sentido_ou_entrada_saida: object,
    qualidade: Any = None,
) -> EfeitoMovimentacao:
    sentido_norm = normalizar_texto(sentido_ou_entrada_saida)

    if isinstance(tipo_ou_movimentacao, TipoMovimentacao):
        chave_enum = (tipo_ou_movimentacao, sentido_norm)
        if chave_enum in EVENTOS:
            return EVENTOS[chave_enum]
        tipo_str = tipo_ou_movimentacao.value
    else:
        tipo_str = normalizar_texto(tipo_ou_movimentacao)
        chave_str = (tipo_str, sentido_norm)
        if chave_str in EVENTOS:
            return EVENTOS[chave_str]
        tipo_enum = classificar_movimentacao(tipo_str)
        chave_enum = (tipo_enum, sentido_norm)
        if chave_enum in EVENTOS:
            return EVENTOS[chave_enum]

    warnings.warn(
        f"Movimentação com efeito pendente: movimentacao={tipo_ou_movimentacao!r}, entrada_saida={sentido_ou_entrada_saida!r}",
        RuntimeWarning,
        stacklevel=2,
    )
    if qualidade is not None:
        from dashboard.models.qualidade import Aviso

        qualidade.add(
            Aviso(
                tipo="EVENTO_DESCONHECIDO",
                produto=str(tipo_ou_movimentacao) if tipo_ou_movimentacao is not None else "",
                detalhe=f"Evento sem efeito: ({tipo_ou_movimentacao!r}, {sentido_ou_entrada_saida!r})",
            )
        )
    return EfeitoMovimentacao(
        tipo=TipoMovimentacao.DESCONHECIDA,
        sentido=sentido_norm,
        semantica_quantidade=SemanticaQuantidade.NENHUMA,
        efeito_custo="pendente",
        eh_provento=False,
        status="pendente",
        movimentacao_nome=tipo_str,
    )


def listar_movimentacoes_pendentes(df: pd.DataFrame) -> list[str]:
    if df is None or df.empty or "movimentacao" not in df.columns:
        return []

    pendentes = []
    seen: set[str] = set()
    for _, row in df.iterrows():
        efeito = efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida"))
        if efeito.status == "pendente":
            chave = f"{efeito.movimentacao}|{efeito.entrada_saida}"
            if chave not in seen:
                seen.add(chave)
                pendentes.append(chave)
    return sorted(pendentes)


def tem_efeito_pendente(df: pd.DataFrame) -> bool:
    return bool(listar_movimentacoes_pendentes(df))
