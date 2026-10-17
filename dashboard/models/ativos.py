"""API pública de ativos: identidade, catálogo e resolução."""
from dashboard.models.catalogo import (
    CATALOGO_ATIVOS,
    anotar_ativos,
    resolver_ativo,
    resolver_ativo_seguro,
)
from dashboard.models.identidade import Ativo, AtivoDesconhecido, AtivoId, Classe
from dashboard.models.texto import normalizar_nome

__all__ = [
    "Classe",
    "AtivoDesconhecido",
    "AtivoId",
    "Ativo",
    "CATALOGO_ATIVOS",
    "normalizar_nome",
    "resolver_ativo",
    "resolver_ativo_seguro",
    "anotar_ativos",
]
