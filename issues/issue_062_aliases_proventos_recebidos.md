# Issue 6.2 — Aliases de Proventos Recebidos (`aliases/proventos_recebidos.py`)

**Fase:** 6 — Loader de Proventos Recebidos
**Status:** ✅ Concluído
**Estimativa:** 1 hora
**Dependência:** Issue 6.1 ✅ (schema documentado)

---

## Por que esta tarefa é valiosa?

Seguindo o padrão SSoT do projeto (`aliases/movimentacao.py`, `aliases/posicao.py`), o mapeamento entre os nomes de coluna brutos da B3 e os nomes normalizados em snake_case deve ficar em **um único lugar**. Qualquer variação ortográfica (acento/sem acento, maiúscula/minúscula) é tratada aqui, não espalhada no reader.

---

## Critérios de Aceite (Definition of Done)

- [x] Arquivo `aliases/proventos_recebidos.py` criado com `ALIASES_PROV_RECEBIDOS: dict[str, list[str]]`.
- [x] Colunas mapeadas conforme schema da Issue 6.1.
- [x] Exportado em `aliases/__init__.py`.
- [x] Teste unitário verifica que todas as chaves do alias produzem um nome normalizado único (sem colisão).


---

## Checklist de Ações

- [ ] Criar `dashboard/aliases/proventos_recebidos.py` com estrutura idêntica a `movimentacao.py`:
  ```python
  from dashboard.aliases.common import normalize_alias

  ALIASES_PROV_RECEBIDOS = {
      "produto":        ["Produto", "Ativo", ...],
      "tipo_evento":    ["Tipo de Evento", "Tipo", ...],
      "data_pagamento": ["Data do Pagamento", "Pagamento", ...],
      "data_ex":        ["Data Ex", "Data Ex-Dividendo", ...],
      # ... demais colunas conforme schema 6.1
  }
  ```
- [ ] Adicionar `from .proventos_recebidos import ALIASES_PROV_RECEBIDOS` em `aliases/__init__.py`.
- [ ] Adicionar `"ALIASES_PROV_RECEBIDOS"` em `__all__`.
- [ ] Criar teste em `tests/` verificando ausência de colisão entre aliases.

---

## Definição de "Testável"

```
pytest tests/ -k "alias" -v
# → PASSED
# Nenhum nome normalizado aparece em dois aliases diferentes.
```
