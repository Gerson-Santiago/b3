"""Dashboard de Investimentos B3 — ponto de entrada da aplicação Streamlit.

Responsabilidade única: configurar a página, montar a sidebar,
carregar/filtrar os dados brutos, construir o DashboardState e delegar
a renderização de cada aba para a view correspondente.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dashboard.filters import filtrar_dataframe
    from dashboard.loaders.default_loader import load_default
    from dashboard.loaders.movimentacao import read_movimentacao_file
    from dashboard.loaders.posicao import read_posicao_file
    from dashboard.models.eventos import listar_movimentacoes_pendentes
    from dashboard.state import DashboardState
    from dashboard.utils import find_latest
    from dashboard.views import carteira, evolucao, proventos, reconciliacao
except ImportError:  # pragma: no cover
    from filters import filtrar_dataframe
    from loaders.default_loader import load_default
    from loaders.movimentacao import read_movimentacao_file
    from loaders.posicao import read_posicao_file
    from models.eventos import listar_movimentacoes_pendentes
    from state import DashboardState
    from utils import find_latest
    from views import carteira, evolucao, proventos, reconciliacao

# Largura padrão dos componentes e tabelas no dashboard
DEFAULT_WIDTH = 'width="stretch"'

# ---------------------------------------------------------------------------
# Carregamento padrão de arquivos
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parents[1]

_MOV_SEARCH_DIRS = [
    (_BASE_DIR / "xlsx" / "movimentacao", "movimentacao"),
    (_BASE_DIR / "xlsx", "movimentacao"),
    (_BASE_DIR / "csv", "movimentacao"),
]
_POS_SEARCH_DIRS = [
    (_BASE_DIR / "xlsx" / "posicao", "posicao"),
    (_BASE_DIR / "xlsx", "posicao"),
]


def load_default_movimentacao() -> pd.DataFrame:
    for folder, prefix in _MOV_SEARCH_DIRS:
        try:
            path = find_latest(folder, prefix)
            if path is None:
                continue
            return read_movimentacao_file(path)
        except Exception as exc:
            st.error(f"Erro ao carregar movimentação padrão em {folder}: {exc}")
            raise

    message = "Nenhum arquivo de movimentação encontrado para carregar como padrão."
    st.error(message)
    raise FileNotFoundError(message)


def load_default_posicao() -> pd.DataFrame:
    for folder, prefix in _POS_SEARCH_DIRS:
        try:
            path = find_latest(folder, prefix)
            if path is None:
                continue
            return read_posicao_file(path)
        except Exception as exc:
            st.error(f"Erro ao carregar posição padrão em {folder}: {exc}")
            raise

    message = "Nenhum arquivo de posição encontrado para carregar como padrão."
    st.error(message)
    raise FileNotFoundError(message)


# ---------------------------------------------------------------------------
# Sidebar — carregamento de arquivos
# ---------------------------------------------------------------------------

def _carregar_dados(uploaded_mov, uploaded_pos) -> tuple[pd.DataFrame, pd.DataFrame]:
    mov_df = read_movimentacao_file(uploaded_mov) if uploaded_mov is not None else load_default_movimentacao()
    pos_df = read_posicao_file(uploaded_pos) if uploaded_pos is not None else load_default_posicao()
    return mov_df.copy(), pos_df.copy()


# ---------------------------------------------------------------------------
# Sidebar — filtros
# ---------------------------------------------------------------------------

def _resolver_periodo(periodo):
    if isinstance(periodo, (list, tuple)):
        start = periodo[0]
        end = periodo[1] if len(periodo) > 1 else periodo[0]
    else:
        start = end = periodo
    return start, end


def _sidebar_filtros(mov_df: pd.DataFrame, pos_df: pd.DataFrame):
    base_df = mov_df if not mov_df.empty else pos_df
    min_date = pd.to_datetime(base_df["data"], errors="coerce").min().date() if "data" in base_df.columns else pd.Timestamp.today().date()
    max_date = pd.to_datetime(base_df["data"], errors="coerce").max().date() if "data" in base_df.columns else pd.Timestamp.today().date()

    st.sidebar.header("Filtros")
    selection_df = pd.concat([mov_df, pos_df], ignore_index=True) if not mov_df.empty and not pos_df.empty else base_df
    instituicoes = sorted(selection_df["instituicao"].dropna().astype(str).unique().tolist()) if "instituicao" in selection_df.columns else []
    produtos = sorted(selection_df["produto"].dropna().astype(str).unique().tolist()) if "produto" in selection_df.columns else []

    selected_inst = st.sidebar.multiselect("Instituição", instituicoes)
    selected_prod = st.sidebar.multiselect("Produto", produtos)
    periodo = st.sidebar.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    start_date, end_date = _resolver_periodo(periodo)
    return selected_inst, selected_prod, start_date, end_date


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Dashboard B3", layout="wide")
    st.title("Dashboard de Investimentos B3")

    st.sidebar.header("Arquivos")
    uploaded_mov = st.sidebar.file_uploader("Movimentação (XLSX)", type=["xlsx", "xls"], key="movimentacao")
    uploaded_pos = st.sidebar.file_uploader("Posição (XLSX)", type=["xlsx", "xls"], key="posicao")

    mov_df, pos_df = _carregar_dados(uploaded_mov, uploaded_pos)

    if mov_df.empty and pos_df.empty:
        st.warning("Nenhum arquivo válido foi encontrado. Faça upload de movimentação e/ou posição da B3.")
        st.stop()

    pendentes = listar_movimentacoes_pendentes(mov_df)
    if pendentes:
        st.warning("Algumas movimentações estão com efeito pendente: " + ", ".join(pendentes))

    selected_inst, selected_prod, start_date, end_date = _sidebar_filtros(mov_df, pos_df)

    mov_filtered = filtrar_dataframe(mov_df, instituicoes=selected_inst, produtos=selected_prod, start_date=start_date, end_date=end_date)
    pos_filtered = filtrar_dataframe(pos_df, instituicoes=selected_inst, produtos=selected_prod)

    state = DashboardState.build(pos_df=pos_df, mov_filtered=mov_filtered, pos_filtered=pos_filtered, end_date=end_date)

    col1, col2, col3 = st.columns(3)
    col1.metric("Movimentações Filtradas", f"{len(mov_filtered):,}" if not mov_filtered.empty else "0")
    col2.metric("Fluxo Líquido Filtrado", f"R$ {mov_filtered['valor_liquido'].sum():,.2f}" if not mov_filtered.empty else "R$ 0,00")
    col3.metric("Ativos em Custódia", f"{state.pos['produto'].nunique():,}" if not state.pos.empty else "0")

    tab_carteira, tab_proventos, tab_evolucao, tab_reconciliacao = st.tabs(
        ["Carteira & Alocação", "Proventos & Renda", "Evolução & Aportes", "Reconciliação B3"]
    )

    with tab_carteira:
        carteira.render(state)
    with tab_proventos:
        proventos.render(state)
    with tab_evolucao:
        evolucao.render(state)
    with tab_reconciliacao:
        reconciliacao.render(state, pos_df_full=pos_df, end_date=end_date)


if __name__ == "__main__":
    main()
