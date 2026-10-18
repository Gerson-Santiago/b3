# Roadmap — Projeto B3 Dashboard

> **Objetivo Final:** Transformar o dashboard de um visualizador de posições num **cockpit de decisão de alocação de capital e rentabilidade**, respondendo às 4 perguntas-chave do investidor:
> 1. Quanto meu patrimônio vale hoje e como evoluiu?
> 2. Quais ativos estão gerando lucro, prejuízo e renda?
> 3. Minha carteira está diversificada ou concentrada demais?
> 4. Quanto recebi de dividendos/JCP e qual é a tendência?

> **Fluxo Ideal de Refatoração em Cada Issue:**
> 1. **Proteja:** Verifique/crie os testes unitários cobrindo o comportamento atual.
> 2. **Isole a Verdade (SSoT):** Identifique regras duplicadas e centralize-as em uma única estrutura; ajuste os testes para refletir essa centralização.
> 3. **Elimine a Duplicação (DRY):** Limpe a redundância tanto no código de teste quanto no código de produção.
> 4. **Divida (SRP):** Quebre funções e classes grandes em componentes coesos, validando cada passo com a execução contínua dos testes.

---

## Fases e Status

| Fase | Módulo | Descrição | Status |
| :--- | :--- | :--- | :---: |
| **Fase 1** | `models/` | Core: Motor de Cálculo, Eventos e Frações Tesouro (1.1–1.5) | ✅ Concluído |
| **Fase 2** | `tests/` | Proteção: Cobertura Unitária da Camada de Gráficos (2.1–2.4) | ✅ Concluído |
| **Fase 3** | `charts/` | SSoT & DRY: Consolidação da Camada de Visualização (3.1–3.3) | ✅ Concluído |
| **Fase 4** | `charts/` + `views/` | P&L, Rentabilidade, 5 Classes, Macro Donut e Ícones SVG (4.1–4.6) | ✅ Concluído |
| **Fase 5** | `metrics/` + `views/` | Calendário de Proventos e Fluxo de Caixa (5.1–5.3 ✅ / 5.4 ⏳) | 🟡 Em Progresso |
| **Fase 6** | `loaders/` + `metrics/` | Loader de Proventos Recebidos & Reconciliação | ⏳ Backlog |
| **Fase 7** | `views/` + `charts/` | Posição Interativa & Alocação Estendida (Setor/Corretora) | ⏳ Backlog |
| **Fase 8** | `metrics/` + `views/` | Vendas, Lucro Realizado e Controle Fiscal (IR) | ⏳ Backlog |
| **Fase 9** | `metrics/` + `views/` | Gestão de Risco e Sinais de Realização de Lucro | ⏳ Backlog |
| **Org** | `loaders/` + `models/` | Limpeza e Desacoplamento Estrutural (`loader.py`, `utils.py`) | ⏳ Backlog |

---

## Fase 1 — Core: Motor de Cálculo e Eventos ✅

> Refatoração do núcleo de domínio (`dashboard/models/`). Todos os commits no branch `dev`.

| # | Issue | Status |
| :--- | :--- | :---: |
| 1.1 | Separação de responsabilidades em `efeitos.py` | ✅ |
| 1.2 | Remoção de `if/else` por tipo de movimentação | ✅ |
| 1.3 | Decidir por semântica em `texto/valor` | ✅ |
| 1.4 | Extração de `pipeline_eventos.py` de `motor_posicao.py` | ✅ |
| 1.5 | [issue_015_fracoes_tesouro.md](./issue_015_fracoes_tesouro.md) (Quantidade fracionária do Tesouro Direto nos loaders e cards) | ✅ |

---

## Fase 2 — Proteção: Cobertura Unitária da Camada de Gráficos ✅

> **Princípio:** Antes de refatorar ou adicionar qualquer gráfico, fixar o comportamento atual com testes.
> **Referência:** `tests/test_treemap.py` é o modelo de qualidade a seguir.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 2.1 | [issue_021_testes_bar.md](./issue_021_testes_bar.md) | Testes unitários para `charts/bars.py` | ✅ Concluído |
| 2.2 | [issue_022_testes_lines.md](./issue_022_testes_lines.md) | Testes unitários para `charts/lines.py` | ✅ Concluído |
| 2.3 | [issue_023_testes_pie.md](./issue_023_testes_pie.md) | Testes unitários para `charts/pie.py` | ✅ Concluído |
| 2.4 | [issue_024_testes_base.md](./issue_024_testes_base.md) | Testes unitários para `charts/base.py` | ✅ Concluído |

