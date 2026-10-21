from __future__ import annotations

ALIASES_PROV_RECEBIDOS: dict[str, list[str]] = {
    "produto": ["Produto", "Ativo"],
    "data_pagamento": [
        "Pagamento",
        "Data do Pagamento",
        "Data Pagamento",
        "Data de Pagamento",
    ],
    "tipo_evento": [
        "Tipo de Evento",
        "Tipo Evento",
        "Tipo",
        "Evento",
    ],
    "instituicao": ["Instituição", "Instituicao", "Corretora"],
    "quantidade": ["Quantidade", "Qtd", "Qtd."],
    "preco_unitario": ["Preço unitário", "Preco unitario"],
    "valor_liquido": ["Valor líquido", "Valor liquido"],
}

__all__ = ["ALIASES_PROV_RECEBIDOS"]
