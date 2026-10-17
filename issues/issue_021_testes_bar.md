# Issue 2.1 — Testes Unitários para `charts/bars.py`

**Fase:** 2 — Proteção
**Status:** ✅ Concluído
**Estimativa:** 2–3 horas
**Arquivo de teste a criar:** `tests/test_charts_bars.py`

---

## Por que esta tarefa é valiosa?

`bars.py` produz os gráficos de `Proventos Mensais` e `Dividend Yield` — dois dos indicadores de renda do investidor (Pergunta 4). Sem testes, qualquer mudança futura na camada de métricas pode quebrar silenciosamente a visualização. Esta issue é a **rede de segurança antes de qualquer refatoração** nos gráficos.

---

## Critérios de Aceite (Definition of Done)

- [x] Arquivo `tests/test_charts_bars.py` criado.
- [x] `pytest tests/test_charts_bars.py` passa com `0 erros`.
- [x] Todos os cenários abaixo cobertos por pelo menos 1 teste.

---

## Checklist de Ações

### `bar_proventos(proventos)`

- [x] **Cenário feliz:** DataFrame com colunas `mes` e `valor_liquido` → retorna `go.Figure` válido (`len(fig.data) > 0`).
- [x] **Altura correta:** `fig.layout.height == HEIGHT_BAR`.
- [x] **Separadores PT-BR:** `fig.layout.separators == ",."`.
- [x] **DataFrame vazio:** Função não lança exceção; retorna `go.Figure`.
- [x] **Hover correto:** `hovertemplate` da trace contém `"R$"`.

### `bar_dy(dy)` com coluna `dy_ltm_pct`

- [x] **Cenário feliz:** DataFrame com `produto` e `dy_ltm_pct` → retorna `go.Figure` válido.
- [x] **Fallback de coluna:** DataFrame com `produto` e `dy_pct` (sem `dy_ltm_pct`) → usa `dy_pct` sem erro.
- [x] **Altura correta:** `fig.layout.height == HEIGHT_BAR`.
- [x] **Hover correto:** `hovertemplate` da trace contém `"%"`.

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
