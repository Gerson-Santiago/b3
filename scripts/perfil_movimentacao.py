from __future__ import annotations

import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.models.ativos import resolver_ativo_seguro


def carregar_dados():
    arquivos = list(Path("xlsx/movimentacao").glob("*.xlsx"))
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo encontrado em xlsx/movimentacao/*.xlsx")
    dfs = [read_movimentacao_file(p) for p in arquivos]
    df = pd.concat(dfs, ignore_index=True)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df = df.sort_values("data", kind="mergesort").reset_index(drop=True)
    return df


def item_1_pares_movimentacao(df: pd.DataFrame):
    print("=" * 80)
    print("ITEM 1 — PARES (MOVIMENTACAO, ENTRADA_SAIDA)")
    print("=" * 80)

    # Identificar coluna de preco unitario
    col_pu = None
    for c in ["preco_unitario", "preco", "preco_medio", "valor_unitario"]:
        if c in df.columns:
            col_pu = c
            break

    total_linhas = len(df)
    grupos = []
    for (mov, es), g in df.groupby(["movimentacao", "entrada_saida"], dropna=False):
        n = len(g)
        pct_n = (n / total_linhas) * 100
        
        # Nulos de valor_operacao
        val_null = g["valor_operacao"].isna() if "valor_operacao" in g.columns else pd.Series([True] * n)
        pct_val_null = (val_null.sum() / n) * 100

        # Nulos de preco unitario
        if col_pu and col_pu in g.columns:
            pu_null = g[col_pu].isna() | (g[col_pu] == 0)
            pct_pu_null = (pu_null.sum() / n) * 100
        else:
            pct_pu_null = 100.0

        # Exemplo real (primeira linha)
        ex = g.iloc[0]
        dt_str = ex["data"].strftime("%Y-%m-%d") if pd.notna(ex.get("data")) else "N/A"
        prod_str = str(ex.get("produto", ""))[:30]
        qtd_str = str(ex.get("quantidade", ""))
        val_str = str(ex.get("valor_operacao", ""))

        grupos.append({
            "movimentacao": str(mov),
            "entrada_saida": str(es),
            "qtd": n,
            "%_total": f"{pct_n:.1f}%",
            "%_val_null": f"{pct_val_null:.1f}%",
            "%_pu_null": f"{pct_pu_null:.1f}%",
            "exemplo": f"[{dt_str}] {prod_str} | qtd={qtd_str} | val={val_str}"
        })

    res_df = pd.DataFrame(grupos).sort_values("qtd", ascending=False)
    print(res_df.to_string(index=False))
    print()


def item_2_semantica_quantidade(df: pd.DataFrame):
    print("=" * 80)
    print("ITEM 2 — SEMANTICA DA QUANTIDADE POR TIPO (DESDOBRO, GRUPAMENTO, ATUALIZACAO, AMORTIZACAO, TRANSFERENCIA)")
    print("=" * 80)

    # Rastrear o saldo cronologico antes de cada linha por produto
    base = df.copy()
    base["_ativo"] = base["produto"].map(lambda p: resolver_ativo_seguro(p).codigo)

    import unicodedata

    def _norm(txt):
        t = unicodedata.normalize("NFKD", str(txt or "")).encode("ascii", "ignore").decode("ascii")
        return t.lower().strip()

    tipos_foco = ["desdobro", "grupamento", "atualizacao", "amortizacao", "transferencia"]

    # Classificacao linha a linha
    registros = []
    for ativo, g in base.groupby("_ativo", sort=False):
        saldo_corrido = 0.0
        for idx, row in g.iterrows():
            mov_raw = str(row.get("movimentacao") or "")
            mov = _norm(mov_raw)
            es = _norm(row.get("entrada_saida"))
            qtd = float(row.get("quantidade") or 0.0)

            # Verifica se pertence aos tipos_foco
            matched_tipo = None
            for tf in tipos_foco:
                if tf in mov:
                    matched_tipo = tf
                    break

            if matched_tipo:
                # Classificar relacao da qtd com saldo_corrido
                # delta: se saldo anterior != 0 e qtd != saldo anterior
                # snapshot: se qtd == saldo anterior
                # total: se qtd == novo saldo (quando faz sentido)
                diff_snap = abs(qtd - saldo_corrido)
                is_snap = diff_snap < 1e-4 and saldo_corrido > 0
                
                dt_str = row["data"].strftime("%Y-%m-%d") if pd.notna(row.get("data")) else "N/A"
                registros.append({
                    "data": dt_str,
                    "ativo": ativo,
                    "movimentacao": row.get("movimentacao"),
                    "entrada_saida": es,
                    "qtd_evento": qtd,
                    "saldo_anterior": saldo_corrido,
                    "is_igual_saldo_ant (snapshot)": is_snap,
                    "produto_original": str(row.get("produto"))[:35]
                })

            # Atualizar saldo corrido simples por sinal de entrada/saida para simular compra/venda/transferencia
            if es in ["credito", "crédito"]:
                saldo_corrido += qtd
            elif es in ["debito", "débito"]:
                saldo_corrido -= qtd

    foco_df = pd.DataFrame(registros)
    if not foco_df.empty:
        print(foco_df.to_string(index=False))
    else:
        print("Nenhum evento encontrado para os tipos especificados.")
    print()


def item_3_identidade(df: pd.DataFrame):
    print("=" * 80)
    print("ITEM 3 — IDENTIDADE DOS ATIVOS, NOMES, TESOURO E COLISOES")
    print("=" * 80)

    produtos_distintos = sorted(df["produto"].dropna().unique().tolist())
    print(f"Total de valores distintos de 'produto': {len(produtos_distintos)}")
    print("Lista completa de produtos distintos:")
    for p in produtos_distintos:
        print(f"  - {p}")
    print()

    print("--- Nomes diferentes por AtivoId ---")
    mapa_ticker_nomes = {}
    for p in produtos_distintos:
        t = resolver_ativo_seguro(p).codigo
        if not t:
            t = "SEM_ATIVO"
        mapa_ticker_nomes.setdefault(t, set()).add(p)

    for t, nomes in sorted(mapa_ticker_nomes.items()):
        if len(nomes) > 1:
            print(f"Ativo [{t}] agrupa {len(nomes)} nomes:")
            for n in sorted(nomes):
                print(f"    * {n}")
        else:
            print(f"Ativo [{t}]: {list(nomes)[0]}")
    print()

    print("--- Titulos do Tesouro com Nome e Vencimento Extraidos ---")
    tesouro_prods = [p for p in produtos_distintos if "tesouro" in p.lower()]
    for tp in tesouro_prods:
        m = re.search(r"(\d{4})", tp)
        venc = m.group(1) if m else "N/A"
        aid = resolver_ativo_seguro(tp)
        print(f"Produto: '{tp}' | AtivoId gerado: '{aid}' | Vencimento extraido: '{venc}'")
    print()

    print("--- Colisoes onde resolver_ativo() junta titulos diferentes ---")
    colisoes = {t: nomes for t, nomes in mapa_ticker_nomes.items() if len(nomes) > 1 and t != "SEM_ATIVO"}
    if colisoes:
        for t, nomes in colisoes.items():
            print(f"COLISAO DETECTADA: Ativo '{t}' unifica os seguintes produtos:")
            for n in nomes:
                print(f"    -> {n}")
    else:
        print("Nenhuma colisao detectada onde resolver_ativo() junte titulos diferentes indevidamente.")
    print()


def item_4_datas(df: pd.DataFrame):
    print("=" * 80)
    print("ITEM 4 — DATAS (FAIXA POR TIPO, DATAS INVALIDAS E MULTIPLOS EVENTOS NO MESMO DIA)")
    print("=" * 80)

    # Datas invalidas
    invalidas = df[df["data"].isna()]
    print(f"Contagem de datas invalidas/nulas: {len(invalidas)}")
    print()

    # Faixa por tipo
    print("--- Faixa de Datas por Tipo de Movimentacao ---")
    faixas = []
    for mov, g in df.groupby("movimentacao"):
        validas = g["data"].dropna()
        if not validas.empty:
            faixas.append({
                "movimentacao": mov,
                "data_min": validas.min().strftime("%Y-%m-%d"),
                "data_max": validas.max().strftime("%Y-%m-%d"),
                "total_linhas": len(g)
            })
    print(pd.DataFrame(faixas).to_string(index=False))
    print()

    # Dias com mais de um evento no mesmo ativo
    print("--- Dias com Mais de Um Evento no Mesmo Ativo ---")
    base = df.copy()
    base["_ativo"] = base["produto"].map(lambda p: resolver_ativo_seguro(p).codigo)
    base["_dt"] = base["data"].dt.strftime("%Y-%m-%d")

    dups = base.groupby(["_ativo", "_dt"]).filter(lambda g: len(g) > 1)
    if not dups.empty:
        res_dups = []
        for (ativo, dt), g in dups.groupby(["_ativo", "_dt"]):
            tipos = g["movimentacao"].tolist()
            res_dups.append({
                "ativo": ativo,
                "data": dt,
                "qtd_eventos": len(g),
                "tipos_no_dia": ", ".join(tipos)
            })
        print(pd.DataFrame(res_dups).to_string(index=False))
    else:
        print("Nenhum dia com multiplos eventos para o mesmo ativo.")
    print()


def item_5_linhas_identicas(df: pd.DataFrame):
    print("=" * 80)
    print("ITEM 5 — LINHAS IDENTICAS EM TODOS OS CAMPOS")
    print("=" * 80)
    duplicadas = df.duplicated(keep=False)
    n_dups = duplicadas.sum()
    print(f"Total de linhas duplicadas (identicas em todas as colunas): {n_dups}")
    if n_dups > 0:
        print("Exemplos de linhas duplicadas:")
        print(df[duplicadas].head(10).to_string())
    print()


def item_6_amortizacao_resgate_e_itsa4_2025(df: pd.DataFrame):
    print("=" * 80)
    print("ITEM 6 — TODAS AS LINHAS DE AMORTIZACAO/RESGATE E TODAS DE ITSA4 (>= 2025)")
    print("=" * 80)

    # Amortizacao e Resgate
    mask_ar = df["movimentacao"].astype(str).str.lower().str.contains("amortiz|resgate")
    df_ar = df[mask_ar].copy()
    print("--- Linhas de Amortizacao e Resgate ---")
    if not df_ar.empty:
        colunas_exibir = [c for c in ["data", "produto", "movimentacao", "entrada_saida", "quantidade", "preco_unitario", "valor_operacao"] if c in df_ar.columns]
        df_ar_exibir = df_ar[colunas_exibir].copy()
        df_ar_exibir["data"] = df_ar_exibir["data"].dt.strftime("%Y-%m-%d")
        print(df_ar_exibir.to_string(index=False))
    else:
        print("Nenhuma linha de amortizacao ou resgate encontrada.")
    print()

    # ITSA4 >= 2025
    mask_itsa = df["produto"].astype(str).str.contains("ITSA", case=False, na=False) & (df["data"] >= pd.Timestamp("2025-01-01"))
    df_itsa = df[mask_itsa].copy()
    print("--- Linhas de ITSA4 de 2025 em Diante ---")
    if not df_itsa.empty:
        colunas_exibir = [c for c in ["data", "produto", "movimentacao", "entrada_saida", "quantidade", "preco_unitario", "valor_operacao"] if c in df_itsa.columns]
        df_itsa_exibir = df_itsa[colunas_exibir].copy()
        df_itsa_exibir["data"] = df_itsa_exibir["data"].dt.strftime("%Y-%m-%d")
        print(df_itsa_exibir.to_string(index=False))
    else:
        print("Nenhuma linha de ITSA4 encontrada de 2025 em diante.")
    print()


def main():
    df = carregar_dados()
    item_1_pares_movimentacao(df)
    item_2_semantica_quantidade(df)
    item_3_identidade(df)
    item_4_datas(df)
    item_5_linhas_identicas(df)
    item_6_amortizacao_resgate_e_itsa4_2025(df)


if __name__ == "__main__":
    main()
