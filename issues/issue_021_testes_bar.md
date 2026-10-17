# Issue 2.1 — Testes Unitários para `charts/bars.py`

**Fase:** 2 — Proteção
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Arquivo de teste a criar:** `tests/test_charts_bars.py`

---

## Por que esta tarefa é valiosa?

`bars.py` produz os gráficos de `Proventos Mensais` e `Dividend Yield` — dois dos indicadores de renda do investidor (Pergunta 4). Sem testes, qualquer mudança futura na camada de métricas pode quebrar silenciosamente a visualização. Esta issue é a **rede de segurança antes de qualquer refatoração** nos gráficos.

---

## Critérios de Aceite (Definition of Done)

- [ ] Arquivo `tests/test_charts_bars.py` criado.
- [ ] `pytest tests/test_charts_bars.py` passa com `0 erros`.
- [ ] Todos os cenários abaixo cobertos por pelo menos 1 teste.

---

## Checklist de Ações

### `bar_proventos(proventos)`

- [ ] **Cenário feliz:** DataFrame com colunas `mes` e `valor_liquido` → retorna `go.Figure` válido (`len(fig.data) > 0`).
- [ ] **Altura correta:** `fig.layout.height == HEIGHT_BAR`.
- [ ] **Separadores PT-BR:** `fig.layout.separators == ",."`.
- [ ] **DataFrame vazio:** Função não lança exceção; retorna `go.Figure`.
- [ ] **Hover correto:** `hovertemplate` da trace contém `"R$"`.

### `bar_dy(dy)` com coluna `dy_ltm_pct`

- [ ] **Cenário feliz:** DataFrame com `produto` e `dy_ltm_pct` → retorna `go.Figure` válido.
- [ ] **Fallback de coluna:** DataFrame com `produto` e `dy_pct` (sem `dy_ltm_pct`) → usa `dy_pct` sem erro.
- [ ] **Altura correta:** `fig.layout.height == HEIGHT_BAR`.
- [ ] **Hover correto:** `hovertemplate` da trace contém `"%"`.

---

## Contexto do Código

```python
# dashboard/charts/bars.py — funções alvo
def bar_proventos(proventos) -> go.Figure: ...
def bar_dy(dy) -> go.Figure: ...
```

**Modelo de referência:** `tests/test_treemap.py` — mesma estrutura de fixture + asserts sobre `fig.layout`.

---

## Definição de "Testável"

O teste deu certo quando:
```
pytest tests/test_charts_bars.py -v
# → PASSED (todos os casos acima verdes)
```
