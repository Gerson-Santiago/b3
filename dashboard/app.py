from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dashboard.charts import bar_dy, bar_proventos, line_evolucao, pie_carteira, pie_carteira_por_categoria, pie_categoria
    from dashboard.loaders.movimentacao import read_movimentacao_file
    from dashboard.loaders.posicao import read_posicao_file
    from dashboard.metrics import compute_dy, compute_evolucao, compute_position, compute_position_categoria, compute_position_por_categoria, compute_proventos
except ImportError:  # pragma: no cover
    from charts import bar_dy, bar_proventos, line_evolucao, pie_carteira, pie_carteira_por_categoria, pie_categoria
    from loaders.movimentacao import read_movimentacao_file
    from loaders.posicao import read_posicao_file
    from metrics import compute_dy, compute_evolucao, compute_position, compute_position_categoria, compute_position_por_categoria, compute_proventos


def load_default_movimentacao():
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "xlsx" / "movimentacao"
    csv_dir = base_dir / "csv"

    for folder, prefix in [(data_dir, "movimentacao"), (base_dir / "xlsx", "movimentacao"), (csv_dir, "movimentacao")]:
        path = __import__("dashboard.loader", fromlist=["find_latest"]).find_latest(folder, prefix)
        if path is not None:
            return read_movimentacao_file(path)

    return pd.DataFrame()


def load_default_posicao():
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "xlsx" / "posicao"

    for folder, prefix in [(data_dir, "posicao"), (base_dir / "xlsx", "posicao")]:
        path = __import__("dashboard.loader", fromlist=["find_latest"]).find_latest(folder, prefix)
        if path is not None:
            return read_posicao_file(path)

    return pd.DataFrame()


