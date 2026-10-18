from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_file
from dashboard.metrics.preco_medio import compute_preco_medio
from dashboard.metrics.reconciliacao import comparar, data_do_arquivo, quantidade_ate
from dashboard.models.ativos import resolver_ativo


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("CPFE3 - CPFL ENERGIA S.A.", "CPFE3"),
        ("CPFE3 - CPFL ENERGIA S/A", "CPFE3"),
        ("PETR4 - PETROLEO BRASILEIRO S/A - PETROBRAS", "PETR4"),
        ("ITSA4 - ITAUSA S/A", "ITSA4"),
    ],
)
def test_ticker_normaliza_variacoes_de_nome(valor, esperado):
    assert resolver_ativo(valor).codigo == esperado


def test_read_posicao_fixture_keeps_decimal_quantities_for_tesouro_and_itsa():
    pos_2025 = read_posicao_file(Path(__file__).resolve().parents[1] / "xlsx" / "posicao" / "posicao-2025-01-01-18-26-12.xlsx")
    itsa = pos_2025[pos_2025["produto"].astype(str).str.contains("ITSA4", case=False, na=False)].iloc[0]
    assert itsa["quantidade"] == pytest.approx(24.15)

    pos_2026 = read_posicao_file(Path(__file__).resolve().parents[1] / "xlsx" / "posicao" / "posicao-2026-01-01-18-24-42.xlsx")
    tesouro = pos_2026[pos_2026["produto"].astype(str).str.contains(r"Tesouro Educa\+ 2026", case=False, na=False)].iloc[0]
    assert tesouro["quantidade"] == pytest.approx(0.13)


def test_reconciliacao_renomeia_nubr35_para_roxo34():
    qtd_mov = pd.DataFrame({"produto": ["NUBR35 - NU HOLDINGS LTD."], "quantidade": [20.0]})
    pos = pd.DataFrame({"produto": ["ROXO34 - NU HOLDINGS LTD."], "quantidade": [20.0]})

    result = comparar(qtd_mov, pos)

    assert result["ativo"].tolist() == ["ROXO34"]
    assert result["qtd_mov"].iloc[0] == pytest.approx(20.0)


def test_quantidade_ate_inclusive_and_exclusive_cutoff():
    mov = pd.DataFrame(
        [
            {"data": "2024-01-01", "produto": "PETR4", "movimentacao": "compra", "entrada_saida": "credito", "quantidade": 10},
            {"data": "2024-01-02", "produto": "PETR4", "movimentacao": "venda", "entrada_saida": "debito", "quantidade": 4},
            {"data": "2024-01-03", "produto": "PETR4", "movimentacao": "compra", "entrada_saida": "credito", "quantidade": 2},
        ]
    )
    mov["data"] = pd.to_datetime(mov["data"])

    assert quantidade_ate(mov, "2024-01-02") == pytest.approx({"PETR4": 6.0})
    assert quantidade_ate(mov, "2024-01-01") == pytest.approx({"PETR4": 10.0})
    assert quantidade_ate(mov, "2024-01-02", inclusive=False) == pytest.approx({"PETR4": 10.0})


def test_comparar_includes_position_without_movement_and_keeps_delta():
    qtd_mov = pd.DataFrame({"produto": ["PETR4", "ROXO34"], "quantidade": [6.0, 0.0]})
    pos = pd.DataFrame({"produto": ["PETR4", "ROXO34"], "quantidade": [6.0, 3.0]})

    result = comparar(qtd_mov, pos)

    assert list(result.columns) == ["ativo", "qtd_mov", "qtd_pos", "delta"]
    assert result.set_index("ativo").loc["ROXO34", "delta"] == 3.0


def test_comparar_matches_synthetic_sale():
    qtd_mov = pd.DataFrame({"produto": ["BBAS3"], "quantidade": [6.0]})
    pos = pd.DataFrame({"produto": ["BBAS3"], "quantidade": [6.0]})

    result = comparar(qtd_mov, pos)

    assert result.iloc[0].to_dict() == {"ativo": "BBAS3", "qtd_mov": 6.0, "qtd_pos": 6.0, "delta": 0.0}


def test_data_do_arquivo_extracts_date_from_filename():
    assert data_do_arquivo("posicao-2026-10-16-18-23-46.xlsx") == "2026-10-16"
    assert data_do_arquivo("movimentacao-2026-01-01-20-22-00.xlsx") == "2026-01-01"


