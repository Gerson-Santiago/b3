# Issue 4.5 — Gráfico Donut de Alocação Macro & Risco

**Fase:** 4 — Novos Gráficos, Alocação Macro & Identidade Visual  
**Status:** ✅ Concluído  
**Commit:** `5f10e31`  

---

## Por que esta tarefa é valiosa?

A proporção macro da carteira (Bolsa de Valores vs Tesouro Direto) era exibida através de uma barra de progresso linear simples (`st.progress`). Substituir a barra por um gráfico donut padronizado ao lado dos cards de métricas cria um visual moderno, alinhado e equilibrado, destacando o percentual de cada grupo e o patrimônio total consolidado no centro da rosquinha.

---

## Critérios de Aceite (Definition of Done)

- [x] Função `pie_macro_alocacao(resumo, height)` em `charts/pie.py` reaproveitando a fábrica interna `_criar_donut()`.
- [x] Suporte a sequência de cores customizadas em `_criar_donut()` via parâmetro `cores`.
- [x] Constantes `HEIGHT_DONUT_MACRO`, `COLOR_BOLSA`, `COLOR_TESOURO` e `MACRO_COLOR_SEQUENCE` em `charts/defaults.py`.
- [x] Layout balanceado em duas colunas `[3, 2]` na seção "Alocação Macro & Risco" em `views/carteira.py`: cards de métricas à esquerda e donut à direita.
- [x] Testes unitários para `pie_macro_alocacao` em `tests/test_charts_pie.py` e para a view em `tests/test_views_carteira.py`.

---

## Checklist de Ações

- [x] Estender `_criar_donut()` para aceitar lista de cores customizadas.
- [x] Implementar `pie_macro_alocacao()` em `dashboard/charts/pie.py` e exportar em `charts/__init__.py`.
- [x] Refatorar `_render_alocacao_macro()` em `dashboard/views/carteira.py` isolando `_render_cards_macro()`.
- [x] Criar suíte de testes `TestPieMacroAlocacao` em `tests/test_charts_pie.py`.
