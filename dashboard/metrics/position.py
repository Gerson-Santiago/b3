from __future__ import annotations

import pandas as pd

from dashboard.models.ativos import Classe, resolver_ativo_seguro

# ---------------------------------------------------------------------------
# SSoT — contratos de schema (única fonte da verdade para colunas)
# ---------------------------------------------------------------------------

#: Colunas garantidas por compute_position (e seus retornos vazios).
COLUNAS_POSICAO: list[str] = ["produto", "quantidade", "valor", "valor_abs"]

#: Colunas garantidas por compute_position_categoria (e seus retornos vazios).
COLUNAS_CATEGORIA: list[str] = ["categoria", "valor", "quantidade"]


# ---------------------------------------------------------------------------
# Mapeamento categoria
# ---------------------------------------------------------------------------

def obter_mapa_categorias(pos_df: pd.DataFrame) -> dict[str, str]:
    if pos_df is None or pos_df.empty or "categoria" not in pos_df.columns:
        return {}

    mapa: dict[str, str] = {}
    for _, row in pos_df.iterrows():
        prod = str(row.get("produto") or "").strip()
        cat = str(row.get("categoria") or "").strip()
        if not prod or not cat:
            continue
        aid = row.get("ativo_id")
        if aid is None or not hasattr(aid, "codigo"):
            aid = resolver_ativo_seguro(prod)
        if aid and aid.codigo:
            mapa[aid.codigo] = cat
        mapa[prod] = cat
        mapa[prod.upper()] = cat

    return mapa


# ---------------------------------------------------------------------------
# Classificação de ativos
# ---------------------------------------------------------------------------

def classificar_ativo_por_mapa(produto: object, mapa_categorias: dict[str, str] | None = None) -> str:
    if not mapa_categorias:
        return "Não classificado"

    texto = str(produto or "").strip()
    if not texto:
        return "Não classificado"

    if texto in mapa_categorias:
        return mapa_categorias[texto]

    if texto.upper() in mapa_categorias:
        return mapa_categorias[texto.upper()]

    aid = resolver_ativo_seguro(texto)
    if aid and aid.codigo in mapa_categorias:
        return mapa_categorias[aid.codigo]

    return "Não classificado"


def classificar_ativo(produto, mapa_categorias: dict[str, str] | None = None):
    if mapa_categorias:
        return classificar_ativo_por_mapa(produto, mapa_categorias)

    aid = resolver_ativo_seguro(produto)
    if aid.classe != Classe.DESCONHECIDO:
        return aid.classe.value if hasattr(aid.classe, "value") else str(aid.classe)

    texto = str(produto or "").strip()
    if not texto:
        return "Não classificado"
    return "Não classificado"


# ---------------------------------------------------------------------------
# Normalização de entrada
# ---------------------------------------------------------------------------

def _normalize_positions(df) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUNAS_POSICAO)

    base = df.copy()
    if "valor_liquido" not in base.columns and "valor_operacao" in base.columns:
        base["valor_liquido"] = base["valor_operacao"]
    if "qtd_liquida" not in base.columns and "quantidade" in base.columns:
        base["qtd_liquida"] = base["quantidade"]

    if "produto" not in base.columns:
        return pd.DataFrame(columns=COLUNAS_POSICAO)

    return base


# ---------------------------------------------------------------------------
# Enriquecimento de categoria (DRY — única implementação)
# ---------------------------------------------------------------------------

def _enriquecer_categoria(pos: pd.DataFrame, df_orig: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta coluna 'categoria' a *pos* usando *df_orig* como referência.

    Única fonte da verdade para a lógica de enriquecimento de categoria:
    tenta mapear produto→categoria a partir de df_orig; usa classificar_ativo
    como fallback para produtos não encontrados.
    """
    if "categoria" in df_orig.columns:
        categoria_map = (
            df_orig[["produto", "categoria"]]
            .drop_duplicates()
            .set_index("produto")["categoria"]
        )
        pos["categoria"] = pos["produto"].map(categoria_map).fillna(
            pos["produto"].apply(classificar_ativo)
        )
    else:
        pos["categoria"] = pos["produto"].apply(classificar_ativo)
    return pos


# ---------------------------------------------------------------------------
# Cálculo de posições
# ---------------------------------------------------------------------------

def compute_position(df) -> pd.DataFrame:
    base = _normalize_positions(df)
    if base.empty:
        return pd.DataFrame(columns=COLUNAS_POSICAO)

    agg_spec = dict(quantidade=("qtd_liquida", "sum"), valor=("valor_liquido", "sum"))
    if "valor_aplicado" in base.columns:
        agg_spec["valor_aplicado"] = ("valor_aplicado", "sum")

    pos = (
        base.groupby("produto", as_index=False)
        .agg(**agg_spec)
    )
    pos = pos[pos["quantidade"].abs() > 0].sort_values("valor", key=lambda s: s.abs(), ascending=False)
    pos["valor"] = pos["valor"].round(2)
    pos["valor_abs"] = pos["valor"].abs().round(2)
    if "valor_aplicado" in pos.columns:
        pos["valor_aplicado"] = pos["valor_aplicado"].round(2)
    return pos


def compute_position_categoria(df) -> pd.DataFrame:
    pos = compute_position(df).copy()
    if pos.empty:
        return pd.DataFrame(columns=COLUNAS_CATEGORIA)

    pos = _enriquecer_categoria(pos, df)

    resumo = pos.groupby("categoria", as_index=False).agg(valor=("valor_abs", "sum"), quantidade=("quantidade", "sum"))
    resumo["valor"] = resumo["valor"].round(2)
    return resumo.sort_values("valor", ascending=False)


def compute_position_por_categoria(df, categoria) -> pd.DataFrame:
    pos = compute_position(df).copy()
    if pos.empty:
        return pd.DataFrame(columns=COLUNAS_POSICAO)

    pos = _enriquecer_categoria(pos, df)

    return pos[pos["categoria"].eq(categoria)].sort_values("valor_abs", ascending=False)
