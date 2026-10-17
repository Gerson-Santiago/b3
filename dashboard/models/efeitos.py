"""Tabela canônica de eventos da B3 e determinação de efeito sobre posição e provento."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import pandas as pd

from dashboard.models.texto import normalizar_texto


@dataclass(frozen=True)
class EfeitoMovimentacao:
    movimentacao: str
    entrada_saida: str
    quantidade: str
    custo: str
    provento: bool = False
    status: str = "definido"


def _efeito(
    movimentacao: str,
    entrada_saida: str,
    quantidade: str,
    custo: str,
    provento: bool = False,
) -> tuple[tuple[str, str], EfeitoMovimentacao]:
    return (
        (movimentacao, entrada_saida),
        EfeitoMovimentacao(movimentacao, entrada_saida, quantidade, custo, provento, "definido"),
    )


EVENTOS: dict[tuple[str, str], EfeitoMovimentacao] = dict(
    (
        _efeito("amortizacao", "debito", "subtrai", "subtrai"),
        _efeito("atualizacao", "credito", "define", "nenhum"),
        _efeito("atualizacao", "debito", "define", "nenhum"),
        _efeito("bonificacao", "credito", "soma", "nenhum"),
        _efeito("bonificacao em ativos", "credito", "soma", "nenhum"),
        _efeito("compra", "credito", "soma", "soma"),
        _efeito("desdobro", "credito", "soma", "nenhum"),
        _efeito("direito de subscricao", "credito", "soma", "nenhum"),
        _efeito("direitos de subscricao - nao exercido", "debito", "subtrai", "nenhum"),
        _efeito("dividendo", "credito", "ignora", "ignora", True),
        _efeito("dividendo - cancelado", "debito", "ignora", "ignora"),
        _efeito("fracao em ativos", "debito", "subtrai", "nenhum"),
        _efeito("grupamento", "credito", "define", "nenhum"),
        _efeito("juros", "credito", "ignora", "ignora", True),
        _efeito("juros sobre capital proprio", "credito", "ignora", "ignora", True),
        _efeito("leilao de fracao", "credito", "ignora", "nenhum"),
        _efeito("rendimento", "credito", "ignora", "ignora", True),
        _efeito("resgate", "debito", "subtrai", "subtrai"),
        _efeito("transferencia", "credito", "soma", "soma"),
        _efeito("transferencia", "debito", "subtrai", "subtrai"),
        _efeito("transferencia - liquidacao", "credito", "soma", "soma"),
        _efeito("transferencia - liquidacao", "debito", "subtrai", "subtrai"),
        _efeito("venda", "debito", "subtrai", "subtrai"),
    )
)


def normalizar_chave_evento(movimentacao: object, entrada_saida: object) -> tuple[str, str]:
    return normalizar_texto(movimentacao), normalizar_texto(entrada_saida)


def efeito_movimentacao(movimentacao: object, entrada_saida: object) -> EfeitoMovimentacao:
    chave = normalizar_chave_evento(movimentacao, entrada_saida)
    efeito = EVENTOS.get(chave)
    if efeito is not None:
        return efeito

    warnings.warn(
        f"Movimentação com efeito pendente: movimentacao={movimentacao!r}, entrada_saida={entrada_saida!r}",
        RuntimeWarning,
        stacklevel=2,
    )
    return EfeitoMovimentacao(
        movimentacao=chave[0],
        entrada_saida=chave[1],
        quantidade="pendente",
        custo="pendente",
        provento=False,
        status="pendente",
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
