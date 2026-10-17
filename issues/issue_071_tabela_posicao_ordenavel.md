# Issue 7.1 — Tabela de Posição Ordenável (`views/carteira.py` ou componente dedicado)

**Fase:** 7 — Posição Interativa & Alocação Estendida
**Status:** ⏳ Backlog
**Estimativa:** 3–4 horas
**Dependência:** Fase 1 ✅ + `state.pos_cards` ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes com estrutura de `pos_cards`) → **2. Isole a Verdade (SSoT)** (usar exclusivamente `state.pos_cards` sem recalcular) → **3. Elimine a Duplicação (DRY)** (reutilizar formatação de moeda e percentual de `_helpers.py`) → **4. Divida (SRP)** (isolar a construção da tabela de exibição em função pura).

---

## Por que esta tarefa é valiosa?

Hoje o dashboard exibe a custódia em cards individuais separados por categoria. Quando o investidor possui dezenas de ativos, comparar ordenadamente por **Preço Médio vs Preço Atual**, **Lucro/Prejuízo (R$)**, **Rentabilidade (%)** ou **Peso na Carteira (%)** torna-se demorado. Uma tabela interativa e ordenável permite identificar instantaneamente as maiores posições e maiores desvios da carteira.

---

## Critérios de Aceite (Definition of Done)

- [ ] Tabela interativa via `st.dataframe` com suporte a ordenação por clique no cabeçalho das colunas.
- [ ] Colunas exibidas:
  - `Ativo` (código/ticker)
  - `Categoria` (Ações, BDR, FII, Tesouro)
  - `Quantidade`
  - `Preço Médio (R$)`
  - `Preço Atual / Cotação (R$)`
  - `Valor Total / Patrimônio (R$)`
  - `Custo Total (R$)`
  - `Resultado (R$)`
  - `Rentabilidade (%)`
  - `% da Carteira`
- [ ] Formatação de valores numéricos como moeda e porcentagem via `column_config` nativo do Streamlit.
- [ ] Integrado na view `views/carteira.py`.
- [ ] Teste unitário verificando a preparação do DataFrame para exibição (sem quebras com valores nulos ou zero).

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar teste unitário em `tests/test_tabela_posicao.py` testando a função formatação com `pos_cards`.

### 2. Isole a Verdade (SSoT)
- [ ] Utilizar as colunas já computadas em `state.pos_cards` (`valor_abs`, `custo_total`, `pl`, `variacao_pct`, `peso_pct`, etc.).

### 3. Elimine a Duplicação (DRY)
- [ ] Evitar recálculos de rentabilidade na camada visual; usar as propriedades já enriquecidas pelo pipeline.

### 4. Divida (SRP)
- [ ] Criar função `_render_tabela_posicoes(pos_cards: pd.DataFrame)` em `views/carteira.py` (ou `views/_helpers.py`).

---

## Definição de "Testável"

```bash
pytest tests/test_tabela_posicao.py -v
# → PASSED
# Tabela com cabeçalhos ordenáveis exibida no Streamlit
```
