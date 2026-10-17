from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dashboard.charts import bar_dy, bar_proventos, line_comparativo_patrimonio_e_aportes, line_evolucao, pie_carteira, pie_carteira_por_categoria, pie_categoria
    from dashboard.loaders.movimentacao import read_movimentacao_file
    from dashboard.loaders.posicao import read_posicao_file
    from dashboard.metrics import compute_dy, compute_evolucao, compute_position, compute_position_categoria, compute_proventos
    from dashboard.metrics.dy import compute_dy_metrics
    from dashboard.metrics.evolucao import compute_evolucao_separada
    from dashboard.metrics.position import obter_mapa_categorias, classificar_ativo_por_mapa
    from dashboard.metrics.reconciliacao import comparar, quantidade_ate
    from dashboard.models.eventos import listar_movimentacoes_pendentes
    from dashboard.utils import find_latest
except ImportError:  # pragma: no cover
    from charts import bar_dy, bar_proventos, line_comparativo_patrimonio_e_aportes, line_evolucao, pie_carteira, pie_carteira_por_categoria, pie_categoria
    from loaders.movimentacao import read_movimentacao_file
    from loaders.posicao import read_posicao_file
    from metrics import compute_dy, compute_evolucao, compute_position, compute_position_categoria, compute_proventos
    from metrics.dy import compute_dy_metrics
    from metrics.evolucao import compute_evolucao_separada
    from metrics.position import obter_mapa_categorias, classificar_ativo_por_mapa
    from metrics.reconciliacao import comparar, quantidade_ate
    from models.eventos import listar_movimentacoes_pendentes
    from utils import find_latest


def load_default_movimentacao():
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "xlsx" / "movimentacao"
    csv_dir = base_dir / "csv"

    for folder, prefix in [(data_dir, "movimentacao"), (base_dir / "xlsx", "movimentacao"), (csv_dir, "movimentacao")]:
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


