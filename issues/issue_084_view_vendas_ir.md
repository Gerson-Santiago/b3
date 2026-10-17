# Issue 8.4 — View "Vendas & IR" no Dashboard (`views/vendas.py`)

**Fase:** 8 — Vendas, Lucro Realizado e IR
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Dependência:** Issue 8.1 ✅ + Issue 8.2 ✅ + Issue 8.3 ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (teste de fumaça de renderização) → **2. Isole a Verdade (SSoT)** (receber dados calculados via `DashboardState`) → **3. Elimine a Duplicação (DRY)** (reutilizar cards de métricas e tabelas com `column_config`) → **4. Divida (SRP)** (view exclusivamente responsável por layout e apresentação).

---

## Por que esta tarefa é valiosa?

Toda a infraestrutura de apuração de vendas e cálculo de IR precisa ser apresentada de forma simples e intuitiva para o investidor. Ter uma aba dedicada com cards de "Total Realizado no Ano", "IR a Pagar no Mês", "Prejuízos a Compensar" e a relação completa de vendas mensais elimina qualquer dúvida na hora de emitir o DARF ou declarar o imposto de renda anual.

---

## Critérios de Aceite (Definition of Done)

- [ ] Criação do módulo `dashboard/views/vendas.py` com função `render(state: DashboardState)`.
- [ ] Nova aba adicionada ao `app.py`: `["Carteira & Alocação", "Proventos & Renda", "Evolução & Aportes", "Vendas & IR", "Reconciliação B3"]`.
- [ ] Seções da aba:
  1. **Cards de Resumo:** Lucro Realizado no Ano, Vendas no Mês Vigente (com termômetro até R$ 20k), Saldo de Prejuízos Acumulados, IR Estimado do Mês.
  2. **Apuração Mensal de IR:** Tabela com status de isenção, base de cálculo e DARF devido.
  3. **Histórico Detalhado de Vendas:** Tabela ordenável com preço médio, preço de venda e resultado de cada operação.
- [ ] Teste de renderização sem erros.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Adicionar teste de renderização da view com estado contendo vendas e estado sem vendas.

### 2. Isole a Verdade (SSoT)
- [ ] Adicionar `vendas_df` e `apuracao_ir` nos atributos do `DashboardState` via `state_pipeline`.

### 3. Elimine a Duplicação (DRY)
- [ ] Usar formatação de moedas e cores verde/vermelho já consolidadas no dashboard.

### 4. Divida (SRP)
- [ ] Manter todo o código de layout em `views/vendas.py`.

---

## Definição de "Testável"

```bash
pytest tests/test_state.py -v
# → PASSED
# Nova aba "Vendas & IR" renderizada no Streamlit
```
