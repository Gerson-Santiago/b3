# Issue 8.2 — Agregação Mensal e Anual de Lucro Realizado

**Fase:** 8 — Vendas, Lucro Realizado e IR
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Dependência:** Issue 8.1 ✅ (lucro realizado por venda)

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de agregação temporal) → **2. Isole a Verdade (SSoT)** (base única vinda de `compute_vendas_realizadas`) → **3. Elimine a Duplicação (DRY)** (agrupamento por período padrão `groupby`) → **4. Divida (SRP)** (função dedicada a sumarização periódica).

---

## Por que esta tarefa é valiosa?

Tanto a análise de desempenho do investidor quanto a obrigação fiscal ocorrem em bases **mensais** e **anuais**. Saber quanto foi realizado de lucro ou prejuízo em cada mês permite avaliar a rentabilidade da estratégia de giro de capital e alimenta diretamente os limites de isenção de tributação.

---

## Critérios de Aceite (Definition of Done)

- [ ] Função `agregar_vendas_por_periodo(vendas_df: pd.DataFrame, freq: str = "M") -> pd.DataFrame` em `dashboard/metrics/lucro_realizado.py`.
- [ ] Retorna resumo agrupado com:
  - Período (Mês/Ano ou Ano)
  - Categoria do ativo
  - Total vendido (R$)
  - Custo total das vendas (R$)
  - Lucro/Prejuízo realizado total (R$)
  - Rentabilidade média realizada (%)
- [ ] Testes unitários cobrindo agrupamentos com meses com múltiplas vendas e meses sem vendas.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Adicionar testes em `tests/test_lucro_realizado.py` para agregações mensais e anuais.

### 2. Isole a Verdade (SSoT)
- [ ] Apenas agregar sobre a saída de `compute_vendas_realizadas()`.

### 3. Elimine a Duplicação (DRY)
- [ ] Padronizar colunas temporais no formato `YYYY-MM`.

### 4. Divida (SRP)
- [ ] Isolar funções de agregação temporal de regras fiscais específicas.

---

## Definição de "Testável"

```bash
pytest tests/test_lucro_realizado.py -k "agregar" -v
# → PASSED
```
