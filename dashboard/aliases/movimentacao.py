from dashboard.aliases.common import normalize_alias

ALIASES_MOV = {
    "entrada_saida": ["Entrada/Saída", "Entrada/Saida", "entrada_saida"],
    "data": ["Data"],
    "movimentacao": ["Movimentação", "Movimentacao"],
    "produto": ["Produto"],
    "instituicao": ["Instituição", "Instituicao"],
    "quantidade": ["Quantidade"],
    "preco_unitario": ["Preço unitário", "Preco unitario"],
    "valor_operacao": ["Valor da Operação", "Valor da Operacao"],
}


__all__ = ["ALIASES_MOV", "normalize_alias"]
