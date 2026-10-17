"""Estado acumulado de quantidade/custo por ativo ao aplicar eventos."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PosicaoAcumulada:
    quantidade: float = 0.0
    custo_total: float = 0.0

    def zerar(self) -> None:
        self.quantidade = 0.0
        self.custo_total = 0.0

    def definir_quantidade(self, qtd: float) -> None:
        self.quantidade = abs(qtd)
        if self.quantidade == 0:
            self.custo_total = 0.0

    def somar_quantidade(self, qtd: float) -> None:
        self.quantidade += abs(qtd)

    def ajustar_quantidade_assinada(self, qtd: float) -> None:
        self.quantidade += qtd
        if self.quantidade < 0:
            self.quantidade = 0.0
        if self.quantidade == 0:
            self.custo_total = 0.0

    def comprar(self, qtd: float, valor: float) -> None:
        self.quantidade += qtd
        self.custo_total += abs(valor)

    def reduzir(self, qtd_removida: float) -> None:
        if self.quantidade <= 0 or qtd_removida >= self.quantidade:
            self.zerar()
            return
        custo_unitario = self.custo_total / self.quantidade if self.quantidade else 0.0
        self.custo_total -= qtd_removida * custo_unitario
        self.quantidade -= qtd_removida

    def preco_medio(self) -> float:
        if self.quantidade > 0:
            if abs(self.custo_total) < 1e-12:
                return float("nan")
            return self.custo_total / self.quantidade
        return float("nan")
