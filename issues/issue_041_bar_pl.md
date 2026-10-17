# Issue 4.1 — Criar `bar_lucro_prejuizo()` e Integrar na View `carteira.py`

**Fase:** 4 — Novos Gráficos
**Status:** ⏳ Backlog
**Estimativa:** 4–6 horas
**Dependência:** Fase 2 ✅ + Fase 3 ✅

---

## Por que esta tarefa é valiosa?

Este é o **maior gap atual do dashboard** em relação às 4 perguntas do investidor. A **Pergunta 2** ("Quais ativos estão gerando lucro ou prejuízo?") não tem nenhuma resposta visual. Os dados de `pl` e `variacao_pct` já são calculados em `state_pipeline.py` (`enriquecer_pos_cards()`) mas nunca são exibidos num gráfico. Esta issue fecha essa lacuna com um único gráfico de alto impacto: barras horizontais com cores positivo/negativo.

---

## Critérios de Aceite (Definition of Done)

- [ ] Função `bar_lucro_prejuizo(pos_cards)` criada em `charts/bars.py`.
- [ ] Gráfico de barras **horizontais** com `produto` no eixo Y e `pl` (R$) no eixo X.
- [ ] Barras verdes para `pl > 0`, vermelhas para `pl < 0`.
- [ ] Hover mostra: `Ativo`, `P&L (R$)`, `Variação (%)`.
- [ ] Integrado na view `views/carteira.py` como uma nova seção `"Resultado por Ativo (P&L)"`.
- [ ] Teste unitário em `tests/test_charts_bars.py` cobre o novo gráfico (cenário feliz + DataFrame vazio).
- [ ] `pytest tests/` passa com `0 erros`.

---

## Checklist de Ações

### 1. Função em `charts/bars.py`

- [ ] Criar `bar_lucro_prejuizo(pos_cards: pd.DataFrame) -> go.Figure`.
- [ ] Usar `px.bar(..., orientation="h")` com `pos_cards` filtrado para `custo_total > 0` (ativos com custo conhecido).
- [ ] Definir `color_discrete_map` ou `color` baseado no sinal de `pl`.
- [ ] Adicionar constante de cor em `charts/defaults.py`: `COLOR_LUCRO = "#10b981"` e `COLOR_PREJUIZO = "#ef4444"`.
- [ ] Chamar `aplicar_layout_padrao(fig, altura=HEIGHT_BAR, legenda_horizontal=False)`.

### 2. Integração em `views/carteira.py`

- [ ] Importar `bar_lucro_prejuizo` de `dashboard.charts`.
- [ ] Adicionar seção `"### Resultado por Ativo (P&L)"` entre o gráfico de alocação e a grade de cards.
- [ ] Só renderizar se `state.pos_cards` tiver algum `custo_total > 0`.

### 3. Exportar no `charts/__init__.py`

- [ ] Adicionar `bar_lucro_prejuizo` em `__all__`.

### 4. Teste unitário

- [ ] Adicionar ao `tests/test_charts_bars.py` (Issue 2.1):
  - Cenário feliz: DataFrame com `produto`, `pl`, `variacao_pct`, `custo_total` → `go.Figure` válido.
  - DataFrame com todos `pl=0` / `custo_total=0` → não lança exceção.

---

## Contexto — Dados Disponíveis

```python
# state_pipeline.py — enriquecer_pos_cards() já produz:
cards["pl"] = (cards["valor_abs"] - cards["custo_total"]).round(2)
cards["variacao_pct"] = round((pl / custo_total) * 100, 2) if custo_total else 0.0
```

Os dados existem. Falta apenas o gráfico.

---

## Definição de "Testável"

```
pytest tests/test_charts_bars.py -v
pytest tests/test_state.py -v          # garantir que pos_cards não quebrou
# → PASSED
# Dashboard abre e exibe o novo gráfico de P&L na aba Carteira & Alocação
```
