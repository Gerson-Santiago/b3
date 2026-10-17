# Issue Org.1 — Limpeza e Unificação de Loaders (`loader.py` vs `loaders/`)

**Fase:** Organização e Qualidade Arquitetural
**Status:** ⏳ Backlog
**Estimativa:** 1–2 horas
**Dependência:** Nenhuma

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de regressão de importações e leitura) → **2. Isole a Verdade (SSoT)** (um único local responsável por delegar leitura de arquivos B3) → **3. Elimine a Duplicação (DRY)** (eliminar wrapper solto na raiz) → **4. Divida (SRP)** (pasta `loaders/` assume toda a responsabilidade de I/O de dados).

---

## Por que esta tarefa é valiosa?

Hoje existem simultaneamente `dashboard/loader.py` na raiz do pacote e o subpacote `dashboard/loaders/` com `movimentacao.py`, `posicao.py` e `default_loader.py`.
O arquivo `loader.py` na raiz é apenas um dispatcher genérico (`read_b3_file`) que não é utilizado pelo `app.py`. Ter um arquivo solto causa ambiguidade ("onde implemento novos loaders?"), quebra a semântica de módulos e cria duplicação conceitual.

---

## Critérios de Aceite (Definition of Done)

- [ ] Mapear todas as referências ao arquivo `dashboard/loader.py` no projeto via busca no código.
- [ ] Transferir a lógica de dispatcher genérico (se ainda necessária) para `loaders/dispatcher.py` ou `loaders/__init__.py`.
- [ ] Deprecar ou remover `dashboard/loader.py` da raiz com segurança.
- [ ] Atualizar qualquer importação nos testes para apontar para `dashboard.loaders`.
- [ ] Todos os testes da suíte passam sem regressão (`pytest tests/`).

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Rodar a suíte completa de testes antes de qualquer alteração (`pytest`).

### 2. Isole a Verdade (SSoT)
- [ ] Unificar todos os pontos de entrada de leitura sob o subpacote `loaders/`.

### 3. Elimine a Duplicação (DRY)
- [ ] Remover importações duplicadas e arquivos obsoletos.

### 4. Divida (SRP)
- [ ] Deixar a raiz do pacote `dashboard/` limpa de loaders genéricos.

---

## Definição de "Testável"

```bash
pytest tests/ -v
# → PASSED (com 0 falhas e sem referências órfãs)
```
