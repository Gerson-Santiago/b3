# Issue 5.2 — Segmentar `bar_proventos()` por Tipo: Dividendos vs JCP vs FII

**Fase:** 5 — Calendário de Proventos e Fluxo de Caixa
**Status:** ✅ Concluído
**Estimativa:** 4–6 horas
**Dependência:** Issue 5.1 ✅

> ⚠️ **Nota de Negociabilidade (N do INVEST):** A coluna `tipo_provento` foi implementada
> de forma limpa em `models/movimentacao.py` (`classificar_tipo_provento`) e integrada a `metrics/proventos.py`
> (`compute_proventos`), distinguindo Dividendos, JCP, Rendimento FII e Outros.

---

## Por que esta tarefa é valiosa?

Dividendos, JCP e Rendimentos FII têm tratamentos fiscais diferentes (JCP tem IR na fonte, FII é isento para PF em certas condições). Misturar os três num único total esconde informações relevantes para decisões de alocação. Segmentar permite ao investidor ver quanto de sua renda é efetivamente isenta vs tributada.

---

## Critérios de Aceite (Definition of Done)

- [x] Verificado que os dados de proventos possuem uma coluna distinguindo o tipo (ex: `tipo` ou `movimentacao`).
- [x] `bar_proventos()` aceita parâmetro `segmentar_por_tipo: bool = False`.
- [x] Quando `True`: barras empilhadas (`barmode="stack"`) com uma cor por tipo.
- [x] Quando `False`: comportamento atual (compatibilidade retroativa).
- [x] Cores definidas em `defaults.py`: `COLOR_DIVIDENDO`, `COLOR_JCP`, `COLOR_FII`.
- [x] Testes existentes continuam passando.
- [x] Novo teste cobre: `segmentar_por_tipo=True` com dados mistos → traces separados por tipo.

---

## Checklist de Ações

### Pré-condição (antes de codificar)

- [x] Abrir `dashboard/metrics/proventos.py` e verificar se a coluna de tipo já existe.
- [x] Integrar `classificar_tipo_provento` ao pipeline de `metrics/proventos.py`.

### Implementação

- [x] Adicionar constantes de cor em `charts/defaults.py`.
- [x] Reescrever `bar_proventos()` com lógica condicional: `barmode="stack"` + uma trace por tipo.
- [x] Atualizar `views/proventos.py` para expor o novo toggle `st.toggle("Por Tipo")`.
- [x] Executar `pytest tests/test_charts_bars.py -v`.

---

## Definição de "Testável"

```
pytest tests/test_charts_bars.py -v
# → PASSED
# Dashboard: gráfico de proventos com toggle para ativar segmentação por tipo.
# Barras empilhadas mostram Dividendos (verde), JCP (âmbar) e FII (ciano).
```
