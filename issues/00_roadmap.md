# Roadmap — Projeto B3 Dashboard

> **Objetivo Final:** Transformar o dashboard de um visualizador de posições num **cockpit de decisão de alocação de capital e rentabilidade**, respondendo às 4 perguntas-chave do investidor:
> 1. Quanto meu patrimônio vale hoje e como evoluiu?
> 2. Quais ativos estão gerando lucro, prejuízo e renda?
> 3. Minha carteira está diversificada ou concentrada demais?
> 4. Quanto recebi de dividendos/JCP e qual é a tendência?

---

## Fases e Status

| Fase | Módulo | Descrição | Status |
| :--- | :--- | :--- | :---: |
| **Fase 1** | `models/` | Core: Motor de Cálculo e Eventos (1.1–1.4) | ✅ Concluído |
| **Fase 2** | `tests/` | Proteção: Cobertura Unitária da Camada de Gráficos | ✅ Concluído |
| **Fase 3** | `charts/` | SSoT & DRY: Consolidação da Camada de Visualização | ✅ Concluído |
| **Fase 4** | `charts/` + `views/` | Novos Gráficos: P&L e Rentabilidade Comparativa | ⏳ Backlog |
| **Fase 5** | `metrics/` + `views/` | Calendário de Proventos e Fluxo de Caixa | ⏳ Backlog |

---

## Fase 1 — Core: Motor de Cálculo e Eventos ✅

> Refatoração do núcleo de domínio (`dashboard/models/`). Todos os commits no branch `dev`.

| # | Issue | Status |
| :--- | :--- | :---: |
| 1.1 | Separação de responsabilidades em `efeitos.py` | ✅ |
| 1.2 | Remoção de `if/else` por tipo de movimentação | ✅ |
| 1.3 | Decidir por semântica em `texto/valor` | ✅ |
| 1.4 | Extração de `pipeline_eventos.py` de `motor_posicao.py` | ✅ |

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

## Fase 4 — Novos Gráficos: P&L e Rentabilidade ⏳

> **Princípio:** Adicionar gráficos de alto valor que respondem às Perguntas 1 e 2 ainda sem visualização.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 4.1 | [issue_041_bar_pl.md](./issue_041_bar_pl.md) | Criar `bar_lucro_prejuizo()` em `charts/bars.py` e integrar na view `carteira.py` | ✅ Concluído |
| 4.2 | [issue_042_line_rentabilidade.md](./issue_042_line_rentabilidade.md) | Criar `line_rentabilidade_acumulada()` com linha de benchmark (CDI/IPCA) | ⏳ Backlog |

---

## Fase 5 — Calendário de Proventos e Fluxo de Caixa ⏳

> **Princípio:** Fechar a última lacuna das 4 perguntas — a tendência e sazonalidade da renda passiva.

| # | Arquivo de Issue | Descrição | Status |
| :--- | :--- | :--- | :---: |
| 5.1 | [issue_051_proventos_acumulado.md](./issue_051_proventos_acumulado.md) | Adicionar linha de acumulado anual ao `bar_proventos()` | ⏳ Backlog |
| 5.2 | [issue_052_proventos_tipo.md](./issue_052_proventos_tipo.md) | Segmentar `bar_proventos()` por tipo: Dividendos vs JCP vs FII | ⏳ Backlog |

---

> **Regra de ouro:** Sempre que marcar uma issue como `✅ Concluído`, atualize esta tabela.
> Nunca inicie a Fase N+1 sem a cobertura de testes da Fase N estar verde (`pytest --tb=short`).
