import pandas as pd

from dashboard.models.eventos import efeito_movimentacao


def compute_preco_medio(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    base = df.copy()
    if "produto" not in base.columns:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    if "valor_liquido" not in base.columns:
        if "valor_operacao" not in base.columns:
            return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])
        base["valor_liquido"] = base["valor_operacao"]

    if "qtd_liquida" not in base.columns:
        if "quantidade" not in base.columns:
            return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

        if "entrada_saida" in base.columns:
            sinal = base["entrada_saida"].fillna("").astype(str).str.lower().map({"credito": 1, "crédito": 1, "debito": -1, "débito": -1}).fillna(0)
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0) * sinal
        else:
            base["qtd_liquida"] = pd.to_numeric(base["quantidade"], errors="coerce").fillna(0).clip(lower=0)

    base["qtd_liquida"] = pd.to_numeric(base["qtd_liquida"], errors="coerce").fillna(0)
    base["valor_liquido"] = pd.to_numeric(base["valor_liquido"], errors="coerce").fillna(0)

    if "data" in base.columns:
        base = base.sort_values(["produto", "data"], kind="mergesort", na_position="last")

    linhas = []
    for produto, grupo in base.groupby("produto", sort=False):
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

                if "grupamento" in texto or "agrupamento" in texto:
                    if abs(qtd_liquida) > 0:
                        quantidade_atual = abs(qtd_liquida)
                    continue

                if "desdobro" in texto or "split" in texto:
                    quantidade_atual += abs(qtd_liquida)
                    continue

                if any(token in texto for token in ["leilao", "leilão", "facao"]):
                    # Leilão de fração é venda da fração e não altera custo nem quantidade do ativo.
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

                    # Fração recebida/creditada não mexe no custo médio do ativo em si.
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
            preco_medio = custo_total / quantidade_atual
        else:
            preco_medio = 0.0

        linhas.append(
            {
                "produto": produto,
                "quantidade": quantidade_atual,
                "custo_total": custo_total,
                "preco_medio": preco_medio,
            }
        )

    if not linhas:
        return pd.DataFrame(columns=["produto", "quantidade", "custo_total", "preco_medio"])

    resumo = pd.DataFrame(linhas, columns=["produto", "quantidade", "custo_total", "preco_medio"])
    resumo = resumo.sort_values("preco_medio", ascending=False, kind="mergesort")
    return resumo.reset_index(drop=True)
