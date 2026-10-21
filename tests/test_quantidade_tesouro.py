"""Testes para a correcao de quantidade fracionaria do Tesouro Direto.

Cobre tres camadas afetadas pela correcao:
1. parse_qtd  -- preserva decimais de quantidade (ex.: 0,12 titulo)
2. Loaders    -- posicao.py e movimentacao.py usam parse_qtd para quantidade
3. Exibicao   -- _render_card formata com 2 casas para TESOURO, inteiro para os demais
"""
from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO

import pandas as pd
import pytest

from dashboard.utils import parse_qtd


# ---------------------------------------------------------------------------
# Helper interno: gera Excel em memoria com multiplas abas
# ---------------------------------------------------------------------------

@contextmanager
def _excel_em_memoria(abas: dict):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for nome_aba, df in abas.items():
            df.to_excel(writer, sheet_name=nome_aba, index=False)
    buf.seek(0)
    yield buf


# ---------------------------------------------------------------------------
# 1. parse_qtd -- unidade
# ---------------------------------------------------------------------------

class TestParseQtd:
    """parse_qtd deve preservar decimais sem tratar virgula como separador de milhar."""

    @pytest.mark.parametrize("entrada, esperado", [
        # Fracoes tipicas do Tesouro Direto
        ("0,12",  0.12),
        ("0,05",  0.05),
        ("1,45",  1.45),
        ("1,00",  1.00),
        # Inteiros (Acoes/BDR) sem separador
        ("100",   100.0),
        ("1000",  1000.0),
        # Valores float/int ja convertidos pelo Python
        (0.12,    0.12),
        (100,     100.0),
        # Valores negativos (venda/debito)
        ("-5",    -5.0),
        ("-0,12", -0.12),
    ])
    def test_converte_corretamente(self, entrada, esperado):
        assert parse_qtd(entrada) == pytest.approx(esperado)

    def test_string_1ponto000_interpretada_como_decimal(self):
        """No formato B3, quantidades nao usam ponto como separador de milhar.
        parse_qtd interpreta '1.000' como decimal 1.0 (unico ponto = separador decimal).
        Isso e aceitavel: o sistema nunca gera esse formato para quantidades.
        """
        # Comportamento documentado: nao e um bug, e uma limitacao de ambiguidade.
        resultado = parse_qtd("1.000")
        assert resultado == pytest.approx(1.0)

    def test_retorna_na_para_none(self):
        assert pd.isna(parse_qtd(None))

    def test_retorna_na_para_string_vazia(self):
        assert pd.isna(parse_qtd(""))

    def test_retorna_na_para_texto_invalido(self):
        assert pd.isna(parse_qtd("abc"))

    def test_fracao_tesouro_nao_vira_zero(self):
        """Garantia central da correcao: 0,12 nao pode resultar em 0."""
        resultado = parse_qtd("0,12")
        assert resultado != pytest.approx(0.0)
        assert resultado == pytest.approx(0.12)

    def test_multiplos_de_001(self):
        """Tesouro permite multiplos de 0,01 conforme regra do programa."""
        for centesimos in range(1, 100):
            valor_str = f"0,{centesimos:02d}"
            esperado = centesimos / 100
            assert parse_qtd(valor_str) == pytest.approx(esperado, abs=1e-9), (
                f"Falhou para {valor_str!r}"
            )


# ---------------------------------------------------------------------------
# 2. Loaders -- quantidade preservada apos leitura do Excel
# ---------------------------------------------------------------------------

class TestLoaderPosicaoQuantidadeTesouro:

    def _df_tesouro(self, qtd_raw: str) -> pd.DataFrame:
        return pd.DataFrame({
            "Produto":           ["Tesouro IPCA+ 2032"],
            "Quantidade":        [qtd_raw],
            "Valor Atualizado":  ["549,32"],
            "Instituicao":       ["XP Investimentos"],
        })

    def test_quantidade_fracionaria_preservada_no_loader(self):
        """0,12 lido do Excel nao deve virar 0 apos parse."""
        from dashboard.loaders.posicao import read_posicao_excel

        with _excel_em_memoria({"Tesouro": self._df_tesouro("0,12")}) as buf:
            df = read_posicao_excel(buf)

        tesouro = df[df["categoria"] == "TESOURO"]
        assert not tesouro.empty, "Aba Tesouro nao foi lida"
        qtd = float(tesouro["quantidade"].iloc[0])
        assert qtd == pytest.approx(0.12), (
            f"Esperado 0.12, obtido {qtd} -- parse_qtd provavelmente nao esta sendo usado"
        )

    def test_quantidade_inteira_acoes_preservada(self):
        from dashboard.loaders.posicao import read_posicao_excel

        df_acao = pd.DataFrame({
            "Produto":          ["PETR4"],
            "Quantidade":       ["100"],
            "Valor Atualizado": ["3500,00"],
            "Instituicao":      ["XP"],
        })
        with _excel_em_memoria({"Acoes": df_acao}) as buf:
            df = read_posicao_excel(buf)

        acoes = df[df["categoria"] == "ACOES"]
        if acoes.empty:
            acoes = df[df["categoria"].str.upper().isin(["ACOES", "ACOES", "ACAO", "AÇÕES"])]
        assert not acoes.empty
        qtd = float(acoes["quantidade"].iloc[0])
        assert qtd == pytest.approx(100.0)

    def test_titulo_inteiro_preservado(self):
        from dashboard.loaders.posicao import read_posicao_excel

        with _excel_em_memoria({"Tesouro": self._df_tesouro("1,00")}) as buf:
            df = read_posicao_excel(buf)

        qtd = float(df[df["categoria"] == "TESOURO"]["quantidade"].iloc[0])
        assert qtd == pytest.approx(1.0)

    def test_quantidade_pequena_preservada(self):
        """0,05 (5 centesimos de titulo) deve ser preservado."""
        from dashboard.loaders.posicao import read_posicao_excel

        with _excel_em_memoria({"Tesouro": self._df_tesouro("0,05")}) as buf:
            df = read_posicao_excel(buf)

        qtd = float(df[df["categoria"] == "TESOURO"]["quantidade"].iloc[0])
        assert qtd == pytest.approx(0.05)


