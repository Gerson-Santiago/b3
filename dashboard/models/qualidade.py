from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import pandas as pd


@dataclass(frozen=True)
class Aviso:
    tipo: str
    produto: str
    detalhe: str


@dataclass
class RelatorioQualidade:
    _avisos: list[Aviso] = field(default_factory=list)

    def add(self, aviso: Aviso) -> None:
        self._avisos.append(aviso)

    @property
    def avisos(self) -> list[Aviso]:
        return list(self._avisos)

    @property
    def vazio(self) -> bool:
        return len(self._avisos) == 0

    def como_dataframe(self) -> pd.DataFrame:
        if not self._avisos:
            return pd.DataFrame(columns=["tipo", "produto", "detalhe"])
        return pd.DataFrame(
            [{"tipo": a.tipo, "produto": a.produto, "detalhe": a.detalhe} for a in self._avisos]
        )


def mensagens(relatorio: RelatorioQualidade | None) -> list[str]:
    if relatorio is None or relatorio.vazio:
        return []
    return [
        f"[{a.tipo}] {a.produto}: {a.detalhe}" if a.detalhe else f"[{a.tipo}] {a.produto}"
        for a in relatorio.avisos
    ]
