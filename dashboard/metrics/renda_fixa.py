"""Mapeamento canônico e metadados de Renda Fixa (Tesouro Direto)."""
from __future__ import annotations

from datetime import date

METADADOS_TESOURO: dict[str, dict] = {
    "Tesouro IPCA+ 2026": {
        "indexador": "inflação",
        "tipo": "tesouro-pos-fixado-ipca",
        "data_vencimento": date(2026, 8, 15),
        "vencimento_str": "15 de agosto de 2026",
    },
    "Tesouro IPCA+ 2032": {
        "indexador": "inflação",
        "tipo": "tesouro-pos-fixado-ipca",
        "data_vencimento": date(2032, 8, 15),
        "vencimento_str": "15 de agosto de 2032",
    },
    "Tesouro Educa+ 2026": {
        "indexador": "inflação",
        "tipo": "tesouro-pos-fixado-ipca",
        "data_vencimento": date(2026, 1, 15),
        "vencimento_str": "15 de janeiro de 2026 (Início da renda)",
    },
    "Tesouro Educa+ 2028": {
        "indexador": "inflação",
        "tipo": "tesouro-pos-fixado-ipca",
        "data_vencimento": date(2028, 1, 15),
        "vencimento_str": "15 de janeiro de 2028 (Início da renda)",
    },
    "Tesouro Selic 2028": {
        "indexador": "pos-fixada",
        "tipo": "tesouro-pos-fixado-selic",
        "data_vencimento": date(2028, 3, 1),
        "vencimento_str": "01 de março de 2028",
    },
    "Tesouro Selic 2031": {
        "indexador": "pos-fixada",
        "tipo": "tesouro-pos-fixado-selic",
        "data_vencimento": date(2031, 3, 1),
        "vencimento_str": "01 de março de 2031",
    },
    "Tesouro Prefixado com Juros Semestrais 2035": {
        "indexador": "prefixada",
        "tipo": "tesouro-prefixado",
        "data_vencimento": date(2035, 1, 1),
        "vencimento_str": "01 de janeiro de 2035",
    },
    "Tesouro Prefixado com Juros Semestrais 2037": {
        "indexador": "prefixada",
        "tipo": "tesouro-prefixado",
        "data_vencimento": date(2037, 1, 1),
        "vencimento_str": "01 de janeiro de 2037",
    },
}

RENDA_FIXA = {
    "inflação": {
        "tesouro-pos-fixado-ipca": [
            k for k, v in METADADOS_TESOURO.items() if v["tipo"] == "tesouro-pos-fixado-ipca"
        ]
    },
    "pos-fixada": {
        "tesouro-pos-fixado-selic": [
            k for k, v in METADADOS_TESOURO.items() if v["tipo"] == "tesouro-pos-fixado-selic"
        ]
    },
    "prefixada": {
        "tesouro-prefixado": [
            k for k, v in METADADOS_TESOURO.items() if v["tipo"] == "tesouro-prefixado"
        ]
    },
}

VENCIMENTOS_RENDA_FIXA = {
    v["tipo"]: {
        k: v["vencimento_str"]
        for k, v in METADADOS_TESOURO.items()
        if v["tipo"] == t
    }
    for t in {"tesouro-pos-fixado-ipca", "tesouro-pos-fixado-selic", "tesouro-prefixado"}
}


def filtrar_por_indexador(indexador: str) -> list[str]:
    return [ativo for ativo, meta in METADADOS_TESOURO.items() if meta["indexador"] == indexador]
