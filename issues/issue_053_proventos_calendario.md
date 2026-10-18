# Issue 5.3 — Calendário de Proventos (Tabela por Data de Pagamento)

**Fase:** 5 — Calendário de Proventos e Fluxo de Caixa
**Status:** 🟡 Quase Concluído (Código implementado; testes unitários pendentes)
**Estimativa:** 3–4 horas
**Dependência:** Issue 5.1 ✅ + Issue 5.2 ✅

---

## Por que esta tarefa é valiosa?

O investidor precisa saber **quando** vai receber proventos, não só o quanto. A visão mensal de barras responde "quanto recebo por mês", mas não responde "quais ativos pagam em outubro?" ou "qual é o meu calendário de renda nos próximos meses?". Uma tabela de calendário organizada por data de pagamento e ativo fecha essa lacuna e auxilia no planejamento de caixa e reinvestimento.

---

## Critérios de Aceite (Definition of Done)

- [x] Tabela `st.dataframe` exibida na aba `Proventos & Renda` com colunas: `data`, `ativo`, `tipo` (Dividendo/JCP/Rendimento FII), `valor_liquido`.
- [x] Tabela ordenada por `data` descendente (mais recente no topo) por padrão.
- [ ] Filtro de mês/ano na sidebar ou acima da tabela (utiliza filtro temporal global da aplicação).
- [x] Linha de totais visível (total no período e contagem de pagamentos via `st.caption`).
- [x] Função `build_calendario_proventos(mov_df)` em `metrics/proventos.py` (e integrada a `DashboardState`).
- [ ] Testes unitários em `tests/test_b3_metrics.py` (ou `test_proventos.py`): cenário feliz + DataFrame vazio.

---

## Checklist de Ações

### 1. Métrica em `metrics/proventos.py`

- [x] Criar `build_calendario_proventos(mov_df: pd.DataFrame) -> pd.DataFrame`.
- [x] Filtrar eventos de provento usando `efeito_movimentacao(...).provento` + `is_credito(entrada_saida)`.
- [x] Extrair colunas: `data`, `ativo` (ou `produto`), `movimentacao` (como `tipo`), `valor_liquido`.
- [x] Ordenar por `data` descendente.

### 2. View em `views/proventos.py`

- [x] Importar `build_calendario_proventos` (integrado via `state.calendario_proventos`).
- [x] Adicionar seção `"### Calendário de Proventos Recebidos"` abaixo das métricas de DY.
- [x] Renderizar `st.dataframe(calendario, width="stretch")` com `column_config` descritivo.

### 3. Testes

- [ ] DataFrame com 3 proventos em meses distintos → retorna DataFrame com 3 linhas.
- [ ] DataFrame vazio → retorna DataFrame vazio sem exceção.

---

## Contexto — Dados Disponíveis

```python
# metrics/proventos.py — compute_proventos() já filtra os eventos de provento.
# A mesma lógica de filtro pode ser reutilizada aqui, sem reagregar por mês.
# Reutilizar: efeito_movimentacao(...).provento e is_credito(entrada_saida)
```

---

## Definição de "Testável"

```
pytest tests/test_b3_metrics.py -v   # ou test_proventos.py
# → PASSED
# Dashboard: tabela de calendário visível na aba Proventos & Renda
# Colunas: data | ativo | tipo | valor_liquido
```