def main():
    st.set_page_config(page_title="Dashboard B3", layout="wide")
    st.title("Dashboard de Investimentos B3")

    st.sidebar.header("Arquivos")
    uploaded_mov = st.sidebar.file_uploader("Movimentação (XLSX)", type=["xlsx", "xls"], key="movimentacao")
    uploaded_pos = st.sidebar.file_uploader("Posição (XLSX)", type=["xlsx", "xls"], key="posicao")

    mov_df = read_movimentacao_file(uploaded_mov) if uploaded_mov is not None else load_default_movimentacao()
    pos_df = read_posicao_file(uploaded_pos) if uploaded_pos is not None else load_default_posicao()

    if mov_df.empty and pos_df.empty:
        st.warning("Nenhum arquivo válido foi encontrado. Faça upload de movimentação e/ou posição da B3.")
        st.stop()

    mov_df = mov_df.copy()
    pos_df = pos_df.copy()

    if mov_df.empty:
        base_df = pos_df
    else:
        base_df = mov_df

    min_date = pd.to_datetime(base_df["data"], errors="coerce").min().date() if "data" in base_df.columns else pd.Timestamp.today().date()
    max_date = pd.to_datetime(base_df["data"], errors="coerce").max().date() if "data" in base_df.columns else pd.Timestamp.today().date()

    st.sidebar.header("Filtros")
    selection_df = pd.concat([mov_df, pos_df], ignore_index=True) if not mov_df.empty and not pos_df.empty else base_df
    instituicoes = sorted(selection_df["instituicao"].dropna().astype(str).unique().tolist()) if "instituicao" in selection_df.columns else []
    produtos = sorted(selection_df["produto"].dropna().astype(str).unique().tolist()) if "produto" in selection_df.columns else []

    selected_instituicao = st.sidebar.multiselect("Instituição", instituicoes)
    selected_produto = st.sidebar.multiselect("Produto", produtos)
    start_date, end_date = st.sidebar.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(start_date, tuple):
        start_date, end_date = start_date

    if not mov_df.empty:
        mov_filtered = mov_df.copy()
        mov_filtered = mov_filtered[(mov_filtered["data"] >= pd.Timestamp(start_date)) & (mov_filtered["data"] <= pd.Timestamp(end_date))]
        if selected_instituicao:
            mov_filtered = mov_filtered[mov_filtered["instituicao"].isin(selected_instituicao)]
        if selected_produto:
            mov_filtered = mov_filtered[mov_filtered["produto"].isin(selected_produto)]
    else:
        mov_filtered = pd.DataFrame()

    if not pos_df.empty:
        pos_filtered = pos_df.copy()
        if "data" in pos_filtered.columns:
            pos_filtered = pos_filtered[(pos_filtered["data"] >= pd.Timestamp(start_date)) & (pos_filtered["data"] <= pd.Timestamp(end_date))]
        if selected_instituicao:
            pos_filtered = pos_filtered[pos_filtered["instituicao"].isin(selected_instituicao)]
        if selected_produto:
            pos_filtered = pos_filtered[pos_filtered["produto"].isin(selected_produto)]
    else:
        pos_filtered = pd.DataFrame()

    pos = compute_position(pos_filtered if not pos_filtered.empty else mov_filtered)
    pos_categoria = compute_position_categoria(pos_filtered if not pos_filtered.empty else mov_filtered)
    pos_bdr = compute_position_por_categoria(pos_filtered if not pos_filtered.empty else mov_filtered, "BDR")
    pos_acoes = compute_position_por_categoria(pos_filtered if not pos_filtered.empty else mov_filtered, "ACOES")
    pos_tesouro = compute_position_por_categoria(pos_filtered if not pos_filtered.empty else mov_filtered, "TESOURO")
    proventos = compute_proventos(mov_filtered)
    evol = compute_evolucao(mov_filtered)
    dy = compute_dy(mov_filtered)

    col1, col2, col3 = st.columns(3)
    col1.metric("Movimentações", f"{len(mov_filtered):,}" if not mov_filtered.empty else "0")
    col2.metric("Valor líquido total", f"R$ {mov_filtered['valor_liquido'].sum():,.2f}" if not mov_filtered.empty else "R$ 0,00")
    col3.metric("Ativos na carteira", f"{pos['produto'].nunique():,}" if not pos.empty else "0")

    st.subheader("Carteira")
    if pos.empty:
        st.info("Nenhum ativo encontrado para o filtro selecionado.")
    else:
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            st.plotly_chart(pie_carteira(pos), use_container_width=True)
        with col_pie2:
            st.plotly_chart(pie_carteira_por_categoria(pos_categoria), use_container_width=True)

        st.markdown("### Distribuição por categoria")
        pie_cols = st.columns(3)
        with pie_cols[0]:
            if pos_bdr.empty:
                st.info("Sem BDR")
            else:
                st.plotly_chart(pie_categoria(pos_bdr), use_container_width=True)
        with pie_cols[1]:
            if pos_acoes.empty:
                st.info("Sem Ações")
            else:
                st.plotly_chart(pie_categoria(pos_acoes), use_container_width=True)
        with pie_cols[2]:
            if pos_tesouro.empty:
                st.info("Sem Tesouro Direto")
            else:
                st.plotly_chart(pie_categoria(pos_tesouro), use_container_width=True)

    st.subheader("Proventos por mês")
    if proventos.empty:
        st.info("Não há proventos no período selecionado.")
    else:
        st.plotly_chart(bar_proventos(proventos), use_container_width=True)

    st.subheader("Evolução do patrimônio")
    if evol.empty:
        st.info("Sem histórico de movimentação para a seleção atual.")
    else:
        st.plotly_chart(line_evolucao(evol), use_container_width=True)

    st.subheader("DY estimado")
    if dy.empty:
        st.info("Sem dados de DY para o filtro atual.")
    else:
        st.plotly_chart(bar_dy(dy), use_container_width=True)

    if not mov_filtered.empty:
        st.subheader("Detalhes da movimentação")
        st.dataframe(mov_filtered, use_container_width=True)

    if not pos_filtered.empty:
        st.subheader("Posição atual")
        st.dataframe(pos_filtered, use_container_width=True)


if __name__ == "__main__":
    main()
