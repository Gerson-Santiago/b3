# Issue 4.4 — Ranking de Ativos em Barras & Agrupamento Donut ("Outros")

**Fase:** 4 — Novos Gráficos, Alocação Macro & Identidade Visual  
**Status:** ✅ Concluído  
**Commit:** `777e27d`  

---

## Por que esta tarefa é valiosa?

Em carteiras com muitos ativos, o gráfico donut tradicional fica poluído e ilegível com dezenas de fatias minúsculas e sobreposição de rótulos. Agrupar posições pequenas (< 3%) em uma fatia consolidada "Outros" restaura a clareza visual. Adicionalmente, fornecer uma visualização alternativa de ranking horizontal em barras permite comparar instantaneamente o peso de cada ativo individual na carteira.

---

## Critérios de Aceite (Definition of Done)

- [x] Função pura `agrupar_posicao_outros(df, ...)` em `charts/pie.py` agrupando fatias abaixo de limiar percentual.
- [x] Função `bar_distribuicao_ativos(pos)` em `charts/bars.py` criando ranking horizontal por valor absoluto e percentual.
- [x] Controles interativos em `views/carteira.py`: seletor de tipo de gráfico (Pizza/Donut, Barras, Treemap, Sunburst) e toggle para agrupamento "Outros".
- [x] Testes unitários cobrindo o agrupamento em `tests/test_charts_pie.py` e o gráfico de barras em `tests/test_charts_bars.py`.

---

## Checklist de Ações

- [x] Criar `agrupar_posicao_outros` em `dashboard/charts/pie.py`.
- [x] Criar `bar_distribuicao_ativos` em `dashboard/charts/bars.py` e exportar em `charts/__init__.py`.
- [x] Adicionar opções no expander de Raio-X Detalhado em `dashboard/views/carteira.py`.
- [x] Cobrir com testes em `tests/test_charts_pie.py` e `tests/test_charts_bars.py`.
