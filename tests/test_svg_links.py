"""Testes para dashboard.views.svg.links.

Cobre:
- get_svg_url: tickers mapeados, não mapeados, case-insensitive, None/vazio
- _URL_MAP: formato das URLs, unicidade de chaves, prefixo correto
- get_all_tickers: retorno ordenado, tipo correto
- Constante _URL_BASE: imutabilidade esperada
"""
from __future__ import annotations

import pytest

from dashboard.views.svg.links import (
    _SVG_ATIVOS,
    _URL_BASE,
    _URL_MAP,
    get_all_tickers,
    get_svg_url,
)


# ---------------------------------------------------------------------------
# get_svg_url — tickers mapeados
# ---------------------------------------------------------------------------

class TestGetSvgUrlMapeados:
    """Tickers presentes em _SVG_ATIVOS devem sempre retornar uma URL válida."""

    def test_petr4_retorna_url(self):
        url = get_svg_url("PETR4")
        assert url is not None
        assert "PETR4" in url

    def test_vale3_retorna_url(self):
        assert get_svg_url("VALE3") is not None

    def test_msft34_bdr_retorna_url(self):
        url = get_svg_url("MSFT34")
        assert url is not None
        assert "MSFT34" in url

    def test_gogl35_bdr_retorna_url(self):
        assert get_svg_url("GOGL35") is not None

    def test_roxo34_retorna_url(self):
        assert get_svg_url("ROXO34") is not None

    def test_todos_os_tickers_mapeados_retornam_url(self):
        """Nenhum ticker em _SVG_ATIVOS pode retornar None."""
        for ticker in _SVG_ATIVOS:
            assert get_svg_url(ticker) is not None, f"get_svg_url({ticker!r}) retornou None"


# ---------------------------------------------------------------------------
# get_svg_url — tickers NÃO mapeados
# ---------------------------------------------------------------------------

class TestGetSvgUrlNaoMapeados:
    def test_ticker_desconhecido_retorna_none(self):
        assert get_svg_url("XXXX99") is None

    def test_ticker_vazio_retorna_none(self):
        assert get_svg_url("") is None

    def test_none_retorna_none(self):
        assert get_svg_url(None) is None

    def test_apenas_espaco_retorna_none(self):
        assert get_svg_url("   ") is None

    def test_tesouro_direto_nao_tem_icone(self):
        """Tesouro Direto não é um ticker de ação — não deve ter ícone."""
        assert get_svg_url("Tesouro Selic 2029") is None

    def test_ticker_parcial_nao_casa(self):
        assert get_svg_url("PETR") is None

    def test_ticker_com_sufixo_extra_nao_casa(self):
        assert get_svg_url("PETR4X") is None


# ---------------------------------------------------------------------------
# get_svg_url — case-insensitivity
# ---------------------------------------------------------------------------

class TestGetSvgUrlCaseInsensitive:
    def test_minusculo_retorna_url(self):
        assert get_svg_url("petr4") == get_svg_url("PETR4")

    def test_misto_retorna_url(self):
        assert get_svg_url("Petr4") == get_svg_url("PETR4")

    def test_bdr_minusculo(self):
        assert get_svg_url("msft34") == get_svg_url("MSFT34")

    def test_com_espacos_nas_bordas(self):
        """Espaços em volta do ticker devem ser ignorados."""
        assert get_svg_url("  PETR4  ") == get_svg_url("PETR4")


# ---------------------------------------------------------------------------
# get_svg_url — formato da URL retornada
# ---------------------------------------------------------------------------

class TestGetSvgUrlFormato:
    def test_url_comeca_com_base(self):
        url = get_svg_url("PETR4")
        assert url.startswith(_URL_BASE)

    def test_url_termina_com_svg(self):
        url = get_svg_url("VALE3")
        assert url.endswith(".svg")

    def test_url_contem_ticker_uppercase(self):
        url = get_svg_url("itub4")
        assert "ITUB4" in url

    def test_url_nao_contem_espacos(self):
        for ticker in _SVG_ATIVOS:
            url = get_svg_url(ticker)
            assert " " not in url, f"URL de {ticker!r} contém espaços: {url!r}"

    @pytest.mark.parametrize("ticker", list(_SVG_ATIVOS.keys()))
    def test_url_formato_padrao_para_todos(self, ticker):
        url = get_svg_url(ticker)
        esperado = f"{_URL_BASE}{ticker}.svg"
        assert url == esperado


