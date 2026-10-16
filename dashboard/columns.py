import unicodedata

ALIASES_MOV = {
    "entrada_saida": [
        "entrada/saída",
        "entrada_saida",
        "entrada saida",
        "tipo",
        "tipo de evento",
        "tipo evento",
    ],
    "data": ["data", "data de pagamento", "pagamento", "date"],
    "movimentacao": [
        "movimentação",
        "movimentacao",
        "movimento",
        "tipo de movimentação",
        "tipo movimentacao",
    ],
    "produto": ["produto", "ativo", "papel", "nome do ativo", "titulo", "título"],
    "instituicao": [
        "instituição",
        "instituicao",
        "instituição corretora",
        "instituicao corretora",
        "corretora",
    ],
    "quantidade": ["quantidade", "qtd"],
    "preco_unitario": [
        "preço unitário",
        "preco unitario",
        "preço unitario",
        "valor unitario",
    ],
    "valor_operacao": [
        "valor da operação",
        "valor da operacao",
        "valor total",
        "valor líquido",
        "valor liquido",
        "valor",
        "valor atualizado",
        "valor atual",
        "valor bruto",
        "valor aplicado",
    ],
    "categoria": ["categoria", "tipo de carteira", "segmento"],
}

ALIASES_POS = {
    "data_posicao": [
        "data da posição",
        "data da posicao",
        "data de referencia",
        "data de referência",
        "data do relatório",
        "data do relatorio",
        "snapshot date",
        "data posicionamento",
    ],
    "produto": ["produto", "ativo", "papel", "nome do ativo", "titulo", "título"],
    "instituicao": ["instituição", "instituicao", "corretora", "instituição corretora"],
    "conta": ["conta", "número da conta", "numero da conta"],
    "codigo_negociacao": ["código de negociação", "codigo de negociacao", "código negociação", "codigo negociacao"],
    "cnpj_empresa": ["cnpj da empresa", "cnpj empresa"],
    "codigo_isin": ["código isin / distribuição", "codigo isin / distribuicao", "isin", "codigo isin"],
    "tipo": ["tipo", "tipo do ativo"],
    "escriturador": ["escriturador"],
    "quantidade": ["quantidade", "quantidade disponível", "quantidade disponivel"],
    "quantidade_disponivel": ["quantidade disponível", "quantidade disponivel"],
    "quantidade_indisponivel": ["quantidade indisponível", "quantidade indisponivel"],
    "motivo": ["motivo"],
    "preco_fechamento": ["preço de fechamento", "preco de fechamento", "preço fechamento", "preco fechamento"],
    "valor_atualizado": ["valor atualizado", "valor atual", "valor de mercado"],
    "categoria": ["categoria", "tipo de carteira", "segmento"],
}

ALIASES = ALIASES_MOV


def _limpa(txt: str) -> str:
    txt = str(txt or "").replace("\ufeff", "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return " ".join(txt.split())


def _build_lookup(aliases):
    lookup = {}
    for canonical, labels in (aliases or {}).items():
        for label in labels:
            lookup[_limpa(label)] = canonical
    return lookup


def normaliza_colunas(df, aliases=None):
    aliases = aliases or ALIASES_MOV
    lookup = _build_lookup(aliases)
    renamed = {}
    for col in df.columns:
        key = _limpa(col)
        renamed[col] = lookup.get(key, key)
    return df.rename(columns=renamed)
