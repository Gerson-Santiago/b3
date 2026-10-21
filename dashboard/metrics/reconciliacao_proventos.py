from __future__ import annotations

import pandas as pd

from dashboard.models.ativos import resolver_ativo_seguro
from dashboard.models.eventos import efeito_movimentacao
from dashboard.models.movimentacao import is_credito

_COLUNAS_RECONCILIACAO_PROVENTOS = [
    "ativo",
    "total_movimentacao",
    "total_extrato_proventos",
    "delta",
    "status",
]


def _extrair_ativo_codigo(row: pd.Series, col_cand: list[str]) -> str:
    for col in col_cand:
        if col in row and pd.notna(row[col]):
            val = row[col]
            if hasattr(val, "codigo"):
                return val.codigo
            # Se for string, tenta resolver se não for já ticker
            res = resolver_ativo_seguro(val)
            if hasattr(res, "codigo"):
                return res.codigo
            return str(val).strip()
    return "Desconhecido"


def reconciliar_proventos(
    mov_df: pd.DataFrame | None,
    prov_df: pd.DataFrame | None,
    tolerancia: float = 0.01,
) -> pd.DataFrame:
    """Cruza proventos da Movimentação com o Extrato de Proventos Recebidos.

    Retorna DataFrame com colunas:
    - ativo: Ticker canônico
    - total_movimentacao: R$ creditado na movimentação
    - total_extrato_proventos: R$ creditado no extrato de proventos
    - delta: total_extrato_proventos - total_movimentacao
    - status: 'OK' ou 'Divergente'
    """
    has_mov = mov_df is not None and not mov_df.empty
    has_prov = prov_df is not None and not prov_df.empty

    if not has_mov and not has_prov:
        return pd.DataFrame(columns=_COLUNAS_RECONCILIACAO_PROVENTOS)

    # 1. Processar Movimentação (apenas créditos de proventos)
    if has_mov:
        from dashboard.models.movimentacao import is_provento

        mask_prov = mov_df.apply(
            lambda r: bool(is_provento(r.get("movimentacao"))) and is_credito(r.get("entrada_saida")),
            axis=1,
        )
        mov_proventos = mov_df.loc[mask_prov].copy()
        if not mov_proventos.empty:
            mov_proventos["_ativo_key"] = mov_proventos.apply(
                lambda r: _extrair_ativo_codigo(r, ["ativo_id", "ativo", "ticker", "produto"]),
                axis=1,
            )
            mov_proventos["_valor"] = pd.to_numeric(mov_proventos["valor_liquido"], errors="coerce").fillna(0.0)
            mov_agg = mov_proventos.groupby("_ativo_key", as_index=False)["_valor"].sum().rename(
                columns={"_ativo_key": "ativo", "_valor": "total_movimentacao"}
            )
        else:
            mov_agg = pd.DataFrame(columns=["ativo", "total_movimentacao"])
    else:
        mov_agg = pd.DataFrame(columns=["ativo", "total_movimentacao"])

    # 2. Processar Extrato de Proventos Recebidos
    if has_prov:
        prov_copy = prov_df.copy()
        prov_copy["_ativo_key"] = prov_copy.apply(
            lambda r: _extrair_ativo_codigo(r, ["ativo_id", "ativo", "ticker", "produto"]),
            axis=1,
        )
        prov_copy["_valor"] = pd.to_numeric(prov_copy["valor_liquido"], errors="coerce").fillna(0.0)
        prov_agg = prov_copy.groupby("_ativo_key", as_index=False)["_valor"].sum().rename(
            columns={"_ativo_key": "ativo", "_valor": "total_extrato_proventos"}
        )
    else:
        prov_agg = pd.DataFrame(columns=["ativo", "total_extrato_proventos"])

    # 3. Cruzamento externo (outer join)
    tabela = pd.merge(mov_agg, prov_agg, on="ativo", how="outer")
    tabela["total_movimentacao"] = pd.to_numeric(tabela["total_movimentacao"], errors="coerce").fillna(0.0)
    tabela["total_extrato_proventos"] = pd.to_numeric(tabela["total_extrato_proventos"], errors="coerce").fillna(0.0)

    tabela["delta"] = (tabela["total_extrato_proventos"] - tabela["total_movimentacao"]).round(2)
    tabela["status"] = tabela["delta"].abs().apply(lambda d: "OK" if d <= tolerancia else "Divergente")

    # Ordenar por ativo
    tabela = tabela.sort_values("ativo", kind="mergesort").reset_index(drop=True)
    return tabela[_COLUNAS_RECONCILIACAO_PROVENTOS]


__all__ = ["reconciliar_proventos"]
