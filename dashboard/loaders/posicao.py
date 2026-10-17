from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd

from dashboard.utils import parse_money, parse_qtd

try:
    from dashboard.columns import ALIASES_POS, normaliza_colunas
except ImportError:  # pragma: no cover
    from columns import ALIASES_POS, normaliza_colunas


def _categorizar_sheet(sheet_name: str) -> str:
    nome = str(sheet_name or "").strip().lower()
    if "tesouro" in nome:
        return "TESOURO"
    if "bdr" in nome:
        return "BDR"
    return "AÇÕES"


def read_posicao_excel(file_source: Union[str, Path, BytesIO, object], qualidade: Any = None):
    xls = pd.ExcelFile(file_source, engine="openpyxl")
    frames = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, dtype=object)
        df = df.dropna(how="all").copy()
        if df.empty:
            continue

        df.columns = [str(c).strip() for c in df.columns]
        df = normaliza_colunas(df, ALIASES_POS)

        if "produto" not in df.columns:
            continue

        produto = df["produto"].fillna("").astype(str).str.strip().str.lower()
        df = df[~produto.isin({"", "-", "total"})].copy()
        if df.empty:
            continue

        if "valor_atualizado" in df.columns and "valor_operacao" not in df.columns:
            df["valor_operacao"] = df["valor_atualizado"]

        if "valor_operacao" in df.columns:
            df["valor_operacao"] = df["valor_operacao"].apply(parse_money)

        if "quantidade" in df.columns:
            df["quantidade"] = df["quantidade"].apply(parse_qtd)

        for col in ["produto", "instituicao", "conta", "tipo", "escriturador"]:
            if col in df.columns:
                df[col] = df[col].fillna("-").astype(str).str.strip()

        df["categoria"] = _categorizar_sheet(sheet_name)
        df["valor_liquido"] = df.get("valor_operacao", pd.Series(0, index=df.index))
        df["qtd_liquida"] = df.get("quantidade", pd.Series(0, index=df.index))
        df["entrada_saida"] = "credito"
        df["movimentacao"] = "posicao"

        if "data_posicao" not in df.columns:
            df["data_posicao"] = pd.Timestamp.today().normalize()

        if "data" not in df.columns:
            df["data"] = df["data_posicao"]

        df["data"] = pd.to_datetime(df["data"], errors="coerce").fillna(pd.Timestamp.today().normalize())
        df["mes"] = df["data"].dt.to_period("M").astype(str)
        frames.append(df)

    if not frames:
        raise ValueError("Nenhuma aba com o formato de posição foi lida corretamente.")

    concatenated = pd.concat(frames, ignore_index=True)
    from dashboard.models.ativos import anotar_ativos
    annotated = anotar_ativos(concatenated, qualidade)

    if qualidade is not None and "ativo_id" in annotated.columns:
        from dashboard.models.qualidade import Aviso

        for _, row in annotated.iterrows():
            aid = row.get("ativo_id")
            cat = row.get("categoria")
            if aid is not None and hasattr(aid, "classe") and cat is not None:
                if aid.classe != cat:
                    qualidade.add(
                        Aviso(
                            tipo="CLASSE_DIVERGENTE",
                            produto=str(row.get("produto") or ""),
                            detalhe=f"Aba {cat} difere da classe do ativo {aid.classe}",
                        )
                    )

    return annotated


def read_posicao_file(file_source: Union[str, Path, BytesIO, object], qualidade: Any = None):
    if file_source is None:
        raise ValueError("Arquivo de posição não informado.")

    if hasattr(file_source, "read"):
        name = str(getattr(file_source, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            return read_posicao_excel(file_source, qualidade=qualidade)
        return pd.DataFrame()

    path = Path(file_source)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return read_posicao_excel(path, qualidade=qualidade)
    return pd.DataFrame()


def load_posicao(file_source, qualidade: Any = None):
    return read_posicao_file(file_source, qualidade=qualidade)
