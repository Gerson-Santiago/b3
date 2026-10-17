from __future__ import annotations

import re
import unicodedata
import warnings
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EfeitoMovimentacao:
    movimentacao: str
    entrada_saida: str
    quantidade: str
    custo: str
    provento: bool = False
    status: str = "definido"


def _normalizar_texto(texto: object) -> str:
    text = unicodedata.normalize("NFKD", str(texto or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


EVENTOS: dict[tuple[str, str], EfeitoMovimentacao] = {
    ("amortizacao", "debito"): EfeitoMovimentacao("amortizacao", "debito", "subtrai", "subtrai", False, "definido"),
    ("atualizacao", "credito"): EfeitoMovimentacao("atualizacao", "credito", "ignora", "nenhum", True, "definido"),
    ("bonificacao", "credito"): EfeitoMovimentacao("bonificacao", "credito", "soma", "nenhum", False, "definido"),
    ("bonificacao em ativos", "credito"): EfeitoMovimentacao("bonificacao em ativos", "credito", "soma", "nenhum", False, "definido"),
    ("compra", "credito"): EfeitoMovimentacao("compra", "credito", "soma", "soma", False, "definido"),
    ("desdobro", "credito"): EfeitoMovimentacao("desdobro", "credito", "soma", "nenhum", False, "definido"),
    ("direito de subscricao", "credito"): EfeitoMovimentacao("direito de subscricao", "credito", "soma", "nenhum", False, "definido"),
    ("direitos de subscricao - nao exercido", "debito"): EfeitoMovimentacao("direitos de subscricao - nao exercido", "debito", "subtrai", "nenhum", False, "definido"),
    ("dividendo", "credito"): EfeitoMovimentacao("dividendo", "credito", "ignora", "ignora", True, "definido"),
    ("dividendo - cancelado", "debito"): EfeitoMovimentacao("dividendo - cancelado", "debito", "ignora", "ignora", False, "definido"),
    ("fracao em ativos", "debito"): EfeitoMovimentacao("fracao em ativos", "debito", "subtrai", "nenhum", False, "definido"),
    ("grupamento", "credito"): EfeitoMovimentacao("grupamento", "credito", "define", "nenhum", False, "definido"),
    ("juros", "credito"): EfeitoMovimentacao("juros", "credito", "ignora", "ignora", True, "definido"),
    ("juros sobre capital proprio", "credito"): EfeitoMovimentacao("juros sobre capital proprio", "credito", "ignora", "ignora", True, "definido"),
    ("leilao de fracao", "credito"): EfeitoMovimentacao("leilao de fracao", "credito", "ignora", "nenhum", False, "definido"),
    ("rendimento", "credito"): EfeitoMovimentacao("rendimento", "credito", "ignora", "ignora", True, "definido"),
    ("resgate", "debito"): EfeitoMovimentacao("resgate", "debito", "subtrai", "subtrai", False, "definido"),
    ("transferencia", "credito"): EfeitoMovimentacao("transferencia", "credito", "soma", "soma", False, "definido"),
    ("transferencia", "debito"): EfeitoMovimentacao("transferencia", "debito", "subtrai", "subtrai", False, "definido"),
    ("transferencia - liquidacao", "credito"): EfeitoMovimentacao("transferencia - liquidacao", "credito", "soma", "soma", False, "definido"),
    ("transferencia - liquidacao", "debito"): EfeitoMovimentacao("transferencia - liquidacao", "debito", "subtrai", "subtrai", False, "definido"),
    ("venda", "debito"): EfeitoMovimentacao("venda", "debito", "subtrai", "subtrai", False, "definido"),
}


def normalizar_chave_evento(movimentacao: object, entrada_saida: object) -> tuple[str, str]:
    return _normalizar_texto(movimentacao), _normalizar_texto(entrada_saida)


def efeito_movimentacao(movimentacao: object, entrada_saida: object) -> EfeitoMovimentacao:
    chave = normalizar_chave_evento(movimentacao, entrada_saida)
    efeito = EVENTOS.get(chave)
    if efeito is not None:
        return efeito

    warnings.warn(
        f"Movimentação com efeito pendente: movimentacao={movimentacao!r}, entrada_saida={entrada_saida!r}",
        RuntimeWarning,
        stacklevel=2,
    )
    return EfeitoMovimentacao(
        movimentacao=chave[0],
        entrada_saida=chave[1],
        quantidade="pendente",
        custo="pendente",
        provento=False,
        status="pendente",
    )


def listar_movimentacoes_pendentes(df) -> list[str]:
    if df is None or df.empty or "movimentacao" not in df.columns:
        return []

    pendentes = []
    seen: set[str] = set()
    for _, row in df.iterrows():
        efeito = efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida"))
        if efeito.status == "pendente":
            chave = f"{efeito.movimentacao}|{efeito.entrada_saida}"
            if chave not in seen:
                seen.add(chave)
                pendentes.append(chave)
    return sorted(pendentes)


def tem_efeito_pendente(df) -> bool:
    return bool(listar_movimentacoes_pendentes(df))