def test_nubank_migration_rows_are_present_in_fixture_and_renamed_to_roxo34():
    mov = read_movimentacao_file(Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx")
    rows = mov[mov["produto"].astype(str).str.contains("NU HOLDINGS|NUBR|ROXO", case=False, na=False)]

    assert not rows.empty
    assert (rows["produto"].astype(str).str.contains("NUBR33|NUBR35|ROXO34", case=False, na=False)).all()
    assert rows[rows["data"].dt.strftime("%Y-%m-%d") == "2023-08-15"]["produto"].tolist() == [
        "NUBR33 - NU HOLDINGS LTD.",
        "NUBR35 - NU HOLDINGS LTD.",
        "ROXO34 - NU HOLDINGS",
    ]
    # Com o catálogo único, resolver_ativo() retorna o código canônico: NUBR33 e NUBR35 → ROXO34
    assert set(rows["produto"].map(lambda p: resolver_ativo(p).codigo)) == {"ROXO34"}



def test_quantidade_ate_warns_and_renames_nubank_transfer_without_double_counting():
    mov = read_movimentacao_file(Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx")

    qtd = quantidade_ate(mov, "2026-10-16")

    assert qtd["ROXO34"] == pytest.approx(20.0)
    assert sum(v for k, v in qtd.items() if k == "ROXO34") == pytest.approx(20.0)


def test_quantidade_ate_matches_expected_real_fixture_snapshot_values():
    mov = read_movimentacao_file(Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx")

    qtd = quantidade_ate(mov, "2026-10-16")

    assert qtd["PETR4"] == pytest.approx(23.0)
    assert qtd["VALE3"] == pytest.approx(12.0)
    assert qtd["GOGL35"] == pytest.approx(17.0)
    assert qtd["B3SA3"] == pytest.approx(57.0)
    assert qtd["CPFE3"] == pytest.approx(3.0)
    assert qtd["MSFT34"] == pytest.approx(11.0)


def test_compute_preco_medio_uses_nan_when_cost_is_unknown_for_roxo34_and_matches_quantity_ate():
    mov = read_movimentacao_file(Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx")
    metricas = compute_preco_medio(mov).copy()
    metricas["produto_norm"] = metricas["produto"].map(lambda v: resolver_ativo(v).codigo)

    roxo = metricas[metricas["produto_norm"] == "ROXO34"].iloc[0]
    assert pd.isna(roxo["preco_medio"]) or roxo["preco_medio"] == pytest.approx(0.0, abs=1e-9) is False

    qtd = quantidade_ate(mov, "2026-10-16")
    final = metricas.groupby("produto_norm", as_index=False)["quantidade"].sum()
    for simbolo, quantidade in qtd.items():
        linha = final[final["produto_norm"] == simbolo]
        assert not linha.empty
        assert linha["quantidade"].iloc[0] == pytest.approx(quantidade)


def test_reconciliacao_atualizacao_no_op_vs_define_7_ativos():
    """Valida que para os 7 ativos reais, atualizar com define ou ignorar (no-op) produz o mesmo saldo (PETR4 e ROXO34 sem flag)."""
    mov = read_movimentacao_file(Path(__file__).resolve().parent / "fixtures" / "movimentacao_7_ativos.xlsx")
    pos = read_posicao_file(Path(__file__).resolve().parent / "fixtures" / "posicao_7_ativos.xlsx")

    qtd_com_define = quantidade_ate(mov, "2026-10-16", aplicar_define=True)
    qtd_sem_define = quantidade_ate(mov, "2026-10-16", aplicar_define=False)

    # Para os 7 ativos, as duas versões são idênticas
    for ativo, qtd in qtd_com_define.items():
        assert qtd_sem_define[ativo] == pytest.approx(qtd)

    tabela = comparar(qtd_com_define, pos, mov_df=mov, data_corte="2026-10-16")
    assert "observacao" in tabela.columns

    # Como não diferem para os 7 ativos, PETR4 e ROXO34 ficam sem a flag
    linha_petr = tabela[tabela["ativo"] == "PETR4"].iloc[0]
    assert linha_petr["observacao"] == ""

    linha_roxo = tabela[tabela["ativo"] == "ROXO34"].iloc[0]
    assert linha_roxo["observacao"] == ""


def test_reconciliacao_sinaliza_ajuste_quando_define_e_no_op_diferem():
    """Quando o evento define altera o saldo em relação ao histórico acumulado no-op, a flag 'ajuste por atualização' é exibida."""
    mov_sintetico = pd.DataFrame(
        [
            {"data": "2024-01-01", "produto": "TEST3", "movimentacao": "compra", "entrada_saida": "credito", "quantidade": 10.0},
            # Evento define ajusta o saldo para 15.0 (divergindo do acumulado cronológico 10.0)
            {"data": "2024-02-01", "produto": "TEST3", "movimentacao": "atualizacao", "entrada_saida": "credito", "quantidade": 15.0},
        ]
    )
    mov_sintetico["data"] = pd.to_datetime(mov_sintetico["data"])
    pos_sintetico = pd.DataFrame([{"produto": "TEST3", "quantidade": 15.0}])

    qtd_def = quantidade_ate(mov_sintetico, "2024-12-31", aplicar_define=True)
    qtd_no_op = quantidade_ate(mov_sintetico, "2024-12-31", aplicar_define=False)

    assert qtd_def["TEST3"] == pytest.approx(15.0)
    assert qtd_no_op["TEST3"] == pytest.approx(10.0)

    tabela = comparar(qtd_def, pos_sintetico, mov_df=mov_sintetico, data_corte="2024-12-31")
    linha = tabela[tabela["ativo"] == "TEST3"].iloc[0]
    assert linha["observacao"] == "ajuste por atualização"


