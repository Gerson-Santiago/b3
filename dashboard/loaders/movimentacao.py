from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd

try:
    from dashboard.columns import ALIASES_MOV, normaliza_colunas
except ImportError:  # pragma: no cover
    from columns import ALIASES_MOV, normaliza_colunas


def parse_money(value):
    if value is None or pd.isna(value):
        return pd.NA

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if not text:
        return pd.NA

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = text.replace("R$", "").replace("USD", "").replace("BRL", "")
    text = text.replace(" ", "")
    text = text.replace("(", "").replace(")", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if len(text.split(",")[-1]) <= 2:
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "." in text:
        if text.count(".") > 1:
            parts = text.split(".")
            if len(parts[-1]) <= 2:
                text = "".join(parts[:-1]) + "." + parts[-1]
            else:
                text = "".join(parts)
        elif len(text.split(".")[-1]) > 2:
            text = text.replace(".", "")

    try:
        number = float(text)
        return -number if negative else number
    except ValueError:
        return pd.NA


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


def read_movimentacao_csv(file_source: Union[str, Path, BytesIO, object]):
    df = _read_csv_with_encodings(file_source)
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

    df = df.copy()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")

    for col in ["quantidade", "preco_unitario", "valor_operacao"]:
        df[col] = df[col].apply(parse_money)

    df["entrada_saida"] = df["entrada_saida"].fillna("").astype(str).str.strip().str.lower()
    df["movimentacao"] = df["movimentacao"].fillna("").astype(str).str.strip().str.lower()
    df["produto"] = df["produto"].fillna("Sem nome").astype(str).str.strip()
    df["instituicao"] = df["instituicao"].fillna("Sem instituição").astype(str).str.strip()

    sinal = {"credito": 1, "crédito": 1, "debito": -1, "débito": -1}
    df["sinal"] = df["entrada_saida"].map(sinal).fillna(0)
    df["qtd_liquida"] = df["quantidade"] * df["sinal"]
    df["valor_liquido"] = df["valor_operacao"] * df["sinal"]
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df


def read_movimentacao_excel(file_source: Union[str, Path, BytesIO, object]):
    xls = pd.ExcelFile(file_source, engine="openpyxl")
    frames = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name, dtype=object)
        df = df.dropna(how="all").copy()
        if df.empty:
            continue

        df.columns = [str(c).strip() for c in df.columns]
        df = normaliza_colunas(df, ALIASES_MOV)

        required = {"entrada_saida", "data", "movimentacao", "produto", "instituicao", "quantidade", "preco_unitario", "valor_operacao"}
        if not required.issubset(df.columns):
            continue

        df = df.copy()
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        for col in ["quantidade", "preco_unitario", "valor_operacao"]:
            df[col] = df[col].apply(parse_money)

        df["entrada_saida"] = df["entrada_saida"].fillna("").astype(str).str.strip().str.lower()
        df["movimentacao"] = df["movimentacao"].fillna("").astype(str).str.strip().str.lower()
        df["produto"] = df["produto"].fillna("Sem nome").astype(str).str.strip()
        df["instituicao"] = df["instituicao"].fillna("Sem instituição").astype(str).str.strip()

        sinal = {"credito": 1, "crédito": 1, "debito": -1, "débito": -1}
        df["sinal"] = df["entrada_saida"].map(sinal).fillna(0)
        df["qtd_liquida"] = df["quantidade"] * df["sinal"]
        df["valor_liquido"] = df["valor_operacao"] * df["sinal"]
        df["mes"] = df["data"].dt.to_period("M").astype(str)
        frames.append(df)

    if not frames:
        raise ValueError("Nenhuma aba com o formato de movimentação foi lida corretamente.")

    return pd.concat(frames, ignore_index=True)


def read_movimentacao_file(file_source: Union[str, Path, BytesIO, object]):
    if file_source is None:
        raise ValueError("Arquivo de movimentação não informado.")

    if hasattr(file_source, "read"):
        name = str(getattr(file_source, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            return read_movimentacao_excel(file_source)
        return read_movimentacao_csv(file_source)

    path = Path(file_source)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return read_movimentacao_excel(path)
    return read_movimentacao_csv(path)


def load_movimentacao(file_source):
    return read_movimentacao_file(file_source)
