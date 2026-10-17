# Issue 7.3 — Visualização de Alocação por Corretora / Instituição

**Fase:** 7 — Posição Interativa & Alocação Estendida
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Dependência:** `charts/pie.py` ✅ + `state.pos_cards` ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de gráfico e agregação) → **2. Isole a Verdade (SSoT)** (coluna `instituicao` normalizada nos loaders) → **3. Elimine a Duplicação (DRY)** (reutilizar `_criar_donut` de `charts/pie.py`) → **4. Divida (SRP)** (nova função de gráfico em `charts/pie.py`).

---

## Por que esta tarefa é valiosa?

Muitos investidores utilizam mais de uma instituição financeira (ex.: XP, NuInvest, BTG, Itaú Corretora). O arquivo de posição da B3 já traz a coluna `instituicao`. Entender a concentração de custódia por instituição é crucial para segurança institucional e gestão de risco contra falência ou problemas operacionais de intermediários.

---

## Critérios de Aceite (Definition of Done)

- [ ] Função `pie_carteira_por_instituicao(pos_df: pd.DataFrame) -> go.Figure` em `charts/pie.py`.
- [ ] Gráfico donut mostrando a distribuição percentual do patrimônio por instituição/corretora.
- [ ] Tabela sumarizada de apoio com: `Instituição`, `Patrimônio (R$)`, `% da Carteira`, `Quantidade de Ativos`.
- [ ] Integrado no expander de Raio-X Detalhado em `views/carteira.py`.
- [ ] Teste unitário em `tests/test_charts_pie.py` validando o novo gráfico donut.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Adicionar testes em `tests/test_charts_pie.py` para `pie_carteira_por_instituicao` (dados válidos e DF vazio).

### 2. Isole a Verdade (SSoT)
- [ ] Agrupar pela coluna `instituicao` já padronizada no loader de posição.

### 3. Elimine a Duplicação (DRY)
- [ ] Usar o helper interno consolidado `_criar_donut()` de `dashboard/charts/pie.py`.

### 4. Divida (SRP)
- [ ] Expor o gráfico isoladamente e integrá-lo nas opções de visualização da carteira.

---

## Definição de "Testável"

```bash
pytest tests/test_charts_pie.py -v
# → PASSED
```