---

## Fase 3 — SSoT & DRY: Consolidação da Camada de Visualização ✅

> **Princípio:** Eliminar duplicação dentro dos módulos de gráficos e mover regras de classificação para o domínio.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 3.1 | [issue_031_dry_pie.md](./issue_031_dry_pie.md) | Extrair `_criar_donut()` para eliminar triplicação em `pie.py` | ✅ Concluído |
| 3.2 | [issue_032_ssot_hierarquia.md](./issue_032_ssot_hierarquia.md) | Mover regras de remapeamento de categoria de `treemap.py` para `models/categorias.py` | ✅ Concluído |
| 3.3 | [issue_033_dry_treemap.md](./issue_033_dry_treemap.md) | Extrair lógica de vazio e layout compartilhado em `treemap.py` | ✅ Concluído |

---

## Fase 4 — Novos Gráficos, Alocação Macro & Identidade Visual ✅

> **Princípio:** Adicionar gráficos de alto valor que respondem às Perguntas 1 e 2 ainda sem visualização e enriquecer a experiência visual da carteira.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 4.1 | [issue_041_bar_pl.md](./issue_041_bar_pl.md) | Criar `bar_lucro_prejuizo()` em `charts/bars.py` e integrar na view `carteira.py` | ✅ Concluído |
| 4.2 | [issue_042_line_rentabilidade.md](./issue_042_line_rentabilidade.md) | Criar `line_rentabilidade_acumulada()` com linha de benchmark (CDI/IPCA) | ✅ Concluído |
| 4.3 | [issue_043_alocacao_5_classes.md](./issue_043_alocacao_5_classes.md) | Classificação dinâmica em 5 Classes de Ativos e segmentação de Renda Fixa | ✅ Concluído |
| 4.4 | [issue_044_ranking_ativos_donut.md](./issue_044_ranking_ativos_donut.md) | Ranking de ativos em barras e agrupamento de fatias < 3% no donut | ✅ Concluído |
| 4.5 | [issue_045_donut_macro.md](./issue_045_donut_macro.md) | Gráfico donut alinhado de Alocação Macro (Bolsa vs Tesouro) com cores SSoT | ✅ Concluído |
| 4.6 | [issue_046_icones_svg.md](./issue_046_icones_svg.md) | Integração de logos SVG e carregamento lazy para cards de custódia | ✅ Concluído |

---

## Fase 5 — Calendário de Proventos e Fluxo de Caixa 🟡

> **Princípio:** Fechar a última lacuna das 4 perguntas — a tendência, sazonalidade e fluxo de proventos recebidos.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 5.1 | [issue_051_proventos_acumulado.md](./issue_051_proventos_acumulado.md) | Adicionar linha de acumulado anual ao `bar_proventos()` | ✅ Concluído |
| 5.2 | [issue_052_proventos_tipo.md](./issue_052_proventos_tipo.md) | Segmentar `bar_proventos()` por tipo: Dividendos vs JCP vs FII | ✅ Concluído |
| 5.3 | [issue_053_proventos_calendario.md](./issue_053_proventos_calendario.md) | Calendário de proventos por data de pagamento (Código pronto; falta teste isolado) | 🟡 Quase Concluído |
| 5.4 | [issue_054_proventos_ranking.md](./issue_054_proventos_ranking.md) | Ranking dos maiores pagadores (top 10 por DY e por R$) | ⏳ Backlog |


---

## Fase 6 — Loader de Proventos Recebidos & Reconciliação ⏳

> **Princípio:** Integrar a fonte dedicada de proventos da B3 e cruzar com os eventos de movimentação.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 6.1 | [issue_061_schema_proventos_recebidos.md](./issue_061_schema_proventos_recebidos.md) | Documentação de schema do export de proventos recebidos | ⏳ Backlog |
| 6.2 | [issue_062_aliases_proventos_recebidos.md](./issue_062_aliases_proventos_recebidos.md) | Mapeamento centralizado de aliases para proventos recebidos | ⏳ Backlog |
| 6.3 | [issue_063_loader_proventos_recebidos.md](./issue_063_loader_proventos_recebidos.md) | Reader isolado e tipado em `loaders/proventos_recebidos.py` | ⏳ Backlog |
| 6.4 | [issue_064_reconciliacao_proventos.md](./issue_064_reconciliacao_proventos.md) | Cálculo de conciliação cruzada (Movimentação vs Extrato Proventos) | ⏳ Backlog |
| 6.5 | [issue_065_view_reconciliacao_proventos.md](./issue_065_view_reconciliacao_proventos.md) | Exibição de auditoria de proventos em `views/reconciliacao.py` | ⏳ Backlog |

