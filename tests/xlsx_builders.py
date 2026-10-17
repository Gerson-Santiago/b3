"""Builders sintéticos de XLSX/CSV B3 para testes de loader."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

POS_ACOES_COLUMNS = [
    "Produto", "Instituicao", "Conta", "Codigo de Negociacao",
    "CNPJ da Empresa", "Codigo ISIN / Distribuicao", "Tipo",
    "Escriturador", "Quantidade", "Quantidade Disponivel",
    "Quantidade Indisponivel", "Motivo", "Preco de Fechamento",
    "Valor Atualizado",
]

POS_BDR_COLUMNS = [
    "Produto", "Instituicao", "Conta", "Codigo de Negociacao",
    "Codigo ISIN / Distribuicao", "Tipo", "Escriturador",
    "Quantidade", "Quantidade Disponivel", "Quantidade Indisponivel",
    "Motivo", "Preco de Fechamento", "Valor Atualizado",
]

POS_TESOURO_COLUMNS = [
    "Produto", "Instituicao", "Codigo ISIN", "Indexador", "Vencimento",
    "Quantidade", "Quantidade Disponivel", "Quantidade Indisponivel",
    "Motivo", "Valor Aplicado", "Valor bruto", "Valor liquido",
    "Valor Atualizado",
]


def make_mov_xlsx(path: Path) -> None:
    rows = [
        ["Credito", "06/08/2026", "Compra", "PETR4", "Corretora X", 10, 30.0, 300.0],
        ["Credito", "07/08/2026", "Compra", "VALE3", "Corretora X", 5, 60.0, 300.0],
    ]
    cols = [
        "Entrada/Saída", "Data", "Movimentação", "Produto",
        "Instituição", "Quantidade", "Preço unitário", "Valor da Operação",
    ]
    pd.DataFrame(rows, columns=cols).to_excel(path, index=False, engine="openpyxl")


def make_mov_csv(path: Path) -> None:
    rows = (
        "Entrada/Saída;Data;Movimentação;Produto;Instituição;Quantidade;Preço unitário;Valor da Operação\n"
        "Credito;06/08/2026;Compra;PETR4;Corretora X;10;30,00;300,00\n"
    )
    path.write_text(rows, encoding="utf-8-sig")


def _with_total_rows(df: pd.DataFrame, columns: list[str], total_val: float) -> pd.DataFrame:
    n = len(columns)
    total_label = pd.DataFrame([[None] * (n - 1) + ["Total"]], columns=columns)
    total_value = pd.DataFrame([[None] * (n - 1) + [total_val]], columns=columns)
    return pd.concat([df, total_label, total_value])


def make_pos_xlsx(
    path: Path,
    acoes_val: float = 100.0,
    bdr_val: float = 200.0,
    tesouro_val: float = 50.0,
) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_a = pd.DataFrame(
            [["PETR4 - PETROBRAS", "Corr", 12345, "PETR4", 0, "BR", "ON", "Banco",
              10, 10, 0, "-", 10.0, acoes_val]],
            columns=POS_ACOES_COLUMNS,
        )
        _with_total_rows(df_a, POS_ACOES_COLUMNS, acoes_val).to_excel(
            writer, sheet_name="Acoes", index=False
        )

        df_b = pd.DataFrame(
            [["GOGL35 - ALPHABET", "Corr", 12345, "GOGL35", "BR", "BDR", "Banco",
              5, 5, 0, "-", 40.0, bdr_val]],
            columns=POS_BDR_COLUMNS,
        )
        _with_total_rows(df_b, POS_BDR_COLUMNS, bdr_val).to_excel(
            writer, sheet_name="BDR", index=False
        )

        df_t = pd.DataFrame(
            [["Tesouro Selic 2029", "Corr", "BRSTNCLF1R91", "SELIC", "01/03/2029",
              1, 1, 0, "-", 50.0, 50.0, 50.0, tesouro_val]],
            columns=POS_TESOURO_COLUMNS,
        )
        _with_total_rows(df_t, POS_TESOURO_COLUMNS, tesouro_val).to_excel(
            writer, sheet_name="Tesouro Direto", index=False
        )
