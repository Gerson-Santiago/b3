import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_file
from dashboard.metrics.reconciliacao import comparar, data_do_arquivo, quantidade_ate
from dashboard.models.ativos import resolver_ativo


def main():
    mov_files = sorted(Path("xlsx/movimentacao").glob("*.xlsx"))
    if not mov_files:
        print("Nenhum arquivo de movimentação encontrado.")
        return

    mov_path = mov_files[-1]
    mov = read_movimentacao_file(mov_path)
    print(f"Movimentação carregada: {mov_path.name} ({len(mov)} linhas)\n")

    pos_files = sorted(Path("xlsx/posicao").glob("*.xlsx"))
    todos_deltas_divergentes = []

    for pos_path in pos_files:
        data_pos = data_do_arquivo(pos_path.name)
        pos = read_posicao_file(pos_path)
        qtd_mov = quantidade_ate(mov, data_pos)
        tabela = comparar(qtd_mov, pos, mov_df=mov, data_corte=data_pos)

        tabela["data"] = data_pos
        tabela["classe"] = tabela["ativo"].map(lambda a: resolver_ativo(a).classe.value)
        tabela["status"] = tabela["delta"].apply(lambda d: "OK" if abs(d) < 1e-4 else "DIVERGE")

        colunas_exibir = ["data", "ativo", "classe", "qtd_mov", "qtd_pos", "delta", "status"]
        tabela_exibir = tabela[colunas_exibir]

        print("=" * 80)
        print(f"SNAPSHOT: {pos_path.name} (Data de Corte: {data_pos})")
        print("=" * 80)
        print(tabela_exibir.to_string(index=False))
        print()

        divergentes = tabela[tabela["status"] == "DIVERGE"]
        if not divergentes.empty:
            for _, r in divergentes.iterrows():
                todos_deltas_divergentes.append({
                    "data": data_pos,
                    "arquivo": pos_path.name,
                    "ativo": r["ativo"],
                    "classe": r["classe"],
                    "qtd_mov": r["qtd_mov"],
                    "qtd_pos": r["qtd_pos"],
                    "delta": r["delta"],
                    "observacao": r.get("observacao", ""),
                })

    print("=" * 80)
    print("RESUMO DE DELTAS DIFERENTES DE ZERO (DIVERGÊNCIAS)")
    print("=" * 80)
    if todos_deltas_divergentes:
        df_div = pd.DataFrame(todos_deltas_divergentes)
        print(df_div.to_string(index=False))
    else:
        print("Nenhuma divergência encontrada em nenhum dos snapshots.")


if __name__ == "__main__":
    main()
