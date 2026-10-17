# Issue 2.4 — Testes Unitários para `charts/base.py`

**Fase:** 2 — Proteção
**Status:** ⏳ Backlog
**Estimativa:** 1–2 horas
**Arquivo de teste a criar:** `tests/test_charts_base.py`

---

## Por que esta tarefa é valiosa?

`base.py` contém `aplicar_layout_padrao()` — a função que **todos os outros gráficos chamam**. É o núcleo do design system visual (altura, margens, legenda, fonte, separadores). Qualquer bug aqui afeta 100% dos gráficos. Por ser pequena e independente, esta é a issue de **menor risco e maior retorno de segurança** da Fase 2.

---

## Critérios de Aceite (Definition of Done)

- [ ] Arquivo `tests/test_charts_base.py` criado.
- [ ] `pytest tests/test_charts_base.py` passa com `0 erros`.
- [ ] Todos os cenários abaixo cobertos.

---

## Checklist de Ações

### `aplicar_layout_padrao(fig, *, altura, legenda_horizontal, margens)`

- [ ] **Altura padrão:** Sem passar `altura` → `fig.layout.height == 400`.
- [ ] **Altura customizada:** `altura=600` → `fig.layout.height == 600`.
- [ ] **Separadores PT-BR:** `fig.layout.separators == ",."`.
- [ ] **Fonte base:** `fig.layout.font.family` contém `"Arial"`.
- [ ] **Legenda horizontal = True:** `fig.layout.legend.orientation == "h"`.
- [ ] **Legenda horizontal = False:** `fig.layout.legend` não define `orientation == "h"` (ou legend é `None`/não configurada).
- [ ] **Margens customizadas:** Passando `margens=dict(l=0, r=0, t=0, b=0)` → `fig.layout.margin.l == 0`.
- [ ] **Retorna a própria figura:** A função retorna o mesmo objeto `fig` passado.

---

## Contexto do Código

```python
# dashboard/charts/base.py — função alvo
def aplicar_layout_padrao(
    fig: go.Figure,
    *,
    altura: int = 400,
    legenda_horizontal: bool = True,
    margens: dict | None = None,
) -> go.Figure: ...
```

---

## Definição de "Testável"

O teste deu certo quando:
```
pytest tests/test_charts_base.py -v
# → PASSED (todos os casos acima verdes)
```

> **Bônus:** Execute `pytest tests/test_charts_base.py tests/test_treemap.py -v` para garantir que
> as mudanças em `base.py` não quebram os testes de treemap existentes.
