from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Union

import pandas as pd

from dashboard.models.movimentacao import classificar_tipo_provento
from dashboard.utils import parse_money, parse_qtd

try:
    from dashboard.aliases.proventos_recebidos import ALIASES_PROV_RECEBIDOS
    from dashboard.columns import normaliza_colunas
except ImportError:  # pragma: no cover
    from aliases.proventos_recebidos import ALIASES_PROV_RECEBIDOS
    from columns import normaliza_colunas


def _read_csv_with_encodings(path_or_buffer: Union[str, Path, BytesIO, object]) -> pd.DataFrame:
    encodings = ["utf-8-sig", "latin-1"]
    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(path_or_buffer, sep=";", decimal=",", encoding=encoding, dtype=str)
        except UnicodeDecodeError as exc:
            last_error = exc
        except ValueError as exc:
            if "codec can't decode" in str(exc).lower():
                last_error = exc
                continue
            raise

        if hasattr(path_or_buffer, "seek"):
            path_or_buffer.seek(0)

    if last_error is not None:
        raise last_error

    raise ValueError("Não foi possível decodificar o arquivo CSV de proventos recebidos.")


def _normalize_proventos_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = normaliza_colunas(df, ALIASES_PROV_RECEBIDOS)

    required = {
        "produto",
        "data_pagamento",
        "tipo_evento",
        "instituicao",
        "quantidade",
        "preco_unitario",
        "valor_liquido",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em proventos recebidos após normalização: {sorted(missing)}")

    # Descarte de linhas vazias ou de totalizadores da B3
    # 1. Se produto for nulo, '-', ou contiver 'total'
    prod_str = df["produto"].astype(str).str.strip()
    df = df[~prod_str.str.lower().isin({"", "-", "nan", "none", "total"})].copy()
    if df.empty:
        return pd.DataFrame(columns=list(required))

    # 2. Se valor_liquido contiver 'total'
    val_str = df["valor_liquido"].astype(str).str.strip().str.lower()
    df = df[val_str != "total"].copy()
    if df.empty:
        return pd.DataFrame(columns=list(required))

    # Parsing de datas
    raw_data = df["data_pagamento"].astype(str).str.strip()
    df["data_pagamento"] = pd.to_datetime(raw_data, format="%d/%m/%Y", dayfirst=True, errors="coerce")
    if df["data_pagamento"].isna().any() and not raw_data.empty:
        df["data_pagamento"] = df["data_pagamento"].fillna(
            pd.to_datetime(raw_data, format="mixed", dayfirst=True, errors="coerce")
        )

    # Descartar linhas sem data válida
    df = df[df["data_pagamento"].notna()].copy()
    if df.empty:
        return pd.DataFrame(columns=list(required))

    # Conversões numéricas
    df["quantidade"] = df["quantidade"].apply(parse_qtd)
    df["preco_unitario"] = df["preco_unitario"].apply(parse_money)
    df["valor_liquido"] = df["valor_liquido"].apply(parse_money)

    # Strings limpas
    df["produto"] = df["produto"].fillna("Sem nome").astype(str).str.strip()
    df["instituicao"] = df["instituicao"].fillna("Sem instituição").astype(str).str.strip()
    df["tipo_evento"] = df["tipo_evento"].fillna("").astype(str).str.strip()

    # Colunas de compatibilidade e enriquecimento
    df["data"] = df["data_pagamento"]
    df["mes"] = df["data_pagamento"].dt.to_period("M").astype(str)
    df["ano"] = df["data_pagamento"].dt.year
    df["tipo_provento"] = df["tipo_evento"].map(classificar_tipo_provento)
    df["entrada_saida"] = "credito"
    df["movimentacao"] = df["tipo_evento"].str.lower()
    df["qtd_liquida"] = df["quantidade"]
    df["valor_operacao"] = df["valor_liquido"]

    return df


def read_proventos_recebidos_csv(
    file_source: Union[str, Path, BytesIO, object], qualidade: Any = None
) -> pd.DataFrame:
    df = _read_csv_with_encodings(file_source)
    normalized = _normalize_proventos_df(df)
    from dashboard.models.ativos import anotar_ativos

    return anotar_ativos(normalized, qualidade)


def read_proventos_recebidos_excel(
    file_source: Union[str, Path, BytesIO, object], qualidade: Any = None
) -> pd.DataFrame:
    xls = pd.ExcelFile(file_source, engine="openpyxl")
    frames = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, dtype=object)
        df = df.dropna(how="all").copy()
        if df.empty:
            continue

        try:
            frames.append(_normalize_proventos_df(df))
        except ValueError:
            continue

    if not frames:
        raise ValueError("Nenhuma aba com o formato de proventos recebidos foi lida corretamente.")

    concatenated = pd.concat(frames, ignore_index=True)
    from dashboard.models.ativos import anotar_ativos

    return anotar_ativos(concatenated, qualidade)


def read_proventos_recebidos_file(
    file_source: Union[str, Path, BytesIO, object], qualidade: Any = None
) -> pd.DataFrame:
    if file_source is None:
        raise ValueError("Arquivo de proventos recebidos não informado.")

    if hasattr(file_source, "read"):
        name = str(getattr(file_source, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            return read_proventos_recebidos_excel(file_source, qualidade=qualidade)
        return read_proventos_recebidos_csv(file_source, qualidade=qualidade)

    path = Path(file_source)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return read_proventos_recebidos_excel(path, qualidade=qualidade)
    return read_proventos_recebidos_csv(path, qualidade=qualidade)


__all__ = [
    "read_proventos_recebidos_file",
    "read_proventos_recebidos_excel",
    "read_proventos_recebidos_csv",
]
