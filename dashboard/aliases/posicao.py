from dashboard.aliases.common import normalize_alias

ALIASES_POS = {
    "data_posicao": ["Data da posição", "Data da posicao"],
    "produto": ["Produto"],
    "instituicao": ["Instituição", "Instituicao"],
    "conta": ["Conta"],
    "codigo_negociacao": ["Código de Negociação", "Codigo de Negociacao"],
    "cnpj_empresa": ["CNPJ da Empresa"],
    "codigo_isin": ["Código ISIN / Distribuição", "Codigo ISIN / Distribuicao"],
    "tipo": ["Tipo"],
    "escriturador": ["Escriturador"],
    "quantidade": ["Quantidade"],
    "quantidade_disponivel": ["Quantidade Disponível", "Quantidade Disponivel"],
    "quantidade_indisponivel": ["Quantidade Indisponível", "Quantidade Indisponivel"],
    "motivo": ["Motivo"],
    "preco_fechamento": ["Preço de Fechamento", "Preco de Fechamento"],
    "valor_atualizado": ["Valor Atualizado"],
    "categoria": ["Categoria"],
}


__all__ = ["ALIASES_POS", "normalize_alias"]
