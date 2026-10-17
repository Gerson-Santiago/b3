# Issue 8.1 — Cálculo de Lucro e Prejuízo Realizado por Venda (`metrics/lucro_realizado.py`)

**Fase:** 8 — Vendas, Lucro Realizado e IR
**Status:** ⏳ Backlog
**Estimativa:** 5–6 horas
**Dependência:** `models/pipeline_eventos.py` ✅ + `metrics/preco_medio.py` ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes com compras múltiplas e vendas parciais) → **2. Isole a Verdade (SSoT)** (custo médio ponderado calculado pela regra canônica da Receita Federal) → **3. Elimine a Duplicação (DRY)** (reutilizar `compute_preco_medio` e motor de eventos) → **4. Divida (SRP)** (módulo focado estritamente em apurar operações de liquidação de posição).

---

## Por que esta tarefa é valiosa?

Atualmente, o pipeline calcula posições acumuladas e preço médio de custódia, mas não gera o registro histórico das **vendas realizadas** com o respectivo lucro ou prejuízo apurado. Sem isso, o investidor não consegue saber se vendeu com ganho ou perda, nem possui a base obrigatória para apuração de Imposto de Renda.

O método de cálculo obrigatório pela Receita Federal é o **Preço Médio Ponderado**:
- Cada nova **compra** recalcula o preço médio ponderado do ativo: `PM = (Custo_Anterior + Custo_Nova_Compra) / (Qtd_Anterior + Qtd_Nova_Compra)`.
- A **venda** (parcial ou total) **não altera o preço médio**. Ela apenas abate quantidade e custo proporcionalmente. O lucro ou prejuízo bruto da venda é `Qtd_Vendida * (Preco_Venda - PM_no_momento_da_venda)`.

---

## Critérios de Aceite (Definition of Done)

- [ ] Módulo `dashboard/metrics/lucro_realizado.py` com função `compute_vendas_realizadas(mov_df: pd.DataFrame) -> pd.DataFrame`.
- [ ] Para cada evento de venda, o DataFrame resultante deve conter:
  - `data` da venda
  - `ativo` / `ticker`
  - `categoria` (Ação, BDR, FII, Tesouro)
  - `quantidade_vendida`
  - `preco_venda` (preço unitário praticado na venda)
  - `valor_total_venda` (`quantidade_vendida * preco_venda`)
  - `preco_medio_aquisicao` (PM ponderado imediatamente anterior à venda)
  - `custo_aquisicao` (`quantidade_vendida * preco_medio_aquisicao`)
  - `resultado_bruto` (`valor_total_venda - custo_aquisicao`)
  - `resultado_pct` (`(resultado_bruto / custo_aquisicao) * 100`)
- [ ] Vendas parciais reduzem saldo de custódia e mantêm rigorosamente o mesmo preço médio ponderado.
- [ ] Cobertura completa de testes em `tests/test_lucro_realizado.py`:
  - Múltiplas compras com preços distintos recalculando o PM.
  - Venda parcial mantendo o PM e apurando lucro/prejuízo exato.
  - Venda total zerando posição.
  - Nova compra após zerar posição estabelecendo novo PM.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar `tests/test_lucro_realizado.py` com cenários:
  - Compra 100 @ R$ 10, Compra 100 @ R$ 20 -> PM = R$ 15.
  - Venda parcial 50 @ R$ 25 -> PM continua R$ 15, Lucro = 50 * (25 - 15) = R$ 500.
  - Venda parcial 50 @ R$ 10 -> PM continua R$ 15, Prejuízo = 50 * (10 - 15) = -R$ 250.
  - Venda total das 100 restantes.

### 2. Isole a Verdade (SSoT)
- [ ] Usar os eventos de débito classificados pelo pipeline de movimentação (`is_venda`).
- [ ] O algoritmo de preço médio deve seguir estritamente a mesma regra de preço médio ponderado de `models/motor_posicao.py` / `metrics/preco_medio.py`.

### 3. Elimine a Duplicação (DRY)
- [ ] Integrar com `pipeline_eventos` para que as movimentações sejam consumidas em ordem cronológica estrita.

### 4. Divida (SRP)
- [ ] Retornar tabela limpa com o livro de vendas fechadas.

---

## Definição de "Testável"

```bash
.venv\Scripts\pytest.exe tests/test_lucro_realizado.py -v
# → PASSED
```
