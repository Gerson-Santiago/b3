# Issue 4.3 — Alocação Dinâmica em 5 Classes de Ativos & Segmentação de Renda Fixa

**Fase:** 4 — Novos Gráficos, Alocação Macro & Identidade Visual  
**Status:** ✅ Concluído  
**Commit:** `93c4708`  

---

## Por que esta tarefa é valiosa?

A visão tradicional de carteira agrupava os ativos de forma rasa ou apenas binária (Bolsa vs Tesouro). Para uma gestão moderna de patrimônio, é fundamental segmentar a carteira em 5 classes fundamentais de risco e indexação: Ações, BDRs, Tesouro Pós-fixado (Selic), Tesouro Inflação (IPCA+ / Educa+) e Tesouro Prefixado. Essa divisão permite ao investidor auditar sua exposição real a juros, inflação e renda variável.

---

## Critérios de Aceite (Definition of Done)

- [x] Classificador canônico `classificar_classe_5(produto, categoria)` em `models/categorias.py`.
- [x] Agregação de alocação `calcular_alocacao_5_classes(pos_df)` retornando `classe`, `categoria`, `valor` e `peso_pct`.
- [x] Curvas de evolução segmentadas para as classes de Renda Fixa (Inflação, Pós, Pré) em `dashboard/state_pipeline.py`.
- [x] Exibição de cards de métricas das 5 classes na aba `views/carteira.py`.
- [x] Suporte ao agrupamento por 5 classes nos gráficos hierárquicos (Treemap e Sunburst).
- [x] Testes unitários cobrindo classificação e curvas em `tests/test_renda_fixa.py` e `tests/test_state.py`.

---

## Checklist de Ações

- [x] Implementar regras das 5 classes em `dashboard/models/categorias.py`.
- [x] Extrair curvas segmentadas em `dashboard/metrics/renda_fixa.py` e integrá-las ao `DashboardState`.
- [x] Integrar seção "Alocação por Classe de Ativos" em `dashboard/views/carteira.py`.
- [x] Conectar opção "5 Classes de Ativos" no seletor de hierarquia de Treemap e Sunburst.
