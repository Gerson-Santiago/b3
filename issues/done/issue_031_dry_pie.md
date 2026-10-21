# Issue 3.1 — DRY: Extrair `_criar_donut()` em `charts/pie.py`

**Fase:** 3 — SSoT & DRY
**Status:** ✅ Concluído
**Estimativa:** 2–3 horas
**Dependência:** Issue 2.3 ✅ (testes de `pie.py` devem estar verdes)

---

## Por que esta tarefa é valiosa?

As três funções de `pie.py` são quase idênticas. A triplicação significa que qualquer ajuste visual (cor, hole, hover, textinfo) precisa ser feito em 3 lugares. Criar `_criar_donut()` centraliza o estilo em 1 local, tornando futuros ajustes seguros e instantâneos.

---

## Critérios de Aceite (Definition of Done)

- [x] Função interna `_criar_donut(df, names_col, values_col, titulo, height)` criada em `pie.py`.
- [x] `pie_carteira`, `pie_carteira_por_categoria` e `pie_categoria` delegam para `_criar_donut()`.
- [x] Todas as 3 funções públicas mantêm a mesma assinatura e comportamento externo.
- [x] `pytest tests/test_charts_pie.py` continua passando sem nenhuma modificação nos testes.

---

## Checklist de Ações

- [x] Identificar os parâmetros que variam entre as 3 funções: `names`, `values`, `titulo`, `altura`.
- [x] Criar `_criar_donut(df, names_col, values_col, titulo, height)` consolidando `px.pie(...)` + `update_traces(...)` + `aplicar_layout_padrao(...)`.
- [x] Reescrever cada função pública para chamar `_criar_donut(...)` com seus parâmetros específicos.
- [x] Executar `pytest tests/test_charts_pie.py -v` → todos devem passar.

---

## Contexto — Duplicação Atual

```python
# As 3 funções têm exatamente este padrão repetido:
fig = px.pie(df, names=..., values=..., title=..., hole=0.45, color_discrete_sequence=PIE_COLOR_SEQUENCE)
fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="...")
return aplicar_layout_padrao(fig, altura=HEIGHT_PIE_*)
```

## Contexto — Resultado Esperado

```python
# pie.py — depois da refatoração
def _criar_donut(df, names_col, values_col, titulo, height) -> go.Figure:
    fig = px.pie(df, names=names_col, values=values_col, title=titulo, hole=0.45, ...)
    fig.update_traces(...)
    return aplicar_layout_padrao(fig, altura=height)

def pie_carteira(pos):
    return _criar_donut(pos, "produto", "valor_abs", "Distribuição da Carteira por Ativo", HEIGHT_PIE)
```
