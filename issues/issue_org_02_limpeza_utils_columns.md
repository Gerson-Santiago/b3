# Issue Org.2 — Modularização e Limpeza de `utils.py` e `columns.py`

**Fase:** Organização e Qualidade Arquitetural
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Dependência:** Nenhuma

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes unitários para `parse_money`, `parse_qtd`, `find_latest`, `normaliza_colunas`) → **2. Isole a Verdade (SSoT)** (parsers de domínio em `models/`, busca de arquivos em `loaders/`, colunas em `aliases/`) → **3. Elimine a Duplicação (DRY)** (eliminar `columns.py` que é só pass-through de aliases) → **4. Divida (SRP)** (acabar com módulos depósito na raiz).

---

## Por que esta tarefa é valiosa?

Arquivos com nomes genéricos como `utils.py` tendem a atrair lógicas heterogêneas ao longo do tempo. Hoje, `utils.py` mistura:
1. `find_latest` (busca e ordenação de arquivos no disco, que pertence a I/O dos `loaders`)
2. `parse_money` e `parse_qtd` (regras semânticas de parsing de números e texto B3, que pertencem a `models/parsers.py`)

Além disso, `columns.py` contém apenas a função `normaliza_colunas()`, que nada mais é do que um executor do subpacote `aliases/`. Mover cada responsabilidade para seu módulo natural traz clareza e previsibilidade à arquitetura.

---

## Critérios de Aceite (Definition of Done)

- [ ] `parse_money` e `parse_qtd` movidos para `dashboard/models/parsers.py` (ou `models/texto.py`).
- [ ] `find_latest` movido para `dashboard/loaders/fs.py` ou `dashboard/loaders/utils.py`.
- [ ] `normaliza_colunas` integrado diretamente em `dashboard/aliases/__init__.py`.
- [ ] Manter reexports temporários com `DeprecationWarning` ou atualizar todas as chamadas no código e testes.
- [ ] Suíte de testes 100% verde (`pytest`).

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Garantir testes cobrindo `parse_money`, `parse_qtd`, `find_latest` e `normaliza_colunas`.

### 2. Isole a Verdade (SSoT)
- [ ] Centralizar parsers nos models e I/O nos loaders.

### 3. Elimine a Duplicação (DRY)
- [ ] Remover código redundante em `columns.py`.

### 4. Divida (SRP)
- [ ] Quebrar o módulo monolítico `utils.py` em componentes com responsabilidade única.

---

## Definição de "Testável"

```bash
pytest tests/ -v
# → PASSED
```
