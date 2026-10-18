# Issue 2.3 — Testes Unitários para `charts/pie.py`

**Fase:** 2 — Proteção
**Status:** ✅ Concluído
**Estimativa:** 2–3 horas
**Arquivo de teste a criar:** `tests/test_charts_pie.py`

---

## Por que esta tarefa é valiosa?

`pie.py` contém 3 funções (`pie_carteira`, `pie_carteira_por_categoria`, `pie_categoria`) que são a resposta principal à **Pergunta 3** ("Minha carteira está diversificada?"). Esses testes também criam a linha de base necessária para a refatoração DRY da Fase 3 (Issue 3.1), que unificará as três funções em uma fábrica interna.

---

## Critérios de Aceite (Definition of Done)

- [x] Arquivo `tests/test_charts_pie.py` criado.
- [x] `pytest tests/test_charts_pie.py` passa com `0 erros`.
- [x] Todos os cenários abaixo cobertos.

---

## Checklist de Ações

### Fixture compartilhada

- [x] Criar `pos_sample` com colunas `produto`, `valor_abs`, `categoria`.
- [x] Criar `pos_categoria_sample` com colunas `categoria`, `valor`.

### `pie_carteira(pos)`

- [x] **Cenário feliz:** DataFrame com `produto` e `valor_abs` → retorna `go.Figure` válido (`len(fig.data) > 0`).
- [x] **Hole = donut:** `fig.data[0].hole == 0.45`.
- [x] **Altura correta:** `fig.layout.height == HEIGHT_PIE`.
- [x] **Separadores PT-BR:** `fig.layout.separators == ",."`.

### `pie_carteira_por_categoria(pos_categoria)`

- [x] **Cenário feliz:** DataFrame com `categoria` e `valor` → retorna `go.Figure` válido.
- [x] **Altura correta:** `fig.layout.height == HEIGHT_PIE`.
- [x] **Hole = donut:** `fig.data[0].hole == 0.45`.

### `pie_categoria(pos, titulo)`

- [x] **Cenário feliz:** Retorna `go.Figure` válido.
- [x] **Título customizado:** `fig.layout.title.text == "Meu Título"` ao passar `titulo="Meu Título"`.
- [x] **Altura correta:** `fig.layout.height == HEIGHT_PIE_SMALL`.

---

## Contexto do Código

```python
# dashboard/charts/pie.py — funções alvo
def pie_carteira(pos) -> go.Figure: ...
def pie_carteira_por_categoria(pos_categoria) -> go.Figure: ...
def pie_categoria(pos, titulo: str = "...") -> go.Figure: ...
```

---

## Definição de "Testável"

O teste deu certo quando:
```
pytest tests/test_charts_pie.py -v
# → PASSED (todos os casos acima verdes)
```

> **Nota:** Este teste também serve como contrato para a Issue 3.1.
> Após a refatoração DRY, todos esses testes devem continuar passando sem modificação.
