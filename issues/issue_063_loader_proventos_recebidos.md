# Issue 6.3 — Reader de Proventos Recebidos (`loaders/proventos_recebidos.py`)

**Fase:** 6 — Loader de Proventos Recebidos
**Status:** ✅ Concluído
**Estimativa:** 3–4 horas
**Dependência:** Issue 6.1 ✅ (schema) + Issue 6.2 ✅ (aliases)

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (criar fixtures e testes unitários antes de concluir o loader) → **2. Isole a Verdade (SSoT)** (reutilizar `normaliza_colunas` e aliases centralizados) → **3. Elimine a Duplicação (DRY)** (reutilizar parsers de valor e data) → **4. Divida (SRP)** (loader apenas lê e normaliza, sem computar métricas).

---

## Por que esta tarefa é valiosa?

A pasta `xlsx/proventos-recebidos/` já contém arquivos reais da B3. No entanto, hoje o dashboard só lê movimentações e posições. O arquivo de proventos recebidos traz detalhes granulares (ex: tipo de provento exato, data de pagamento vs data com, valor líquido creditado) que permitem tanto uma visão rica de renda quanto a conferência cruzada com a movimentação.

---

## Critérios de Aceite (Definition of Done)

- [x] Função `read_proventos_recebidos_file(path_or_buffer, qualidade=None) -> pd.DataFrame` implementada em `dashboard/loaders/proventos_recebidos.py`.
- [x] Colunas normalizadas conforme `ALIASES_PROV_RECEBIDOS`.
- [x] Datas parseadas para `pd.Timestamp` e valores monetários para `float`.
- [x] Tratamento de arquivo vazio ou inválido com retorno limpo ou relatório em `RelatorioQualidade`.
- [x] Integração com `dashboard/loaders/default_loader.py` e configuração de busca padrão em `app.py`.
- [x] Testes unitários em `tests/test_proventos_recebidos_loader.py` cobrindo cenários com arquivo válido, colunas ausentes e tipos inválidos.
- [x] `pytest tests/test_proventos_recebidos_loader.py` passando com 100% de sucesso.


---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar fixture mínima de teste em `tests/fixtures/` ou builder in-memory para proventos recebidos.
- [ ] Criar `tests/test_proventos_recebidos_loader.py` definindo os comportamentos esperados (parsing de datas, números e aliases).

### 2. Isole a Verdade (SSoT)
- [ ] Utilizar `ALIASES_PROV_RECEBIDOS` de `dashboard.aliases.proventos_recebidos`.
- [ ] Garantir que o nome das colunas canônicas obedeça ao schema documentado na Issue 6.1.

### 3. Elimine a Duplicação (DRY)
- [ ] Reutilizar funções de sanitização e parsing de moeda/data existentes (`parse_money`, etc.).

### 4. Divida (SRP)
- [ ] Isolar a função puramente no arquivo `loaders/proventos_recebidos.py`.
- [ ] Exportar no `loaders/__init__.py`.

---

## Definição de "Testável"

```bash
pytest tests/test_proventos_recebidos_loader.py -v
# → PASSED
```
