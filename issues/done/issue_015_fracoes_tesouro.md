# Issue 1.5 — Quantidade Fracionária do Tesouro Direto

**Fase:** 1 — Core: Motor de Cálculo e Eventos  
**Status:** ✅ Concluído  
**Commit:** `928e14f`  

---

## Por que esta tarefa é valiosa?

A quantidade de títulos do Tesouro Direto (ex.: `0,12` título) vinha sendo truncada ou exibida incorretamente nos cards e relatórios da carteira. Títulos públicos aceitam aportes em frações decimais (múltiplos de 0,01 título), exigindo que os parsers numéricos e as camadas de visualização preservem as casas decimais para a categoria TESOURO, sem afetar ações ou outros ativos que utilizam quantidades inteiras.

---

## Critérios de Aceite (Definition of Done)

- [x] Utilizar `parse_qtd` em `loaders/posicao.py` e `loaders/movimentacao.py` para preservar frações na coluna quantidade.
- [x] Formatar quantidade com 2 casas decimais para categoria TESOURO nos cards de custódia em `views/_helpers.py`.
- [x] Manter formatação inteira para Ações, BDRs e FIIs.
- [x] Testes unitários cobrindo `parse_qtd`, loaders e formatação condicional de cards em `tests/test_quantidade_tesouro.py`.

---

## Checklist de Ações

- [x] Adaptar `dashboard/utils.py` com `parse_qtd` com suporte a fracionários.
- [x] Atualizar loaders para aplicar `parse_qtd` nas colunas de quantidade.
- [x] Atualizar `_format_qtd` em `dashboard/views/_helpers.py` para distinguir categoria TESOURO.
- [x] Validar cobertura em `tests/test_quantidade_tesouro.py`.
