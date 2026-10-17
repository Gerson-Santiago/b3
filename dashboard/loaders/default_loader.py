"""Carregamento padrão de arquivos do Dashboard B3.

Responsabilidade única: localizar o arquivo mais recente no disco para um
dado tipo de dado (movimentação, posição) e retornar o DataFrame lido.

Não depende de Streamlit — erros são levantados como exceptions puras,
permitindo teste unitário sem mocks de UI.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from dashboard.utils import find_latest


def load_default(
    tipo: str,
    reader: Callable[[Path], pd.DataFrame],
    search_dirs: list[tuple[Path, str]],
) -> pd.DataFrame:
    """Localiza o arquivo mais recente e retorna o DataFrame lido.

    Parameters
    ----------
    tipo:
        Nome do tipo de dado (ex.: ``"movimentacao"``, ``"posicao"``).
        Usado apenas nas mensagens de erro.
    reader:
        Callable que recebe um ``Path`` e retorna um ``pd.DataFrame``.
        Exemplos: ``read_movimentacao_file``, ``read_posicao_file``.
    search_dirs:
        Lista de ``(diretório, prefixo)`` onde procurar, em ordem de prioridade.
        O primeiro diretório que contiver um arquivo válido é usado.

    Raises
    ------
    FileNotFoundError
        Se nenhum arquivo for encontrado em nenhum dos diretórios.
    Exception
        Qualquer exceção lançada por *reader* é propagada sem alteração.
    """
    for folder, prefix in search_dirs:
        path = find_latest(folder, prefix)
        if path is None:
            continue
        # Propaga exceções do reader diretamente (sem captura silenciosa)
        return reader(path)

    raise FileNotFoundError(
        f"Nenhum arquivo de {tipo} encontrado nos diretórios: "
        + ", ".join(str(d) for d, _ in search_dirs)
    )
