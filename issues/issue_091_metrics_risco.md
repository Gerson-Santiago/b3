# Issue 9.1 — Métricas de Concentração e Risco da Carteira (`metrics/risco.py`)

**Fase:** 9 — Risco e Sinais de Venda
**Status:** ⏳ Backlog
**Estimativa:** 3–4 horas
**Dependência:** Fase 7 ✅ (`pos_cards` enriquecido com setores e categorias)

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de métricas matemáticas de risco) → **2. Isole a Verdade (SSoT)** (cálculo de risco derivado unicamente de `pos_cards`) → **3. Elimine a Duplicação (DRY)** (reutilizar pesos percentuais consolidados) → **4. Divida (SRP)** (módulo puramente analítico de risco da carteira).

---

## Por que esta tarefa é valiosa?

O controle de risco é fundamental para evitar a ruína ou perdas irreparáveis no patrimônio. Investidores frequentemente acreditam estar diversificados quando, na verdade, os 5 maiores ativos representam mais de 70% da carteira, ou a exposição cambial/setorial está desbalanceada. Esta issue calcula métricas objetivas de risco para alimentar a tomada de decisão.

---

## Critérios de Aceite (Definition of Done)

- [ ] Módulo `dashboard/metrics/risco.py` com funções:
  - `calcular_concentracao_top5(pos_cards: pd.DataFrame) -> dict`: percentual somado dos 5 maiores ativos e lista dos ativos.
  - `calcular_exposicao_internacional(pos_cards: pd.DataFrame) -> float`: percentual alocado em BDRs / ativos dolarizados.
  - `calcular_indice_herfindahl(pos_cards: pd.DataFrame) -> float`: cálculo do Índice Herfindahl-Hirschman (HHI) para medir dispersão/concentração da carteira.
- [ ] Testes unitários em `tests/test_risco.py` cobrindo carteira concentrada (1 único ativo = 100%), carteira perfeitamente distribuída e carteira com ativos mistos.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar `tests/test_risco.py` com dados sintéticos de carteiras.

### 2. Isole a Verdade (SSoT)
- [ ] Consumir `pos_cards` garantindo que a soma dos pesos seja igual a 100%.

### 3. Elimine a Duplicação (DRY)
- [ ] Utilizar a classificação de categorias de `models/categorias.py` para identificar BDRs.

### 4. Divida (SRP)
- [ ] Manter os cálculos matemáticos em `metrics/risco.py`.

---

## Definição de "Testável"

```bash
pytest tests/test_risco.py -v
# → PASSED
```
