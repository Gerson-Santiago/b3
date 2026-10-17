# Issue 3.3 — DRY: Extrair Lógica de Vazio e Layout Compartilhado em `treemap.py`

**Fase:** 3 — SSoT & DRY
**Status:** ✅ Concluído
**Estimativa:** 1–2 horas
**Dependência:** Issue 2.1 a 2.4 ✅ + Issue 3.2 ✅

---

## Por que esta tarefa é valiosa?

`treemap_carteira()` e `sunburst_carteira()` compartilham:
1. A mesma guarda de DataFrame vazio (3 linhas idênticas).
2. A mesma chamada a `_preparar_dados_hierarquia()`.
3. O mesmo padrão de `update_traces` com `hovertemplate` idêntico.
4. A mesma chamada a `aplicar_layout_padrao(..., legenda_horizontal=False)`.

Extrair uma função interna `_figura_hierarquia_vazia(titulo, altura)` centraliza o caso de vazio e reduz a chance de as duas funções divergirem.

---

## Critérios de Aceite (Definition of Done)

- [x] Função interna `_figura_hierarquia_vazia(titulo, altura)` criada em `treemap.py`.
- [x] `treemap_carteira` e `sunburst_carteira` usam `_figura_hierarquia_vazia` no caso de DataFrame vazio/None.
- [x] As assinaturas públicas permanecem idênticas.
- [x] `pytest tests/test_treemap.py -v` → todos os testes continuam passando.

---

## Checklist de Ações

- [x] Criar `_figura_hierarquia_vazia(titulo: str, altura: int) -> go.Figure`.
- [x] Substituir os 3 blocos de guarda duplicados por chamadas à nova função.
- [x] Verificar se o `hovertemplate` de `treemap_carteira` e `sunburst_carteira` é realmente idêntico — se sim, extrair para constante `_HOVER_HIERARQUIA`.
- [x] Executar `pytest tests/test_treemap.py -v`.

---

## Contexto — Duplicação Atual

```python
# treemap_carteira() — linhas 33-36
if pos is None or pos.empty:
    fig = go.Figure()
    fig.update_layout(title=dict(text=titulo))
    return aplicar_layout_padrao(fig, altura=HEIGHT_TREEMAP)

# sunburst_carteira() — linhas 69-72 (idêntico!)
if pos is None or pos.empty:
    fig = go.Figure()
    fig.update_layout(title=dict(text=titulo))
    return aplicar_layout_padrao(fig, altura=HEIGHT_TREEMAP)
```
