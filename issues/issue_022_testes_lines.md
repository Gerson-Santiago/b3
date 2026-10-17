# Issue 2.2 — Testes Unitários para `charts/lines.py`

**Fase:** 2 — Proteção
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Arquivo de teste a criar:** `tests/test_charts_lines.py`

---

## Por que esta tarefa é valiosa?

`lines.py` produz os dois gráficos de evolução patrimonial — o mais importante para responder a **Pergunta 1** ("Quanto meu patrimônio vale e como evoluiu?"). `line_comparativo_patrimonio_e_aportes` é também o gráfico mais complexo do módulo porque aceita `None` em qualquer dos dois parâmetros e combina múltiplas traces. Testes aqui garantem que o gráfico nunca quebre quando apenas um dataset estiver disponível.

---

## Critérios de Aceite (Definition of Done)

- [ ] Arquivo `tests/test_charts_lines.py` criado.
- [ ] `pytest tests/test_charts_lines.py` passa com `0 erros`.
- [ ] Todos os cenários abaixo cobertos.

---

## Checklist de Ações

### `line_evolucao(evol)`

- [ ] **Cenário feliz:** DataFrame com `data` e `patrimonio` → retorna `go.Figure` válido.
- [ ] **Altura correta:** `fig.layout.height == HEIGHT_LINE`.
- [ ] **Separadores PT-BR:** `fig.layout.separators == ",."`.
- [ ] **Hover correto:** `hovertemplate` da trace contém `"Patrimônio"`.

### `line_comparativo_patrimonio_e_aportes(curva_aportes, curva_patrimonio)`

- [ ] **Ambos presentes:** Dois DataFrames válidos → `len(fig.data) == 2`.
- [ ] **Apenas aportes:** `curva_patrimonio=None` → `len(fig.data) == 1` (não lança exceção).
- [ ] **Apenas patrimônio:** `curva_aportes=None` → `len(fig.data) == 1`.
- [ ] **Ambos None:** Retorna `go.Figure` com `len(fig.data) == 0` sem lançar exceção.
- [ ] **Ambos vazios (DataFrame empty):** Mesmo comportamento do caso `None`.
- [ ] **Altura correta:** `fig.layout.height == HEIGHT_LINE_COMPARATIVO`.

---

## Contexto do Código

```python
# dashboard/charts/lines.py — funções alvo
def line_evolucao(evol) -> go.Figure: ...
def line_comparativo_patrimonio_e_aportes(curva_aportes, curva_patrimonio) -> go.Figure: ...
```

**Colunas esperadas:**
- `curva_aportes`: `data`, `custo_acumulado`
- `curva_patrimonio`: `data`, `patrimonio_liquido`

---

## Definição de "Testável"

O teste deu certo quando:
```
pytest tests/test_charts_lines.py -v
# → PASSED (todos os casos acima verdes)
```
