# Issue 2.2 — Testes Unitários para `charts/lines.py`

**Fase:** 2 — Proteção
**Status:** ✅ Concluído
**Estimativa:** 2–3 horas
**Arquivo de teste a criar:** `tests/test_charts_lines.py`

---

## Por que esta tarefa é valiosa?

`lines.py` produz os dois gráficos de evolução patrimonial — o mais importante para responder a **Pergunta 1** ("Quanto meu patrimônio vale e como evoluiu?"). `line_comparativo_patrimonio_e_aportes` é também o gráfico mais complexo do módulo porque aceita `None` em qualquer dos dois parâmetros e combina múltiplas traces. Testes aqui garantem que o gráfico nunca quebre quando apenas um dataset estiver disponível.

---

## Critérios de Aceite (Definition of Done)

- [x] Arquivo `tests/test_charts_lines.py` criado.
- [x] `pytest tests/test_charts_lines.py` passa com `0 erros`.
- [x] Todos os cenários abaixo cobertos.

---

## Checklist de Ações

### `line_evolucao(evol)`

- [x] **Cenário feliz:** DataFrame com `data` e `patrimonio` → retorna `go.Figure` válido.
- [x] **Altura correta:** `fig.layout.height == HEIGHT_LINE`.
- [x] **Separadores PT-BR:** `fig.layout.separators == ",."`.
- [x] **Hover correto:** `hovertemplate` da trace contém `"Patrimônio"`.

### `line_comparativo_patrimonio_e_aportes(curva_aportes, curva_patrimonio)`

- [x] **Ambos presentes:** Dois DataFrames válidos → `len(fig.data) == 2`.
- [x] **Apenas aportes:** `curva_patrimonio=None` → `len(fig.data) == 1` (não lança exceção).
- [x] **Apenas patrimônio:** `curva_aportes=None` → `len(fig.data) == 1`.
- [x] **Ambos None:** Retorna `go.Figure` com `len(fig.data) == 0` sem lançar exceção.
- [x] **Ambos vazios (DataFrame empty):** Mesmo comportamento do caso `None`.
- [x] **Altura correta:** `fig.layout.height == HEIGHT_LINE_COMPARATIVO`.

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
