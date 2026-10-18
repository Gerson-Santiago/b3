"""Mapeamento de tickers → URL do ícone SVG (brapi.dev/icons).

Uso:
    from dashboard.views.svg.links import get_svg_url

    url = get_svg_url("PETR4")   # "https://icons.brapi.dev/icons/PETR4.svg"
    url = get_svg_url("XXXX99")  # None  (ticker não mapeado)

Adicione novos ativos na constante ``_SVG_ATIVOS`` abaixo.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
_URL_BASE: str = "https://icons.brapi.dev/icons/"

# Mapeamento ticker → nome de exibição (informativo).
# Apenas os tickers listados aqui receberão ícone no card.
_SVG_ATIVOS: dict[str, str] = {
    # ── Ações Brasileiras ──────────────────────────────────────────────────
    "PETR4":  "Petrobras",
    "PETR3":  "Petrobras",
    "VALE3":  "Vale",
    "B3SA3":  "B3",
    "CPFE3":  "CPFL",
    "ITUB4":  "Itaú Unibanco",
    "ITUB3":  "Itaú Unibanco",
    "BBDC4":  "Bradesco",
    "BBDC3":  "Bradesco",
    "BBAS3":  "Banco do Brasil",
    "ABEV3":  "Ambev",
    "WEGE3":  "WEG",
    "RENT3":  "Localiza",
    "RADL3":  "Raia Drogasil",
    "LREN3":  "Lojas Renner",
    "MGLU3":  "Magazine Luiza",
    "VBBR3":  "Vibra",
    "CPLE6":  "Copel",
    "ELET3":  "Eletrobras",
    "ELET6":  "Eletrobras",
    "SUZB3":  "Suzano",
    "CSNA3":  "CSN",
    "USIM5":  "Usiminas",
    "GOAU4":  "Gerdau Met",
    "GGBR4":  "Gerdau",
    "EMBR3":  "Embraer",
    "AZUL4":  "Azul",
    "GOLL4":  "Gol",
    "VIVA3":  "Vivara",
    "PRIO3":  "PetroRio",
    "RECV3":  "PetroRecôncavo",
    "CSAN3":  "Cosan",
    "RAIL3":  "Rumo",
    "SBSP3":  "Sabesp",
    "TAEE11": "Taesa",
    "ENGI11": "Energisa",
    "EQTL3":  "Equatorial",
    "EGIE3":  "Engie",
    "CMIG4":  "Cemig",
    "TRPL4":  "ISA CTEEP",
    "HYPE3":  "Hypera",
    "FLRY3":  "Fleury",
    "RDOR3":  "Rede D'Or",
    "HAPV3":  "Hapvida",
    "TOTS3":  "TOTVS",
    "INTB3":  "Intelbras",
    # ── BDRs ──────────────────────────────────────────────────────────────
    "ROXO34": "Nu Holdings",
    "MSFT34": "Microsoft",
    "GOGL35": "Alphabet (Google)",
    "AAPL34": "Apple",
    "AMZO34": "Amazon",
    "TSLA34": "Tesla",
    "META34": "Meta",
    "NVDC34": "NVIDIA",
    "NFLX34": "Netflix",
    "DISB34": "Disney",
    "JPMC34": "JPMorgan",
    "VISA34": "Visa",
}

# Pré-computado na inicialização do módulo: ticker em maiúsculas → URL completa.
# Lookup O(1) sem custo extra em tempo de renderização.
_URL_MAP: dict[str, str] = {
    ticker.upper(): f"{_URL_BASE}{ticker}.svg"
    for ticker in _SVG_ATIVOS
}


def get_svg_url(ticker: str | None) -> str | None:
    """Retorna a URL do ícone SVG para *ticker*, ou ``None`` se não mapeado.

    A busca é case-insensitive.

    Parameters
    ----------
    ticker:
        Código do ativo (ex.: ``"PETR4"``, ``"msft34"``).

    Returns
    -------
    str | None
        URL completa do SVG ou ``None``.
    """
    if not ticker:
        return None
    return _URL_MAP.get(ticker.strip().upper())


def get_all_tickers() -> list[str]:
    """Retorna todos os tickers mapeados, ordenados."""
    return sorted(_SVG_ATIVOS.keys())

