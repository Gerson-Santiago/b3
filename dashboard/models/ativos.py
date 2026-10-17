from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Optional
import unicodedata


@dataclass(frozen=True)
class AtivoId:
    classe: str
    codigo: str

    def __str__(self) -> str:
        return self.codigo

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AtivoId):
            return self.classe == other.classe and self.codigo == other.codigo
        if isinstance(other, str):
            return self.codigo == other
        return False

    def __hash__(self) -> int:
        return hash((self.classe, self.codigo))

    def __lt__(self, other: object) -> bool:
        if isinstance(other, AtivoId):
            return (self.classe, self.codigo) < (other.classe, other.codigo)
        if isinstance(other, str):
            return self.codigo < other
        return NotImplemented


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
        return self.categoria.upper() == "AÇÕES"

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


# Catálogo Canônico de Ativos (SSOT)
CATALOGO_ATIVOS: list[tuple[AtivoId, list[str]]] = [
    # Ações
    (
        AtivoId(classe="AÇÕES", codigo="B3SA3"),
        [
            "B3SA3",
            "B3SA3 - B3",
            "B3SA3 - B3 S.A. - BRASIL, BOLSA, BALCAO",
            "B3SA3 - B3 S.A. - BRASIL, BOLSA, BALCÃO",
            "B3SA3 - B3 S/A - BRASIL, BOLSA, BALCAO",
            "B3SA3 - B3 S/A - BRASIL, BOLSA, BALCÃO",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="PETR4"),
        [
            "PETR4",
            "PETR4 - PETROLEO BRASILEIRO S/A - PETROBRAS",
            "PETR4 - PETROLEO BRASILEIRO S/A PETROBRAS",
            "PETR4 - PETROLEO BRASILEIRO S.A. PETROBRAS",
            "PETR4 - PETROLEO BRASILEIRO S.A. - PETROBRAS",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="VALE3"),
        [
            "VALE3",
            "VALE3 - VALE S.A.",
            "VALE3 - VALE S/A",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="CPFE3"),
        [
            "CPFE3",
            "CPFE3 - CPFL ENERGIA S.A.",
            "CPFE3 - CPFL ENERGIA S/A",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="ITSA4"),
        [
            "ITSA4",
            "ITSA4 - ITAUSA S.A.",
            "ITSA4 - ITAUSA S/A",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="ITSA2"),
        [
            "ITSA2",
            "ITSA2 - ITAUSA S.A.",
            "ITSA2 - ITAUSA S/A",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="CASH3"),
        [
            "CASH3",
            "CASH3 - MÉLIUZ S.A.",
            "CASH3 - MELIUZ S.A.",
            "CASH3 - MÉLIUZ S/A",
            "CASH3 - MELIUZ S/A",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="BBAS3"),
        [
            "BBAS3",
            "BBAS3 - BANCO DO BRASIL S.A.",
            "BBAS3 - BANCO DO BRASIL S/A",
        ],
    ),
    (
        AtivoId(classe="AÇÕES", codigo="TEST3"),
        [
            "TEST3",
        ],
    ),
    # BDRs
    (
        AtivoId(classe="BDR", codigo="ROXO34"),
        [
            "ROXO34",
            "ROXO34 - NU HOLDINGS",
            "ROXO34 - NU HOLDINGS LTD.",
            "NUBR33",
            "NUBR33 - NU HOLDINGS LTD.",
            "NUBR35",
            "NUBR35 - NU HOLDINGS LTD.",
        ],
    ),
    (
        AtivoId(classe="BDR", codigo="GOGL35"),
        [
            "GOGL35",
            "GOGL35 - ALPHABET INC.",
        ],
    ),
    (
        AtivoId(classe="BDR", codigo="MSFT34"),
        [
            "MSFT34",
            "MSFT34 - MICROSOFT CORPORATION",
        ],
    ),
    (
        AtivoId(classe="BDR", codigo="COCA34"),
        [
            "COCA34",
            "COCA34 - THE COCA-COLA COMPANY",
        ],
    ),
    (
        AtivoId(classe="BDR", codigo="TSLA34"),
        [
            "TSLA34",
            "TSLA34 - TESLA INC",
        ],
    ),
    (
        AtivoId(classe="BDR", codigo="AAPL34"),
        [
            "AAPL34",
            "AAPL34 - APPLE INC.",
        ],
    ),
    # ETFs
    (
        AtivoId(classe="ETF", codigo="BOVA11"),
        [
            "BOVA11",
            "BOVA11 - ISHARES IBOVESPA FUNDO DE INDICE",
        ],
    ),
    (
        AtivoId(classe="ETF", codigo="IVVB11"),
        [
            "IVVB11",
            "IVVB11 - ISHARE S&P 500 FIC EM FUNDO DE INDICE IE",
        ],
    ),
    (
        AtivoId(classe="ETF", codigo="SMAL11"),
        [
            "SMAL11",
            "SMAL11 - ISHARES BM&FBOVESPA SMALL CAP FUNDO DE INDICE",
        ],
    ),
    # FIIs
    (
        AtivoId(classe="FII", codigo="XPLG11"),
        [
            "XPLG11",
        ],
    ),
    # Tesouro Direto
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Educa+ 2026"),
        ["Tesouro Educa+ 2026"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Educa+ 2028"),
        ["Tesouro Educa+ 2028"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro IPCA+ 2026"),
        ["Tesouro IPCA+ 2026"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro IPCA+ 2032"),
        ["Tesouro IPCA+ 2032"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Prefixado 2024"),
        ["Tesouro Prefixado 2024"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Prefixado com Juros Semestrais 2035"),
        ["Tesouro Prefixado com Juros Semestrais 2035"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Prefixado com Juros Semestrais 2037"),
        ["Tesouro Prefixado com Juros Semestrais 2037"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Selic 2028"),
        ["Tesouro Selic 2028"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Selic 2031"),
        ["Tesouro Selic 2031"],
    ),
    (
        AtivoId(classe="TESOURO", codigo="Tesouro Selic 2029"),
        ["Tesouro Selic 2029"],
    ),
]


def _normalizar_texto(texto: Any) -> str:
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = t.encode("ascii", "ignore").decode("ascii")
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.upper().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\bS/A\b", "S.A.", t)
    t = re.sub(r"-\s*PETROBRAS", "PETROBRAS", t)
    return re.sub(r"\s+", " ", t).strip()


_MAPA_CATALOGO: dict[str, AtivoId] = {}
_MAPA_TICKERS: dict[str, AtivoId] = {}

for _ativo_id, _aliases in CATALOGO_ATIVOS:
    _MAPA_TICKERS[_normalizar_texto(_ativo_id.codigo)] = _ativo_id
    for _alias in _aliases:
        _MAPA_CATALOGO[_normalizar_texto(_alias)] = _ativo_id
        if " - " in _alias:
            _ticker_alias = _alias.split(" - ", 1)[0].strip()
            _MAPA_TICKERS[_normalizar_texto(_ticker_alias)] = _ativo_id


def resolver_ativo(produto: Any) -> AtivoId:
    if isinstance(produto, AtivoId):
        return produto

    if produto is None:
        raise ValueError("Produto não pode ser nulo")

    texto = str(produto).strip()
    if not texto:
        raise ValueError("Produto não pode ser vazio")

    norm = _normalizar_texto(texto)

    # 1. Busca direta no mapa de aliases normalizados
    if norm in _MAPA_CATALOGO:
        return _MAPA_CATALOGO[norm]

    # 2. Busca por ticker se contiver " - "
    if " - " in norm:
        primeira_parte = norm.split(" - ", 1)[0].strip()
        if primeira_parte in _MAPA_TICKERS:
            return _MAPA_TICKERS[primeira_parte]
        if primeira_parte in _MAPA_CATALOGO:
            return _MAPA_CATALOGO[primeira_parte]

    # 3. Busca por ticker puro
    if norm in _MAPA_TICKERS:
        return _MAPA_TICKERS[norm]

    # 4. Busca para títulos de tesouro
    if "TESOURO" in norm:
        for _ativo_id, _ in CATALOGO_ATIVOS:
            if _ativo_id.classe == "TESOURO":
                if _normalizar_texto(_ativo_id.codigo) == norm:
                    return _ativo_id

    # Produto desconhecido gera erro explícito, nunca chave inventada
    raise ValueError(f"Produto desconhecido: {produto!r}")


RENOMEACAO_ATIVOS: dict[str, str] = {
    "NUBR33": "ROXO34",
    "NUBR33 - NU HOLDINGS LTD.": "ROXO34",
    "NUBR35": "ROXO34",
    "NUBR35 - NU HOLDINGS LTD.": "ROXO34",
}


def _ticker_regex(text: str) -> str:
    """Extrai ticker via regex — fallback para produtos fora do catálogo."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\s+", " ", text).upper().strip()
    primeira_parte = text.split(" ", 1)[0] if " " in text else text
    match = re.search(r"\b([A-Z]{2,5}\d{1,2}[A-Z]?|B3SA\d{1,2})\b", primeira_parte)
    if match:
        return match.group(0)
    match = re.search(r"\b([A-Z]{2,5}\d{1,2}[A-Z]?|B3SA\d{1,2})\b", text)
    if match:
        return match.group(0)
    return primeira_parte


def ticker(valor: Any) -> str:
    """Retorna o código de negociação normalizado.

    Prioridade:
    1. Se o produto está no catálogo → retorna o código canônico (NUBR33 → ROXO34).
    2. Caso contrário, extrai via regex (compatibilidade com dados sintéticos de testes).
    """
    if valor is None:
        return ""
    text = str(valor).strip()
    if not text:
        return ""
    try:
        return resolver_ativo(text).codigo
    except (ValueError, KeyError):
        return _ticker_regex(text)


def renomear_ativo(valor: Any) -> str:
    """Retorna o código canônico do ativo (SSOT via catálogo).

    Ao contrário de ticker(), nunca usa fallback regex — produto desconhecido
    retorna string vazia, sinalizando que o catálogo precisa ser atualizado.
    """
    if valor is None:
        return ""
    text = str(valor).strip()
    if not text:
        return ""
    try:
        return resolver_ativo(text).codigo
    except (ValueError, KeyError):
        return ""
