# Issue 6.4 — Cruzamento e Reconciliação de Proventos (`metrics/reconciliacao_proventos.py`)

**Fase:** 6 — Loader de Proventos Recebidos
**Status:** ⏳ Backlog
**Estimativa:** 4–5 horas
**Dependência:** Issue 6.3 ✅ (loader proventos) + `models/eventos.py` ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes com discrepâncias sintéticas simuladas) → **2. Isole a Verdade (SSoT)** (regras de provento em `models/eventos.py`) → **3. Elimine a Duplicação (DRY)** (reutilizar tolerâncias e helpers numéricos de reconciliação) → **4. Divida (SRP)** (separar reconciliação de quantidade da reconciliação de proventos).

---

## Por que esta tarefa é valiosa?

Atualmente, a reconciliação do dashboard audita apenas a **quantidade de ativos** em custódia (movimentações acumuladas vs posição B3). Proventos creditados na conta podem sofrer divergências (valores líquidos após IR retido em JCP, datas de pagamento retroativas ou não compensadas). Cruzar o arquivo de **Movimentação** com o arquivo de **Proventos Recebidos** garante auditoria de ponta a ponta e total integridade fiscal e financeira.

---

## Critérios de Aceite (Definition of Done)

- [ ] Função `reconciliar_proventos(mov_df: pd.DataFrame, prov_df: pd.DataFrame) -> pd.DataFrame` implementada em `dashboard/metrics/reconciliacao_proventos.py`.
- [ ] O DataFrame resultante deve conter:
  - `ativo` / `ticker`
  - `total_movimentacao` (soma de proventos creditados na movimentação)
  - `total_extrato_proventos` (soma de proventos no arquivo dedicado)
  - `delta` (`total_movimentacao - total_extrato_proventos`)
  - `status` (`"OK"` ou `"Divergente"`)
- [ ] Agrupamento flexível por ativo e por mês/ano.
- [ ] Testes unitários em `tests/test_reconciliacao_proventos.py` com cenários 100% conciliados, diferenças de centavos por arredondamento e divergências reais.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar `tests/test_reconciliacao_proventos.py` com mocks de movimentação e proventos recebidos.
- [ ] Testar cenários: matching perfeito, item faltando em um dos lados, arredondamentos.

### 2. Isole a Verdade (SSoT)
- [ ] Reutilizar a classificação de proventos via `efeito_movimentacao` de `dashboard.models.eventos`.
- [ ] Normalizar ativos usando `resolver_ativo_seguro` de `dashboard.models.ativos`.

### 3. Elimine a Duplicação (DRY)
- [ ] Reutilizar função de matching e tolerância (`delta.abs() > 0.01`) idêntica à reconciliação de posições.

### 4. Divida (SRP)
- [ ] Manter este cálculo em `dashboard/metrics/reconciliacao_proventos.py`, sem poluir `metrics/reconciliacao.py` que cuida de quantidade física de custódia.

---

## Definição de "Testável"

```bash
pytest tests/test_reconciliacao_proventos.py -v
# → PASSED
```