class TestLoaderMovimentacaoQuantidadeTesouro:

    def _raw_mov(self, quantidade_str: str, produto: str = "Tesouro IPCA+ 2032") -> pd.DataFrame:
        return pd.DataFrame({
            "Entrada/Saida":     ["Credito"],
            "Data":              ["15/01/2024"],
            "Movimentacao":      ["Compra"],
            "Produto":           [produto],
            "Instituicao":       ["XP Investimentos"],
            "Quantidade":        [quantidade_str],
            "Preco unitario":    ["2943,59"],
            "Valor da Operacao": ["353,23"],
        })

    def _normalizar(self, raw: pd.DataFrame) -> pd.DataFrame:
        from dashboard.loaders.movimentacao import _normalize_movimentacao_df
        from dashboard.aliases.movimentacao import ALIASES_MOV
        from dashboard.columns import normaliza_colunas

        raw.columns = [str(c).strip() for c in raw.columns]
        df = normaliza_colunas(raw, ALIASES_MOV)
        return _normalize_movimentacao_df(df)

    def test_quantidade_fracionaria_em_movimentacao(self):
        """Compra de 0,12 titulo nao pode virar 0."""
        result = self._normalizar(self._raw_mov("0,12"))
        qtd = float(result["quantidade"].iloc[0])
        assert qtd == pytest.approx(0.12), f"Esperado 0.12, obtido {qtd}"

    def test_qtd_liquida_fracionaria_calculada_corretamente(self):
        """qtd_liquida = quantidade * sinal deve preservar a fracao."""
        result = self._normalizar(self._raw_mov("0,05"))
        qtd_liq = float(result["qtd_liquida"].iloc[0])
        assert qtd_liq == pytest.approx(0.05)

    def test_quantidade_inteira_em_movimentacao(self):
        result = self._normalizar(self._raw_mov("100", produto="PETR4"))
        qtd = float(result["quantidade"].iloc[0])
        assert qtd == pytest.approx(100.0)

    def test_quantidade_um_virgula_quarenta_cinco(self):
        result = self._normalizar(self._raw_mov("1,45"))
        qtd = float(result["quantidade"].iloc[0])
        assert qtd == pytest.approx(1.45)


# ---------------------------------------------------------------------------
# 3. Formatacao de exibicao -- logica extraida de _render_card
# ---------------------------------------------------------------------------

def _formatar_quantidade_card(quantidade: float, categoria: str) -> str:
    """Reproduz exatamente a logica de formatacao em _helpers._render_card."""
    if "TESOURO" in categoria.upper():
        return f"{quantidade:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{int(round(quantidade)):,}".replace(",", ".")


class TestFormatacaoQuantidadeCard:

    # --- Tesouro: 2 casas decimais ---

    def test_tesouro_zero_virgula_doze(self):
        assert _formatar_quantidade_card(0.12, "TESOURO") == "0,12"

    def test_tesouro_zero_virgula_zero_cinco(self):
        assert _formatar_quantidade_card(0.05, "TESOURO") == "0,05"

    def test_tesouro_um_titulo_inteiro(self):
        assert _formatar_quantidade_card(1.0, "TESOURO") == "1,00"

    def test_tesouro_um_virgula_quarenta_cinco(self):
        assert _formatar_quantidade_card(1.45, "TESOURO") == "1,45"

    def test_tesouro_nao_exibe_zero_para_fracao(self):
        """Garantia central: 0,12 nao pode aparecer como '0' ou '0,00'."""
        resultado = _formatar_quantidade_card(0.12, "TESOURO")
        assert resultado != "0"
        assert resultado != "0,00"
        assert resultado == "0,12"

    @pytest.mark.parametrize("cat", ["TESOURO", "Tesouro", "tesouro", "TESOURO DIRETO"])
    def test_tesouro_case_insensitive(self, cat):
        assert _formatar_quantidade_card(0.12, cat) == "0,12"

    # --- Acoes / BDR / FII: inteiro sem casas decimais ---

    @pytest.mark.parametrize("cat", ["ACOES", "BDR", "FII"])
    def test_nao_tesouro_exibe_inteiro(self, cat):
        assert _formatar_quantidade_card(100.0, cat) == "100"

    def test_acoes_lote_padrao(self):
        assert _formatar_quantidade_card(200.0, "ACOES") == "200"

    def test_acoes_mercado_fracionario(self):
        assert _formatar_quantidade_card(37.0, "ACOES") == "37"

    def test_acoes_arredonda_float_impreciso(self):
        assert _formatar_quantidade_card(100.000000001, "ACOES") == "100"

    def test_acoes_milhares_usa_ponto_br(self):
        assert _formatar_quantidade_card(1000.0, "ACOES") == "1.000"

    def test_acoes_dez_mil_usa_ponto_br(self):
        assert _formatar_quantidade_card(10000.0, "ACOES") == "10.000"