def load_default_posicao():
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "xlsx" / "posicao"

    for folder, prefix in [(data_dir, "posicao"), (base_dir / "xlsx", "posicao")]:
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

    pendentes = listar_movimentacoes_pendentes(mov_df)
    if pendentes:
        st.warning("Algumas movimentações estão com efeito pendente na tabela central: " + ", ".join(pendentes))

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
    periodo = st.sidebar.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(periodo, (list, tuple)):
        start_date = periodo[0]
        end_date = periodo[1] if len(periodo) > 1 else periodo[0]
    else:
        start_date = periodo
        end_date = periodo

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
        if selected_instituicao:
            pos_filtered = pos_filtered[pos_filtered["instituicao"].isin(selected_instituicao)]
        if selected_produto:
            pos_filtered = pos_filtered[pos_filtered["produto"].isin(selected_produto)]
    else:
        pos_filtered = pd.DataFrame()

    # SSOT de categorias
    mapa_cat = obter_mapa_categorias(pos_df) if not pos_df.empty else {}

    # Posição consolidada
    pos = compute_position(pos_filtered if not pos_filtered.empty else mov_filtered)
    if not pos.empty:
        pos["categoria"] = pos["produto"].apply(lambda p: classificar_ativo_por_mapa(p, mapa_cat))
        pos_categoria = (
            pos.groupby("categoria", as_index=False)
            .agg(valor=("valor_abs", "sum"), quantidade=("quantidade", "sum"))
            .sort_values("valor", ascending=False)
        )
    else:
        pos_categoria = pd.DataFrame(columns=["categoria", "valor", "quantidade"])

    proventos = compute_proventos(mov_filtered)
    evol_dict = compute_evolucao_separada(mov_filtered, [pos_df] if not pos_df.empty else [])
    dy_metrics = compute_dy_metrics(mov_filtered, pos_df, data_referencia=end_date)

    col1, col2, col3 = st.columns(3)
    col1.metric("Movimentações Filtradas", f"{len(mov_filtered):,}" if not mov_filtered.empty else "0")
    col2.metric("Fluxo Líquido Filtrado", f"R$ {mov_filtered['valor_liquido'].sum():,.2f}" if not mov_filtered.empty else "R$ 0,00")
    col3.metric("Ativos em Custódia", f"{pos['produto'].nunique():,}" if not pos.empty else "0")

    tab_carteira, tab_proventos, tab_evolucao, tab_reconciliacao = st.tabs(
        ["📊 Carteira & Alocação", "💰 Proventos & Renda", "📈 Evolução & Aportes", "⚖️ Reconciliação B3"]
    )

    with tab_carteira:
        if pos.empty:
            st.info("Nenhum ativo encontrado para os filtros selecionados.")
        else:
            separar_bdr_acoes = st.toggle(
                "Separar BDR e Ações no gráfico de alocação",
                value=False,
                key="toggle_separar_bdr_acoes",
            )

            if separar_bdr_acoes:
                pos_categoria_exibida = pos_categoria.copy()
            else:
                # Agrupa BDR + AÇÕES como "Bolsa de Valores" (padrão)
                pos_cat_agrupada = pos_categoria.copy()
                pos_cat_agrupada["categoria"] = pos_cat_agrupada["categoria"].replace(
                    {"AÇÕES": "Bolsa de Valores", "BDR": "Bolsa de Valores"}
                )
                pos_categoria_exibida = (
                    pos_cat_agrupada
                    .groupby("categoria", as_index=False)
                    .agg(valor=("valor", "sum"), quantidade=("quantidade", "sum"))
                    .sort_values("valor", ascending=False)
                )

            col_pie1, col_pie2 = st.columns(2)
            with col_pie1:
                st.plotly_chart(pie_carteira(pos), width="stretch")
            with col_pie2:
                st.plotly_chart(pie_carteira_por_categoria(pos_categoria_exibida), width="stretch")

            st.markdown("### Posição Detalhada em Custódia")

            pos_acoes_bdr = pos[pos["categoria"].isin(["AÇÕES", "BDR"])].sort_values("produto")
            pos_tesouro = pos[pos["categoria"] == "TESOURO"].sort_values("produto")

            if separar_bdr_acoes:
                pos_acoes = pos[pos["categoria"] == "AÇÕES"].sort_values("produto")
                pos_bdr = pos[pos["categoria"] == "BDR"].sort_values("produto")

                st.markdown("#### 📈 Ações")
                if pos_acoes.empty:
                    st.info("Nenhum ativo de Ações em custódia.")
                else:
                    st.dataframe(pos_acoes, width="stretch")

                st.markdown("#### 🌎 BDR")
                if pos_bdr.empty:
                    st.info("Nenhum BDR em custódia.")
                else:
                    st.dataframe(pos_bdr, width="stretch")
            else:
                st.markdown("#### 📈 Bolsa de Valores (Ações & BDR)")
                if pos_acoes_bdr.empty:
                    st.info("Nenhum ativo de Ações ou BDR em custódia.")
                else:
                    st.dataframe(pos_acoes_bdr, width="stretch")

            st.markdown("#### 🏦 Tesouro Direto")
            if pos_tesouro.empty:
                st.info("Nenhum ativo de Tesouro Direto em custódia.")
            else:
                st.dataframe(pos_tesouro, width="stretch")

            if not pos_filtered.empty:
                st.caption("ℹ️ Dados baseados no snapshot de custódia mais recente da B3.")

    with tab_proventos:
        if proventos.empty:
            st.info("Não há proventos registrados no período selecionado.")
        else:
            st.plotly_chart(bar_proventos(proventos), width="stretch")

        st.markdown("### Métricas de Dividend Yield (LTM) & Yield on Cost")
        if dy_metrics.empty:
            st.info("Sem dados suficientes para cálculo de Dividend Yield.")
        else:
            st.plotly_chart(bar_dy(dy_metrics), width="stretch")
            st.dataframe(
                dy_metrics[["ticker", "valor_atual", "custo_total", "proventos_12m", "dy_ltm_pct", "yield_on_cost_pct"]],
                width="stretch",
            )

    with tab_evolucao:
        st.markdown("### Curva Comparativa de Patrimônio e Aportes")
        st.plotly_chart(
            line_comparativo_patrimonio_e_aportes(evol_dict["curva_aportes"], evol_dict["curva_patrimonio"]),
            width="stretch",
        )
        if not mov_filtered.empty:
            st.markdown("### Detalhamento das Movimentações")
            st.dataframe(mov_filtered, width="stretch")

    with tab_reconciliacao:
        st.markdown("### Auditoria de Reconciliação (Movimentações vs Posição)")
        if not mov_df.empty and not pos_df.empty:
            qtd_calculada = quantidade_ate(mov_df, end_date)
            tabela_conciliacao = comparar(qtd_calculada, pos_df)
            st.dataframe(tabela_conciliacao, width="stretch")
            deltas_divergentes = tabela_conciliacao[tabela_conciliacao["delta"].abs() > 1e-4]
            if deltas_divergentes.empty:
                st.success("✅ Todos os ativos auditados estão 100% conciliados com o extrato da B3.")
            else:
                st.warning(f"⚠️ {len(deltas_divergentes)} ativo(s) com divergência entre movimentações e posição.")
        else:
            st.info("Carregue tanto a movimentação quanto a posição para conferência de reconciliação.")


if __name__ == "__main__":
    main()
