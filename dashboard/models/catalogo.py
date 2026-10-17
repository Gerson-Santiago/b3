"""Catálogo canônico de ativos e resolução de produto → AtivoId."""
from __future__ import annotations

from typing import Any

from dashboard.models.identidade import AtivoDesconhecido, AtivoId, Classe
from dashboard.models.texto import normalizar_nome


def _item(classe: str | Classe, codigo: str, *aliases: str) -> tuple[AtivoId, list[str]]:
    aid = AtivoId(classe=classe, codigo=codigo)
    extras = list(dict.fromkeys([codigo, *aliases]))
    return aid, extras


CATALOGO_ATIVOS: list[tuple[AtivoId, list[str]]] = [
    _item("AÇÕES", "B3SA3"),
    _item("AÇÕES", "PETR4"),
    _item("AÇÕES", "VALE3"),
    _item("AÇÕES", "CPFE3"),
    _item("AÇÕES", "ITSA4"),
    _item("AÇÕES", "ITSA2"),
    _item("AÇÕES", "CASH3"),
    _item("AÇÕES", "BBAS3"),
    _item("AÇÕES", "TEST3"),
    _item("BDR", "ROXO34", "NUBR33", "NUBR35"),
    _item("BDR", "GOGL35"),
    _item("BDR", "MSFT34"),
    _item("BDR", "COCA34"),
    _item("BDR", "TSLA34"),
    _item("BDR", "AAPL34"),
    _item("ETF", "BOVA11"),
    _item("ETF", "IVVB11"),
    _item("ETF", "SMAL11"),
    _item("FII", "XPLG11"),
    _item("TESOURO", "Tesouro Educa+ 2026"),
    _item("TESOURO", "Tesouro Educa+ 2028"),
    _item("TESOURO", "Tesouro IPCA+ 2026"),
    _item("TESOURO", "Tesouro IPCA+ 2032"),
    _item("TESOURO", "Tesouro Prefixado 2024"),
    _item("TESOURO", "Tesouro Prefixado com Juros Semestrais 2035"),
    _item("TESOURO", "Tesouro Prefixado com Juros Semestrais 2037"),
    _item("TESOURO", "Tesouro Selic 2028"),
    _item("TESOURO", "Tesouro Selic 2031"),
    _item("TESOURO", "Tesouro Selic 2029"),
]


def _montar_mapas(
    catalogo: list[tuple[AtivoId, list[str]]],
) -> tuple[dict[str, AtivoId], dict[str, AtivoId]]:
    mapa_catalogo: dict[str, AtivoId] = {}
    mapa_tickers: dict[str, AtivoId] = {}
    for ativo_id, aliases in catalogo:
        mapa_tickers[normalizar_nome(ativo_id.codigo)] = ativo_id
        for alias in aliases:
            mapa_catalogo[normalizar_nome(alias)] = ativo_id
            if " - " in alias:
                ticker_alias = alias.split(" - ", 1)[0].strip()
                mapa_tickers[normalizar_nome(ticker_alias)] = ativo_id
    return mapa_catalogo, mapa_tickers


_MAPA_CATALOGO, _MAPA_TICKERS = _montar_mapas(CATALOGO_ATIVOS)


def resolver_ativo(produto: Any) -> AtivoId:
    if isinstance(produto, AtivoId):
        return produto

    if produto is None:
        raise AtivoDesconhecido(produto, "Produto não pode ser nulo")

    texto = str(produto).strip()
    if not texto:
        raise AtivoDesconhecido(produto, "Produto não pode ser vazio")

    norm = normalizar_nome(texto)

    if norm in _MAPA_CATALOGO:
        return _MAPA_CATALOGO[norm]

    if " - " in norm:
        primeira_parte = norm.split(" - ", 1)[0].strip()
        if primeira_parte in _MAPA_TICKERS:
            return _MAPA_TICKERS[primeira_parte]
        if primeira_parte in _MAPA_CATALOGO:
            return _MAPA_CATALOGO[primeira_parte]

    if norm in _MAPA_TICKERS:
        return _MAPA_TICKERS[norm]

    raise AtivoDesconhecido(produto)


def resolver_ativo_seguro(produto: Any, qualidade: Any = None) -> AtivoId:
    try:
        return resolver_ativo(produto)
    except (AtivoDesconhecido, ValueError):
        aid = AtivoId(classe=Classe.DESCONHECIDO, codigo=normalizar_nome(produto))
        if qualidade is not None:
            from dashboard.models.qualidade import Aviso

            qualidade.add(
                Aviso(
                    tipo="ATIVO_DESCONHECIDO",
                    produto=str(produto) if produto is not None else "",
                    detalhe="Ativo não encontrado no catálogo canônico",
                )
            )
        return aid


def anotar_ativos(df: Any, qualidade: Any = None, coluna_origem: str = "produto") -> Any:
    if df is None:
        return None
    out = df.copy()
    if out.empty or coluna_origem not in out.columns:
        if "ativo_id" not in out.columns:
            out["ativo_id"] = None
        if "ativo" not in out.columns:
            out["ativo"] = ""
        return out

    ids = [resolver_ativo_seguro(p, qualidade) for p in out[coluna_origem]]
    out["ativo_id"] = ids
    out["ativo"] = [a.codigo for a in ids]
    return out