# ---------------------------------------------------------------------------
# _URL_MAP — integridade do mapa pré-computado
# ---------------------------------------------------------------------------

class TestUrlMap:
    def test_url_map_nao_vazio(self):
        assert len(_URL_MAP) > 0

    def test_url_map_tem_mesmo_tamanho_que_svg_ativos(self):
        assert len(_URL_MAP) == len(_SVG_ATIVOS)

    def test_todas_chaves_em_maiusculas(self):
        for chave in _URL_MAP:
            assert chave == chave.upper(), f"Chave {chave!r} não está em uppercase"

    def test_todos_valores_sao_strings(self):
        for url in _URL_MAP.values():
            assert isinstance(url, str)

    def test_sem_urls_duplicadas(self):
        urls = list(_URL_MAP.values())
        assert len(urls) == len(set(urls)), "Existem URLs duplicadas no _URL_MAP"

    def test_url_base_presente_em_todas_entradas(self):
        for ticker, url in _URL_MAP.items():
            assert url.startswith(_URL_BASE), f"{ticker}: URL sem prefixo correto"


# ---------------------------------------------------------------------------
# get_all_tickers
# ---------------------------------------------------------------------------

class TestGetAllTickers:
    def test_retorna_lista(self):
        assert isinstance(get_all_tickers(), list)

    def test_lista_nao_vazia(self):
        assert len(get_all_tickers()) > 0

    def test_lista_ordenada(self):
        tickers = get_all_tickers()
        assert tickers == sorted(tickers)

    def test_todos_tickers_sao_strings(self):
        for t in get_all_tickers():
            assert isinstance(t, str)

    def test_tickers_conhecidos_presentes(self):
        tickers = get_all_tickers()
        for esperado in ("PETR4", "VALE3", "MSFT34", "GOGL35"):
            assert esperado in tickers

    def test_sem_duplicatas(self):
        tickers = get_all_tickers()
        assert len(tickers) == len(set(tickers))

    def test_mesmo_conjunto_que_svg_ativos(self):
        assert set(get_all_tickers()) == set(_SVG_ATIVOS.keys())


# ---------------------------------------------------------------------------
# _URL_BASE
# ---------------------------------------------------------------------------

class TestUrlBase:
    def test_url_base_e_string(self):
        assert isinstance(_URL_BASE, str)

    def test_url_base_comeca_com_https(self):
        assert _URL_BASE.startswith("https://")

    def test_url_base_termina_com_barra(self):
        assert _URL_BASE.endswith("/")

    def test_url_base_aponta_para_brapi(self):
        assert "brapi.dev" in _URL_BASE


# ---------------------------------------------------------------------------
# Cobertura de tickers por categoria (smoke tests)
# ---------------------------------------------------------------------------

class TestCoberturaPorCategoria:
    """Garante que as principais categorias de ativos estão representadas."""

    ACOES_ESPERADAS = ["PETR4", "VALE3", "ITUB4", "BBAS3", "WEGE3", "EMBR3"]
    BDRS_ESPERADAS  = ["MSFT34", "GOGL35", "AAPL34", "TSLA34", "META34", "NVDC34"]

    @pytest.mark.parametrize("ticker", ACOES_ESPERADAS)
    def test_acao_brasileira_mapeada(self, ticker):
        assert get_svg_url(ticker) is not None, f"Ação {ticker} sem ícone"

    @pytest.mark.parametrize("ticker", BDRS_ESPERADAS)
    def test_bdr_mapeado(self, ticker):
        assert get_svg_url(ticker) is not None, f"BDR {ticker} sem ícone"
