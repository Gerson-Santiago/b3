# Issue 5.2 — Segmentar `bar_proventos()` por Tipo: Dividendos vs JCP vs FII

**Fase:** 5 — Calendário de Proventos e Fluxo de Caixa
**Status:** ⏳ Backlog
**Estimativa:** 4–6 horas
**Dependência:** Issue 5.1 ✅

> ⚠️ **Nota de Negociabilidade (N do INVEST):** Esta issue depende de a coluna `tipo_provento`
> (ou equivalente) existir nos dados brutos de proventos. Verifique antes de iniciar se `metrics/proventos.py`
> já distingue Dividendos, JCP e Rendimentos FII. Se não existir, pode ser necessário criar uma
> issue de infraestrutura antes desta.

---

## Por que esta tarefa é valiosa?

Dividendos, JCP e Rendimentos FII têm tratamentos fiscais diferentes (JCP tem IR na fonte, FII é isento para PF em certas condições). Misturar os três num único total esconde informações relevantes para decisões de alocação. Segmentar permite ao investidor ver quanto de sua renda é efetivamente isenta vs tributada.

---

## Critérios de Aceite (Definition of Done)

- [ ] Verificado que os dados de proventos possuem uma coluna distinguindo o tipo (ex: `tipo` ou `movimentacao`).
- [ ] `bar_proventos()` aceita parâmetro `segmentar_por_tipo: bool = False`.
- [ ] Quando `True`: barras empilhadas (`barmode="stack"`) com uma cor por tipo.
- [ ] Quando `False`: comportamento atual (compatibilidade retroativa).
- [ ] Cores definidas em `defaults.py`: `COLOR_DIVIDENDO`, `COLOR_JCP`, `COLOR_FII`.
- [ ] Testes existentes continuam passando.
- [ ] Novo teste cobre: `segmentar_por_tipo=True` com dados mistos → traces separados por tipo.

---

## Checklist de Ações

### Pré-condição (antes de codificar)

- [ ] Abrir `dashboard/metrics/proventos.py` e verificar se a coluna de tipo já existe.
- [ ] Se não existir: criar issue de infraestrutura separada para adicionar a coluna `tipo_provento` ao pipeline de métricas e marcar esta issue como bloqueada.

### Implementação

- [ ] Adicionar constantes de cor em `charts/defaults.py`.
- [ ] Reescrever `bar_proventos()` com lógica condicional: `barmode="relative"` + uma trace por tipo.
- [ ] Atualizar `views/proventos.py` para expor o novo toggle `st.toggle("Segmentar por tipo")`.
- [ ] Executar `pytest tests/test_charts_bars.py -v`.

---

## Definição de "Testável"

```
pytest tests/test_charts_bars.py -v
# → PASSED
# Dashboard: gráfico de proventos com toggle para ativar segmentação por tipo.
# Barras empilhadas mostram Dividendos (verde), JCP (âmbar) e FII (ciano).
```
