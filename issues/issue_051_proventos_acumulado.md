# Issue 5.1 — Adicionar Linha de Acumulado Anual ao `bar_proventos()`

**Fase:** 5 — Calendário de Proventos e Fluxo de Caixa
**Status:** ⏳ Backlog
**Estimativa:** 3–4 horas
**Dependência:** Fase 2 ✅ + Fase 3 ✅

---

## Por que esta tarefa é valiosa?

O gráfico atual `bar_proventos()` mostra colunas mensais isoladas. Sem uma linha de acumulado, é impossível responder visualmente à **Pergunta 4** ("Qual é a tendência da minha renda passiva?"). A linha de acumulado anual transforma colunas estáticas em uma curva de crescimento, permitindo comparar o ano atual com o anterior no mesmo gráfico.

---

## Critérios de Aceite (Definition of Done)

- [ ] `bar_proventos()` aceita parâmetro opcional `mostrar_acumulado: bool = True`.
- [ ] Quando `True`, adiciona trace de linha com o acumulado mensal do ano corrente em eixo Y secundário (ou sobreposto).
- [ ] A linha de acumulado usa `go.Scatter` com `mode="lines+markers"` e cor `COLOR_PATRIMONIO`.
- [ ] Quando `False`, comportamento idêntico ao atual (compatibilidade retroativa total).
- [ ] Testes existentes em `test_charts_bars.py` continuam passando.
- [ ] Novo teste cobre: `mostrar_acumulado=True` → `len(fig.data) == 2`.

---

## Checklist de Ações

- [ ] Calcular coluna `acumulado_ano` dentro de `bar_proventos()`: `df.groupby(ano)["valor_liquido"].cumsum()`.
- [ ] Adicionar `go.Scatter(...)` como segunda trace ao gráfico quando `mostrar_acumulado=True`.
- [ ] Atualizar a chamada em `views/proventos.py` se necessário.
- [ ] Executar `pytest tests/test_charts_bars.py -v` → todos passando.

---

## Definição de "Testável"

```
pytest tests/test_charts_bars.py -v
# → PASSED
# Dashboard: gráfico de proventos com a linha de acumulado visível sobre as barras.
```
