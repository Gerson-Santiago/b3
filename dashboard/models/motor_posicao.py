"""Motor de cálculo de posição e custo acumulado a partir de movimentações e eventos."""
from __future__ import annotations

import pandas as pd

from dashboard.models.efeitos import EfeitoMovimentacao, SemanticaQuantidade, efeito_movimentacao
from dashboard.models.movimentacao import TipoMovimentacao
from dashboard.models.posicao_acumulada import PosicaoAcumulada


def _aplicar_ajuste_sem_custo(
    pos: PosicaoAcumulada,
    efeito: EfeitoMovimentacao,
    qtd_liquida: float,
    aplicar_define: bool,
) -> None:
    if efeito.semantica_quantidade == SemanticaQuantidade.TOTAL:
        if efeito.tipo == TipoMovimentacao.PROVENTO and not aplicar_define:
            return
        if efeito.tipo == TipoMovimentacao.GRUPAMENTO and abs(qtd_liquida) <= 0:
            return
        pos.definir_quantidade(qtd_liquida)
        return

    if efeito.semantica_quantidade == SemanticaQuantidade.NENHUMA:
        return

    if efeito.tipo == TipoMovimentacao.DESDOBRAMENTO:
        pos.somar_quantidade(qtd_liquida)
        return

    if efeito.tipo == TipoMovimentacao.AJUSTE_QUANTIDADE:
        if qtd_liquida < 0:
            pos.reduzir(abs(qtd_liquida))
        return

    pos.ajustar_quantidade_assinada(qtd_liquida)


def _aplicar_linha(
    pos: PosicaoAcumulada,
    row: pd.Series,
    aplicar_define: bool,
) -> None:
    qtd_liquida = float(row.get("qtd_liquida", 0.0) or 0.0)
    valor_liquido = float(row.get("valor_liquido", 0.0) or 0.0)
    efeito = efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida"))

    if efeito.provento or efeito.status == "pendente":
        return
    if efeito.quantidade == "ignora":
        return
    if abs(qtd_liquida) < 1e-9:
        return

    if efeito.custo == "nenhum" and efeito.quantidade in {"soma", "subtrai", "define"}:
        _aplicar_ajuste_sem_custo(pos, efeito, qtd_liquida, aplicar_define)
        return

    if qtd_liquida > 0:
        pos.comprar(qtd_liquida, valor_liquido)
        return

    if qtd_liquida < 0:
        pos.reduzir(abs(qtd_liquida))


__all__ = [
    "_aplicar_ajuste_sem_custo",
    "_aplicar_linha",
]
