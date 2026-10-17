import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.metrics.preco_medio import compute_preco_medio


def main():
    mov_dir = ROOT / "xlsx" / "movimentacao"
    mov_files = sorted(mov_dir.glob("*.xlsx"))
    if not mov_files:
        mov_files = [ROOT / "tests" / "fixtures" / "movimentacao_7_ativos.xlsx"]

    mov_path = mov_files[-1]
    mov = read_movimentacao_file(mov_path)
    resumo = compute_preco_medio(mov)

    df_out = resumo[["produto", "quantidade", "custo_total", "preco_medio"]].copy()
    df_out = df_out.rename(columns={"produto": "ativo"})
    df_out["quantidade"] = df_out["quantidade"].round(4)
    df_out["custo_total"] = df_out["custo_total"].round(2)
    df_out["preco_medio"] = df_out["preco_medio"].round(4)
    df_out = df_out.sort_values("ativo").reset_index(drop=True)

    out_csv = ROOT / "referencia_eventos.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"Referência gerada em: {out_csv}")
    print(df_out.to_string(index=False))


if __name__ == "__main__":
    main()
