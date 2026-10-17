# Issue 9.2 — Motor de Sinais de Rebalanceamento e Realização de Lucro (`metrics/sinais.py`)

**Fase:** 9 — Risco e Sinais de Venda
**Status:** ⏳ Backlog
**Estimativa:** 4–5 horas
**Dependência:** Issue 9.1 ✅ + `metrics/dy.py` ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes com limites e gatilhos de sinais) → **2. Isole a Verdade (SSoT)** (regras de gatilho centralizadas em constantes e parâmetros configuráveis) → **3. Elimine a Duplicação (DRY)** (reutilizar métricas de rentabilidade e DY) → **4. Divida (SRP)** (motor de decisão sem dependência de UI).

---

## Por que esta tarefa é valiosa?

Um dos maiores desafios do investidor é saber a hora certa de realizar lucro ou rebalancear. A especificação define claramente os sinais comuns:
1. **Posição excedeu o peso-alvo:** Exposição cresceu além da meta de alocação de risco.
2. **DY muito abaixo da média histórica / Yield on Cost esticado:** O preço subiu tanto que a taxa de dividendo atual tornou-se pouco atrativa frente a alternativas.
3. **Rentabilidade alta sobre o PM:** Lucro expressivo acumulado pronto para realização ou proteção.

Este motor processa os dados locais da carteira e gera scores e alertas objetivos por ativo.

---

## Critérios de Aceite (Definition of Done)

- [ ] Módulo `dashboard/metrics/sinais.py` com função `gerar_sinais_rebalanceamento(pos_cards: pd.DataFrame, metas_pesos: dict | None = None) -> pd.DataFrame`.
- [ ] Retorna tabela com:
  - `ativo`
  - `peso_atual_pct`
  - `peso_alvo_pct` (configurado ou assumido proporcional)
  - `desvio_peso_pct` (`peso_atual_pct - peso_alvo_pct`)
  - `lucro_sobre_pm_pct`
  - `dy_ltm_pct`
  - `status_sinal` (`"🟢 Manter"`, `"🟡 Avaliar / Monitorar"`, `"🔴 Realizar Lucro / Rebalancear"`)
  - `motivo_sinal` (texto explicativo do gatilho ativado)
- [ ] Gatilhos padrão:
  - Desvio > +5% em relação ao peso-alvo → Sinal 🔴
  - Lucro > 100% sobre o Preço Médio → Sinal 🟡 ou 🔴
- [ ] Testes unitários em `tests/test_sinais.py` validando os disparos de cada sinal.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar `tests/test_sinais.py` cobrindo cenários onde gatilhos são ativados e onde nenhum sinal é emitido.

### 2. Isole a Verdade (SSoT)
- [ ] Definir regras de limiares em `dashboard/metrics/sinais.py`.

### 3. Elimine a Duplicação (DRY)
- [ ] Consumir dados diretamente de `pos_cards` e `dy_metrics`.

### 4. Divida (SRP)
- [ ] Retornar tabela de diagnóstico desacoplada de Streamlit.

---

## Definição de "Testável"

```bash
pytest tests/test_sinais.py -v
# → PASSED
```
