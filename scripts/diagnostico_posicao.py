import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.loaders.movimentacao import read_movimentacao_file
from dashboard.loaders.posicao import read_posicao_file
from dashboard.metrics.preco_medio import compute_preco_medio


def normalizar_produto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    if " - " in texto:
        texto = texto.split(" - ", 1)[0]
    return texto.strip().upper()


mov = read_movimentacao_file(sorted(Path("xlsx/movimentacao").glob("*.xlsx"))[-1])
pos = read_posicao_file(sorted(Path("xlsx/posicao").glob("*.xlsx"))[-1])

metricas = compute_preco_medio(mov).copy()
metricas["produto_norm"] = metricas["produto"].map(normalizar_produto)

pos_agg = (
    pos.assign(produto_norm=pos["produto"].map(normalizar_produto))
    .groupby("produto_norm", as_index=False)["quantidade"]
    .sum()
    .rename(columns={"quantidade": "quantidade_posicao"})
)

produtos = ["B3SA3", "PETR4", "VALE3", "CPFE3", "MSFT34", "ROXO34", "GOGL35"]
resumo = []
for codigo in produtos:
    item = metricas[metricas["produto_norm"] == codigo]
    pos_item = pos_agg[pos_agg["produto_norm"] == codigo]
    if item.empty:
        continue
    linha = item.iloc[0].to_dict()
    linha["quantidade_codigo"] = linha.get("quantidade", 0.0)
    linha["quantidade_posicao"] = pos_item["quantidade_posicao"].iloc[0] if not pos_item.empty else None
    linha["produto"] = codigo
    resumo.append(linha)

for linha in resumo:
    print(
        f"{linha['produto']}: quantidade_codigo={linha['quantidade_codigo']}, "
        f"preco_medio={linha.get('preco_medio')}, "
        f"quantidade_posicao={linha['quantidade_posicao']}"
    )

print("\n--- posição atual ---")
print(pos[["produto", "quantidade"]].head(20).to_string(index=False))
