# Issue 5.4 — Ranking dos Maiores Pagadores (Top 10 por DY e por R$)

**Fase:** 5 — Calendário de Proventos e Fluxo de Caixa
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Dependência:** Issue 5.1 ✅ + `metrics/dy.py` ✅

---

## Por que esta tarefa é valiosa?

A tabela de `dy_metrics` já existe no `DashboardState`, mas é exibida sem destaque visual. O investidor que quer saber "quais são meus 5 melhores pagadores de dividendos?" precisa varrer a tabela inteira. Um ranking visual de barras horizontais com os top 10 por DY% e por R$ recebidos nos últimos 12 meses responde essa pergunta em menos de 2 segundos.

---

## Critérios de Aceite (Definition of Done)

- [ ] Gráfico de barras horizontais `bar_ranking_proventos(dy_metrics, top_n=10)` em `charts/bars.py`.
- [ ] Duas visões selecionáveis via `st.radio`: **"por Dividend Yield (%)"** e **"por R$ Recebidos (12m)"**.
- [ ] Barras ordenadas de maior para menor.
- [ ] Hover mostra: `Ativo`, `DY LTM (%)`, `Proventos 12m (R$)`, `Yield on Cost (%)`.
- [ ] Integrado em `views/proventos.py` abaixo do gráfico de barras mensais.
- [ ] Teste unitário: top_n=3 com 5 ativos → retorna figura com 3 barras.

---

## Checklist de Ações

### 1. Função em `charts/bars.py`

- [ ] Criar `bar_ranking_proventos(dy_metrics: pd.DataFrame, top_n: int = 10, ordenar_por: str = "dy_ltm_pct") -> go.Figure`.
- [ ] Validar `ordenar_por` em `{"dy_ltm_pct", "proventos_12m"}`.
- [ ] Filtrar top N com `.nlargest(top_n, ordenar_por)` e inverter para exibição horizontal.
- [ ] Aplicar `COLOR_PROVENTO` (definir em `defaults.py` se não existir).
- [ ] Chamar `aplicar_layout_padrao(fig, altura=HEIGHT_BAR)`.

### 2. Exportar em `charts/__init__.py`

- [ ] Adicionar `bar_ranking_proventos` em `__all__`.

### 3. View em `views/proventos.py`

- [ ] Adicionar seção `"### Ranking dos Maiores Pagadores"`.
- [ ] `st.radio` para escolha de métrica de ordenação.
- [ ] Só renderizar se `state.dy_metrics` não estiver vazio.

### 4. Testes

- [ ] Adicionar em `tests/test_charts_bars.py`:
  - Cenário feliz com `top_n=3` e 5 linhas → figura com 3 barras.
  - DataFrame vazio → figura vazia sem exceção.

---

## Contexto — Dados Disponíveis

```python
# state.dy_metrics já contém:
# ["ticker", "valor_atual", "custo_total", "proventos_12m", "dy_ltm_pct", "yield_on_cost_pct"]
# Nenhuma métrica nova é necessária.
```

---

## Definição de "Testável"

```
pytest tests/test_charts_bars.py -v
# → PASSED
# Dashboard: ranking visível na aba Proventos & Renda
# Radio: "por DY%" | "por R$ Recebidos"
```
