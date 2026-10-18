"""Testes para dashboard.views._helpers.

Cobre:
- _obter_tipo_e_grupo: todas as categorias e edge cases
- _svg_icon_html: tickers mapeados/não-mapeados, atributos HTML, fallback
- _render_card: integração, rótulo, delta colorido, tipos de ativos
- render_section: DataFrame vazio e não-vazio
- render_cards_grid: DataFrame vazio, não-vazio, múltiplas linhas de cards
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.views._helpers import (
    _extrair_ticker,
    _obter_tipo_e_grupo,
    _render_card,
    _svg_icon_html,
    render_cards_grid,
    render_section,
)


# ---------------------------------------------------------------------------
# _extrair_ticker
# ---------------------------------------------------------------------------

class TestExtrairTicker:
    """Garante que o ticker é extraído corretamente do campo produto da B3."""

    @pytest.mark.parametrize("produto,esperado", [
        # Formato simples (ticker puro)
        ("PETR4",                               "PETR4"),
        ("VALE3",                               "VALE3"),
        ("MSFT34",                              "MSFT34"),
        # Formato completo da B3 (ticker + " - " + nome)
        ("PETR4 - PETROBRAS",                   "PETR4"),
        ("VALE3 - VALE S/A",                    "VALE3"),
        ("GOGL35 - GOLDEN OCEAN GROUP",         "GOGL35"),
        ("PETR4 - PETROLEO BRASILEIRO SA",      "PETR4"),
        ("B3SA3 - B3 S.A. BRASIL BOLSA BALCAO", "B3SA3"),
        # Tesouro Direto (sem " - ", retorna inteiro)
        ("Tesouro Selic 2029",                  "Tesouro Selic 2029"),
        ("Tesouro IPCA+ 2035",                  "Tesouro IPCA+ 2035"),
        # Edge cases
        ("  PETR4  ",                           "PETR4"),        # espaços nas bordas
        ("PETR4 - Nome - Extra",                "PETR4"),        # múltiplos " - "
    ])
    def test_extrair_ticker(self, produto, esperado):
        assert _extrair_ticker(produto) == esperado

    def test_ticker_extraido_casa_no_svg_map(self):
        """Ticker extraído de nome completo deve encontrar o ícone SVG."""
        html = _svg_icon_html(_extrair_ticker("PETR4 - PETROBRAS"))
        assert "<img" in html
        assert "PETR4" in html

    def test_ticker_extraido_bdr_casa_no_svg_map(self):
        html = _svg_icon_html(_extrair_ticker("MSFT34 - MICROSOFT CORP"))
        assert "<img" in html
        assert "MSFT34" in html

    def test_tesouro_sem_icone_apos_extracao(self):
        """Tesouro não tem ' - ', extrator retorna string completa e sem ícone."""
        assert _svg_icon_html(_extrair_ticker("Tesouro Selic 2029")) == ""


# ---------------------------------------------------------------------------
# _obter_tipo_e_grupo
# ---------------------------------------------------------------------------

class TestObterTipoEGrupo:
    """Cobre todas as categorias suportadas e casos de borda."""

    @pytest.mark.parametrize("entrada,esperado", [
        ("AÇÕES",          ("Ação", "das Ações")),
        ("ações",          ("Ação", "das Ações")),
        ("Acoes",          ("Ação", "das Ações")),
        ("ACOES",          ("Ação", "das Ações")),
        ("AÇÃO",           ("Ação", "das Ações")),
        ("BDR",            ("BDR", "dos BDRs")),
        ("bdr",            ("BDR", "dos BDRs")),
        ("BDRS",           ("BDR", "dos BDRs")),
        ("Tesouro Direto", ("Tesouro", "do Tesouro")),
        ("TESOURO SELIC",  ("Tesouro", "do Tesouro")),
        ("FII",            ("FII", "dos FIIs")),
        ("FIIS",           ("FII", "dos FIIs")),
        ("fii",            ("FII", "dos FIIs")),
        ("Cripto",         ("Cripto", "de Cripto")),
        ("",               ("Ativo", "de Ativo")),
    ])
    def test_categorias(self, entrada, esperado):
        assert _obter_tipo_e_grupo(entrada) == esperado

    def test_categoria_desconhecida_usa_title_case(self):
        tipo, grupo = _obter_tipo_e_grupo("DEBENTURE")
        assert tipo == "Debenture"
        assert grupo == "de Debenture"


# ---------------------------------------------------------------------------
# _svg_icon_html
# ---------------------------------------------------------------------------

class TestSvgIconHtml:
    """Testes unitários para a função _svg_icon_html."""

    def test_ticker_mapeado_retorna_html(self):
        html = _svg_icon_html("PETR4")
        assert html != ""
        assert "<img" in html

    def test_ticker_nao_mapeado_retorna_vazio(self):
        assert _svg_icon_html("XXXX99") == ""

    def test_ticker_vazio_retorna_vazio(self):
        assert _svg_icon_html("") == ""

    def test_url_correta_no_src(self):
        html = _svg_icon_html("VALE3")
        assert 'src="https://icons.brapi.dev/icons/VALE3.svg"' in html

    def test_loading_lazy_presente(self):
        html = _svg_icon_html("PETR4")
        assert 'loading="lazy"' in html

    def test_onerror_presente(self):
        """Se o CDN falhar, o elemento deve se ocultar via onerror."""
        html = _svg_icon_html("ITUB4")
        assert "onerror" in html
        assert "display" in html

    def test_dimensao_28px(self):
        html = _svg_icon_html("BBAS3")
        assert 'width="28"' in html
        assert 'height="28"' in html

    def test_alt_contem_ticker(self):
        html = _svg_icon_html("WEGE3")
        assert 'alt="WEGE3"' in html

    def test_case_insensitive_ticker(self):
        """Ticker em minúsculas deve apontar para a mesma URL que em maiúsculas."""
        html_lower = _svg_icon_html("petr4")
        html_upper = _svg_icon_html("PETR4")
        # A URL (src) deve ser idêntica — o alt pode diferir pelo input original
        assert "brapi.dev/icons/PETR4.svg" in html_lower
        assert "brapi.dev/icons/PETR4.svg" in html_upper

    def test_bdr_retorna_html(self):
        html = _svg_icon_html("MSFT34")
        assert "<img" in html
        assert "MSFT34" in html

    def test_ticker_tesouro_retorna_vazio(self):
        """Tesouro Direto não tem ícone — deve retornar string vazia."""
        assert _svg_icon_html("Tesouro Selic 2029") == ""

    @pytest.mark.parametrize("ticker", ["PETR4", "VALE3", "MSFT34", "GOGL35", "AAPL34"])
    def test_html_valido_varios_tickers(self, ticker):
        html = _svg_icon_html(ticker)
        assert html.startswith("<img")
        assert html.endswith(">")


# ---------------------------------------------------------------------------
# _render_card — integração com mocks do Streamlit
# ---------------------------------------------------------------------------

class TestRenderCard:
    """Testa que _render_card chama as primitivas certas do Streamlit."""

    def _make_row(self, **kwargs) -> pd.Series:
        defaults = dict(
            produto="PETR4",
            categoria="AÇÕES",
            quantidade=100,
            valor_abs=3500.0,
            preco_medio=30.0,
            custo_total=3000.0,
            pl=500.0,
            variacao_pct=16.67,
            peso_pct=10.0,
            peso_pct_no_produto=100.0,
        )
        defaults.update(kwargs)
        return pd.Series(defaults)

    def _col_mock(self):
        m = MagicMock()
        m.__enter__ = lambda s: s
        m.__exit__ = MagicMock(return_value=False)
        return m

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_chama_container_com_border(self, mock_container, mock_cols, mock_md):
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row())
        mock_container.assert_called_with(border=True)

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_markdown_chamado_para_cabecalho(self, mock_container, mock_cols, mock_md):
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row())
        assert mock_md.call_count >= 1

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_icone_svg_no_html_para_ticker_mapeado(self, mock_container, mock_cols, mock_md):
        """Card de PETR4 deve incluir a tag <img> com o ícone SVG."""
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row(produto="PETR4"))
        html_calls = " ".join(str(c) for c in mock_md.call_args_list)
        assert "<img" in html_calls or "brapi.dev" in html_calls

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_sem_icone_para_ticker_nao_mapeado(self, mock_container, mock_cols, mock_md):
        """Produto sem ícone: card renderiza sem quebrar."""
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row(produto="DESCONHECIDO99"))
        assert mock_md.called

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_tesouro_sem_icone_renderiza_ok(self, mock_container, mock_cols, mock_md):
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row(
            produto="Tesouro Selic 2029",
            categoria="Tesouro Direto",
            quantidade=0.5,
            variacao_pct=1.5,
            custo_total=7000.0,
        ))
        assert mock_md.called

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_pl_negativo_renderiza_ok(self, mock_container, mock_cols, mock_md):
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row(pl=-200.0, variacao_pct=-6.67, custo_total=3000.0))
        assert mock_md.called

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    def test_sem_custo_delta_off_renderiza_ok(self, mock_container, mock_cols, mock_md):
        """Quando custo_total == 0, o delta deve ser 'off' (neutro) sem erros."""
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        mock_cols.return_value = [self._col_mock(), self._col_mock()]
        _render_card(self._make_row(custo_total=0.0, pl=0.0, variacao_pct=0.0))
        assert mock_md.called


# ---------------------------------------------------------------------------
# render_section
# ---------------------------------------------------------------------------

class TestRenderSection:
    @patch("streamlit.dataframe")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    def test_dataframe_vazio_exibe_info(self, mock_md, mock_info, mock_df):
        render_section(pd.DataFrame(), "Título Teste", "Msg Vazia")
        mock_md.assert_called_with("#### Título Teste")
        mock_info.assert_called_with("Msg Vazia")
        mock_df.assert_not_called()

    @patch("streamlit.dataframe")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    def test_dataframe_nao_vazio_exibe_tabela(self, mock_md, mock_info, mock_df):
        render_section(pd.DataFrame({"col": [1, 2]}), "Título Teste", "Msg Vazia")
        mock_df.assert_called_once()
        mock_info.assert_not_called()

    @patch("streamlit.dataframe")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    def test_nivel_customizado(self, mock_md, mock_info, mock_df):
        render_section(pd.DataFrame(), "Título", "Vazio", nivel="##")
        mock_md.assert_called_with("## Título")


# ---------------------------------------------------------------------------
# render_cards_grid
# ---------------------------------------------------------------------------

class TestRenderCardsGrid:
    """Cobre a grade de cards: vazio, não-vazio, múltiplas linhas."""

    def _make_df(self, n: int = 1) -> pd.DataFrame:
        rows = []
        for i in range(n):
            rows.append({
                "produto": f"PETR{i}",
                "categoria": "Ações",
                "quantidade": 100,
                "valor_abs": float(1000 * (i + 1)),
                "preco_medio": 30.0,
                "custo_total": 900.0 * (i + 1),
                "pl": 100.0,
                "variacao_pct": 11.11,
                "peso_pct": 10.0,
                "peso_pct_no_produto": 100.0,
            })
        return pd.DataFrame(rows)

    def _col_factory(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        mocks = []
        for _ in range(n):
            m = MagicMock()
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            mocks.append(m)
        return mocks

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    @patch("streamlit.info")
    def test_dataframe_vazio_exibe_info(self, mock_info, mock_container, mock_cols, mock_md):
        render_cards_grid(pd.DataFrame(), "Título", "Sem dados")
        mock_info.assert_called_with("Sem dados")

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    @patch("streamlit.info")
    def test_dataframe_nao_vazio_nao_chama_info(self, mock_info, mock_container, mock_cols, mock_md):
        mock_cols.side_effect = self._col_factory
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        render_cards_grid(self._make_df(1), "Título", "Sem dados")
        mock_info.assert_not_called()

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    @patch("streamlit.info")
    def test_dois_cards_usa_uma_linha(self, mock_info, mock_container, mock_cols, mock_md):
        """2 cards num grid de 2 → 2 containers renderizados (1 card cada)."""
        mock_cols.side_effect = self._col_factory
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        render_cards_grid(self._make_df(2), "Título", "Sem dados", cards_por_linha=2)
        # Cada card chama container(border=True) exatamente 1 vez
        border_calls = [c for c in mock_container.call_args_list if c.kwargs.get("border")]
        assert len(border_calls) == 2

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    @patch("streamlit.info")
    def test_tres_cards_usa_duas_linhas(self, mock_info, mock_container, mock_cols, mock_md):
        """3 cards num grid de 2 → 3 containers renderizados (linhas 2+1)."""
        mock_cols.side_effect = self._col_factory
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        render_cards_grid(self._make_df(3), "Título", "Sem dados", cards_por_linha=2)
        # 3 cards → 3 chamadas container(border=True)
        border_calls = [c for c in mock_container.call_args_list if c.kwargs.get("border")]
        assert len(border_calls) == 3

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.container")
    @patch("streamlit.info")
    def test_rotulo_valor_customizado_nao_levanta_excecao(self, mock_info, mock_container, mock_cols, mock_md):
        mock_cols.side_effect = self._col_factory
        mock_container.return_value.__enter__ = lambda s: s
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        render_cards_grid(
            self._make_df(1), "Meus Cards", "Sem dados",
            rotulo_valor="Custo histórico",
        )
        assert mock_md.called
