from __future__ import annotations

import re
import unicodedata
import warnings
from dataclasses import dataclass
from typing import Iterable

import pandas as pd


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
    ("atualizacao", "credito"): EfeitoMovimentacao("atualizacao", "credito", "define", "nenhum", False, "definido"),
    ("atualizacao", "debito"): EfeitoMovimentacao("atualizacao", "debito", "define", "nenhum", False, "definido"),
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


def aplicar_eventos_ordenados(df, aplicar_define: bool = True):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    base = df.copy()
    if "produto" not in base.columns:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    if "valor_liquido" not in base.columns:
        if "valor_operacao" in base.columns:
            base["valor_liquido"] = pd.to_numeric(base["valor_operacao"], errors="coerce").fillna(0.0)
        else:
            base["valor_liquido"] = 0.0

    if "qtd_liquida" not in base.columns:
        if "quantidade" not in base.columns:
            return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

        if "entrada_saida" in base.columns:
            sinal = base["entrada_saida"].fillna("").astype(str).str.lower().map({"credito": 1, "crédito": 1, "debito": -1, "débito": -1}).fillna(0)
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0) * sinal
        else:
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0).clip(lower=0)

    base["qtd_liquida"] = pd.to_numeric(base["qtd_liquida"], errors="coerce").fillna(0.0)
    base["valor_liquido"] = pd.to_numeric(base["valor_liquido"], errors="coerce").fillna(0.0)

    from dashboard.models.ativos import renomear_ativo

    base["_ativo_chave"] = base["produto"].map(lambda p: renomear_ativo(p) or str(p).strip())

    if "data" in base.columns:
        base = base.sort_values(["_ativo_chave", "data"], kind="mergesort", na_position="last")

    linhas = []
    for chave, grupo in base.groupby("_ativo_chave", sort=False):
        quantidade_atual = 0.0
        custo_total = 0.0

        for _, row in grupo.iterrows():
            movimentacao = str(row.get("movimentacao") or "").lower()
            qtd_liquida = float(row.get("qtd_liquida", 0.0) or 0.0)
            valor_liquido = float(row.get("valor_liquido", 0.0) or 0.0)
            efeito = efeito_movimentacao(row.get("movimentacao"), row.get("entrada_saida"))

            if efeito.provento or efeito.status == "pendente":
                continue
            if efeito.quantidade == "ignora":
                continue
            if abs(qtd_liquida) < 1e-9:
                continue

            if efeito.custo == "nenhum" and efeito.quantidade in {"soma", "subtrai", "define"}:
                texto = movimentacao.lower()

                if efeito.quantidade == "define":
                    if aplicar_define:
                        quantidade_atual = abs(qtd_liquida)
                        if quantidade_atual == 0:
                            custo_total = 0.0
                        continue
                    else:
                        quantidade_atual += qtd_liquida
                        if quantidade_atual < 0:
                            quantidade_atual = 0.0
                        continue

                if "grupamento" in texto or "agrupamento" in texto:
                    if abs(qtd_liquida) > 0:
                        quantidade_atual = abs(qtd_liquida)
                    continue

                if "desdobro" in texto or "split" in texto:
                    quantidade_atual += abs(qtd_liquida)
                    continue

                if any(token in texto for token in ["leilao", "leilão", "facao"]):
                    continue

                if any(token in texto for token in ["fracao", "fração", "facao"]):
                    if qtd_liquida < 0:
                        quantidade_removida = abs(qtd_liquida)
                        if quantidade_atual <= 0:
                            quantidade_atual = 0.0
                            custo_total = 0.0
                            continue

                        if quantidade_removida >= quantidade_atual:
                            quantidade_atual = 0.0
                            custo_total = 0.0
                            continue

                        custo_unitario = custo_total / quantidade_atual if quantidade_atual else 0.0
                        custo_total -= quantidade_removida * custo_unitario
                        quantidade_atual -= quantidade_removida
                        continue
                    continue

                quantidade_atual += qtd_liquida
                if quantidade_atual < 0:
                    quantidade_atual = 0.0
                if quantidade_atual == 0:
                    custo_total = 0.0
                continue

            if qtd_liquida > 0:
                quantidade_atual += qtd_liquida
                custo_total += abs(valor_liquido)
                continue

            if qtd_liquida < 0:
                quantidade_vendida = abs(qtd_liquida)
                if quantidade_atual <= 0:
                    quantidade_atual = 0.0
                    custo_total = 0.0
                    continue

                if quantidade_vendida >= quantidade_atual:
                    quantidade_atual = 0.0
                    custo_total = 0.0
                    continue

                custo_unitario = custo_total / quantidade_atual if quantidade_atual else 0.0
                custo_total -= quantidade_vendida * custo_unitario
                quantidade_atual -= quantidade_vendida

        if quantidade_atual > 0:
            if abs(custo_total) < 1e-12:
                preco_medio = float("nan")
            else:
                preco_medio = custo_total / quantidade_atual
        else:
            preco_medio = float("nan")

        linhas.append(
            {
                "produto": chave,
                "quantidade": quantidade_atual,
                "custo_total": custo_total,
                "preco_medio": preco_medio,
            }
        )

    if not linhas:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    return pd.DataFrame(linhas, columns=["produto", "quantidade", "custo_total", "preco_medio"]).reset_index(drop=True)


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