---

## Fase 7 — Posição Interativa & Alocação Estendida ⏳

> **Princípio:** Transformar os cards estáticos em visão tabular dinâmica com recortes por corretora e setor.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 7.1 | [issue_071_tabela_posicao_ordenavel.md](./issue_071_tabela_posicao_ordenavel.md) | Tabela `st.dataframe` ordenável de custódia com PM vs Atual | ⏳ Backlog |
| 7.2 | [issue_072_filtro_categoria_tabela.md](./issue_072_filtro_categoria_tabela.md) | Filtro dinâmico por classe de ativos e subtotais na tabela | ⏳ Backlog |
| 7.3 | [issue_073_alocacao_corretora.md](./issue_073_alocacao_corretora.md) | Gráfico donut e tabela de alocação por corretora/instituição | ⏳ Backlog |
| 7.4 | [issue_074_alocacao_setor.md](./issue_074_alocacao_setor.md) | Mapeamento canônico de setores e visão de diversificação setorial | ⏳ Backlog |

---

## Fase 8 — Vendas, Lucro Realizado e Controle Fiscal (IR) ⏳

> **Princípio:** Registrar histórico de liquidações e automatizar regras de tributação da Receita Federal.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 8.1 | [issue_081_lucro_realizado.md](./issue_081_lucro_realizado.md) | Apuração de lucro/prejuízo por venda individual (Preço Médio Ponderado) | ⏳ Backlog |
| 8.2 | [issue_082_agregacao_mensal_anual_lucro.md](./issue_082_agregacao_mensal_anual_lucro.md) | Agregação temporal de resultados realizados (mensal e anual) | ⏳ Backlog |
| 8.3 | [issue_083_calculo_ir_isencao.md](./issue_083_calculo_ir_isencao.md) | Motor fiscal: isenção R$ 20k ações swing, cestas de compensação e DARF 6015 | ⏳ Backlog |
| 8.4 | [issue_084_view_vendas_ir.md](./issue_084_view_vendas_ir.md) | Nova aba "Vendas & IR" com painel de DARF e histórico de vendas | ⏳ Backlog |

---

## Fase 9 — Gestão de Risco e Sinais de Realização de Lucro ⏳

> **Princípio:** Prover ferramentas ativas para decisões de rebalanceamento e controle de concentração.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 9.1 | [issue_091_metrics_risco.md](./issue_091_metrics_risco.md) | Métricas de risco: concentração Top 5, exposição cambial e HHI | ⏳ Backlog |
| 9.2 | [issue_092_metrics_sinais_venda.md](./issue_092_metrics_sinais_venda.md) | Gatilhos de rebalanceamento: peso vs meta, lucro esticado e DY | ⏳ Backlog |
| 9.3 | [issue_093_view_risco_sinais.md](./issue_093_view_risco_sinais.md) | Cockpit de risco e painel semafórico de alertas (🟢🟡🔴) | ⏳ Backlog |

---

## Organização e Qualidade Arquitetural (Issues Transversais) ⏳

> **Princípio:** Eliminar código morto, depósitos genéricos e ambiguidade na árvore de arquivos.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| Org.1 | [issue_org_01_loader_raiz.md](./issue_org_01_loader_raiz.md) | Unificar `loader.py` na raiz sob o subpacote `loaders/` | ⏳ Backlog |
| Org.2 | [issue_org_02_limpeza_utils_columns.md](./issue_org_02_limpeza_utils_columns.md) | Modularizar `utils.py` (parsers vs I/O) e unificar `columns.py` | ⏳ Backlog |

---

> **Regra de ouro:** Sempre que marcar uma issue como `✅ Concluído`, atualize esta tabela.
> Nunca inicie a Fase N+1 sem a cobertura de testes da Fase N estar verde (`pytest --tb=short`).
