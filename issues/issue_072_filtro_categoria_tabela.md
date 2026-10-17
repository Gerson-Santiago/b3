# Issue 7.2 — Filtro e Agrupamento por Categoria na Tabela de Posição

**Fase:** 7 — Posição Interativa & Alocação Estendida
**Status:** ⏳ Backlog
**Estimativa:** 1–2 horas
**Dependência:** Issue 7.1 ✅ (tabela ordenável)

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de filtragem) → **2. Isole a Verdade (SSoT)** (categorias de `models/categorias.py`) → **3. Elimine a Duplicação (DRY)** (reutilizar constantes `CATEGORIAS_BOLSA`, `CATEGORIA_TESOURO`) → **4. Divida (SRP)** (filtro visual isolado).

---

## Por que esta tarefa é valiosa?

Com a tabela geral de posições implementada, o usuário precisa conseguir focar em classes específicas de ativos (apenas Ações, apenas BDRs, apenas FIIs ou apenas Renda Fixa/Tesouro) sem ter que reconfigurar os filtros globais da barra lateral.

---

## Critérios de Aceite (Definition of Done)

- [ ] Seletor multiselect ou pills/tabs acima da tabela de posições com as categorias presentes na carteira.
- [ ] Opção `"Todas"` selecionada por padrão.
- [ ] Linha ou card de subtotais (Patrimônio, Custo, Resultado R$ e %) atualizada dinamicamente com base na categoria selecionada.
- [ ] Categorias padronizadas via `models/categorias.py`.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Testar função de filtragem por categoria garantindo que mantém a integridade dos subtotais.

### 2. Isole a Verdade (SSoT)
- [ ] Importar nomes e classificações de `dashboard.models.categorias`.

### 3. Elimine a Duplicação (DRY)
- [ ] Utilizar a mesma regra de normalização de categoria já aplicada no Treemap e nos Cards.

### 4. Divida (SRP)
- [ ] Isolar a lógica de seleção e subtotais no componente da tabela.

---

## Definição de "Testável"

```bash
pytest tests/test_tabela_posicao.py -v
# → PASSED
```
