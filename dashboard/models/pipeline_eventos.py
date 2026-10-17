"""Pipeline de preparação e aplicação ordenada de eventos corporativos."""
from __future__ import annotations

import pandas as pd

from dashboard.models.motor_posicao import _aplicar_linha
from dashboard.models.movimentacao import SINAL_ENTRADA_SAIDA
from dashboard.models.posicao_acumulada import PosicaoAcumulada

_COLUNAS_RESUMO = ["produto", "quantidade", "custo_total", "preco_medio"]
_COLUNAS_RESUMO_COMPLETO = ["ativo_id", "ativo", "produto", "quantidade", "custo_total", "preco_medio"]


def _preparar_movimentacoes(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or df.empty or "produto" not in df.columns:
        return None

    base = df.copy()

    if "valor_liquido" not in base.columns:
        if "valor_operacao" in base.columns:
            base["valor_liquido"] = pd.to_numeric(base["valor_operacao"], errors="coerce").fillna(0.0)
        else:
            base["valor_liquido"] = 0.0

    if "qtd_liquida" not in base.columns:
        if "quantidade" not in base.columns:
            return None
        if "entrada_saida" in base.columns:
            sinal = (
                base["entrada_saida"]
                .fillna("")
                .astype(str)
                .str.lower()
                .map(SINAL_ENTRADA_SAIDA)
                .fillna(0)
            )
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0) * sinal
        else:
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0).clip(lower=0)

    base["qtd_liquida"] = pd.to_numeric(base["qtd_liquida"], errors="coerce").fillna(0.0)
    base["valor_liquido"] = pd.to_numeric(base["valor_liquido"], errors="coerce").fillna(0.0)

    from dashboard.models.ativos import resolver_ativo_seguro

    if "ativo_id" not in base.columns:
        base["ativo_id"] = base["produto"].map(resolver_ativo_seguro)

    if "data" in base.columns:
        base = base.sort_values(["ativo_id", "data"], kind="mergesort", na_position="last")
    return base


def aplicar_eventos_ordenados(df: pd.DataFrame, aplicar_define: bool = True) -> pd.DataFrame:
    base = _preparar_movimentacoes(df)
    if base is None:
        return pd.DataFrame(columns=_COLUNAS_RESUMO)

    linhas = []
    for chave, grupo in base.groupby("ativo_id", sort=False):
        pos = PosicaoAcumulada()
        for _, row in grupo.iterrows():
            _aplicar_linha(pos, row, aplicar_define)

        codigo = chave.codigo if hasattr(chave, "codigo") else str(chave)
        linhas.append(
            {
                "ativo_id": chave,
                "ativo": codigo,
                "produto": codigo,
                "quantidade": pos.quantidade,
                "custo_total": pos.custo_total,
                "preco_medio": pos.preco_medio(),
            }
        )

    if not linhas:
        return pd.DataFrame(columns=_COLUNAS_RESUMO_COMPLETO)

    return pd.DataFrame(linhas).reset_index(drop=True)
