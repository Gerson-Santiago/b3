# Issue 9.3 — View de Gestão de Risco e Cockpit de Sinais (`views/risco.py`)

**Fase:** 9 — Risco e Sinais de Venda
**Status:** ⏳ Backlog
**Estimativa:** 3–4 horas
**Dependência:** Issue 9.1 ✅ + Issue 9.2 ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de renderização da view) → **2. Isole a Verdade (SSoT)** (view consome apenas saídas de `metrics/risco.py` e `metrics/sinais.py`) → **3. Elimine a Duplicação (DRY)** (reutilizar visualizadores de alerta e cores semafóricas) → **4. Divida (SRP)** (view isolada focada em suporte à decisão do investidor).

---

## Por que esta tarefa é valiosa?

Transforma o dashboard de um visualizador passivo de dados em um verdadeiro **Cockpit de Decisão**. Apresenta de forma imediata onde estão os pontos de vulnerabilidade da carteira (concentração excessiva) e os ativos que acionaram gatilhos de realização de lucros ou rebalanceamento.

---

## Critérios de Aceite (Definition of Done)

- [ ] Criação de `dashboard/views/risco.py` com função `render(state: DashboardState)`.
- [ ] Incorporação na navegação do dashboard (como aba `"Gestão de Risco & Sinais"` ou seção destacada).
- [ ] Elementos visuais:
  - **Cards de Risco:** Concentração Top 5 (%), Exposição Internacional/Dólar (%), Nível de Diversificação (HHI).
  - **Tabela de Alertas de Rebalanceamento:** Semáforo visual 🟢🟡🔴 ordenável por urgência do sinal.
  - **Gráfico de Concentração:** Barras horizontais dos 5 maiores ativos em relação ao total da carteira.
- [ ] Teste unitário de smoke test garantindo renderização sem falhas.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Adicionar teste de renderização da view em `tests/test_views.py`.

### 2. Isole a Verdade (SSoT)
- [ ] Obter sinais e riscos calculados diretamente de `state.risco` e `state.sinais`.

### 3. Elimine a Duplicação (DRY)
- [ ] Usar formatações e componentes visuais comuns do dashboard.

### 4. Divida (SRP)
- [ ] Manter todo o código visual concentrado em `views/risco.py`.

---

## Definição de "Testável"

```bash
pytest tests/ -k "risco" -v
# → PASSED
# Interface exibe cockpit com semáforo de sinais e indicadores de concentração
```
