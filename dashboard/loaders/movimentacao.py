from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd

from dashboard.models.movimentacao import SINAL_ENTRADA_SAIDA
from dashboard.utils import parse_money

try:
    from dashboard.columns import ALIASES_MOV, normaliza_colunas
except ImportError:  # pragma: no cover
    from columns import ALIASES_MOV, normaliza_colunas


def _read_csv_with_encodings(path_or_buffer):
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

    raise ValueError("Não foi possível decodificar o arquivo CSV de movimentação.")


def _normalize_movimentacao_df(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = normaliza_colunas(df, ALIASES_MOV)

    required = {
        "entrada_saida",
        "data",
        "movimentacao",
        "produto",
        "instituicao",
        "quantidade",
        "preco_unitario",
        "valor_operacao",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes na movimentação após normalização: {sorted(missing)}")

    raw_data = df["data"].astype(str).str.strip()
    df["data"] = pd.to_datetime(raw_data, format="%d/%m/%Y", dayfirst=True, errors="coerce")
    if df["data"].isna().any() and not raw_data.empty:
        df["data"] = df["data"].fillna(pd.to_datetime(raw_data, format="mixed", dayfirst=True, errors="coerce"))

    for col in ["quantidade", "preco_unitario", "valor_operacao"]:
        df[col] = df[col].apply(parse_money)

    df["entrada_saida"] = df["entrada_saida"].fillna("").astype(str).str.strip().str.lower()
    df["movimentacao"] = df["movimentacao"].fillna("").astype(str).str.strip().str.lower()
    df["produto"] = df["produto"].fillna("Sem nome").astype(str).str.strip()
    df["instituicao"] = df["instituicao"].fillna("Sem instituição").astype(str).str.strip()

    df["sinal"] = df["entrada_saida"].map(SINAL_ENTRADA_SAIDA).fillna(0)
    df["qtd_liquida"] = df["quantidade"] * df["sinal"]
    df["valor_liquido"] = df["valor_operacao"] * df["sinal"]
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df


def read_movimentacao_csv(file_source: Union[str, Path, BytesIO, object], qualidade: Any = None):
    df = _read_csv_with_encodings(file_source)
    normalized = _normalize_movimentacao_df(df)
    from dashboard.models.ativos import anotar_ativos

    return anotar_ativos(normalized, qualidade)


def read_movimentacao_excel(file_source: Union[str, Path, BytesIO, object], qualidade: Any = None):
    xls = pd.ExcelFile(file_source, engine="openpyxl")
    frames = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, dtype=object)
        df = df.dropna(how="all").copy()
        if df.empty:
            continue

        try:
            frames.append(_normalize_movimentacao_df(df))
        except ValueError:
            continue

    if not frames:
        raise ValueError("Nenhuma aba com o formato de movimentação foi lida corretamente.")

    concatenated = pd.concat(frames, ignore_index=True)
    from dashboard.models.ativos import anotar_ativos

    return anotar_ativos(concatenated, qualidade)


def read_movimentacao_file(file_source: Union[str, Path, BytesIO, object], qualidade: Any = None):
    if file_source is None:
        raise ValueError("Arquivo de movimentação não informado.")

    if hasattr(file_source, "read"):
        name = str(getattr(file_source, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            return read_movimentacao_excel(file_source, qualidade=qualidade)
        return read_movimentacao_csv(file_source, qualidade=qualidade)

    path = Path(file_source)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return read_movimentacao_excel(path, qualidade=qualidade)
    return read_movimentacao_csv(path, qualidade=qualidade)


def load_movimentacao(file_source, qualidade: Any = None):
    return read_movimentacao_file(file_source, qualidade=qualidade)
