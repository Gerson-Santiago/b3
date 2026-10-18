# Área do Investidor B3 — Guia de Arquitetura & Schemas

A **Área do Investidor** é o portal oficial da B3 que centraliza a custódia e o histórico operacional de ativos financeiros mantidos em diferentes corretoras e instituições financeiras. Os relatórios exportados pelo portal são a fonte primária de ingestão de dados para o Dashboard B3.

---

## 1. Relatórios Suportados e Complementaridade

Os relatórios possuem naturezas distintas e complementares:

- **Movimentação (Eventos no Tempo):** Registro cronológico de operações (compras, vendas, transferências e proventos recebidos/creditados). Contrato detalhado em [movimentacao_b3_xlsx.md](movimentacao_b3_xlsx.md).
- **Posição em Custódia (Fotografia / Snapshot):** Saldo patrimonial em uma data de corte de referência, organizado normalmente em abas por classe de ativo. Contrato detalhado em [posicao_b3_xlsx.md](posicao_b3_xlsx.md).

> [!IMPORTANT]
> **Regra Antiduplicação (SSoT):** Nunca some a posição em custódia diretamente às movimentações históricas como se fosse um novo evento de compra. A posição serve como snapshot de validação, cálculo de patrimônio a mercado e reconciliação dos saldos derivados do histórico.

---

## 2. Pipeline de Processamento e Enriquecimento Canônico

O processamento dos arquivos segue um pipeline estrito de normalização e enriquecimento:

```
Arquivo B3 (.xlsx / .csv)
       │
       ▼
[dashboard.loaders] ── Normalização de colunas (ALIASES_MOV / ALIASES_POS)
       │             ── Parsing monetário e quantitativo (parse_money, parse_qtd)
       ▼
[dashboard.models.ativos.anotar_ativos]
       │             ── Resolução do Ticker canônico (`ativo`)
       │             ── Atribuição do `AtivoId(classe, codigo)`
       │             ── Registro de inconsistências no `RelatorioQualidade`
       ▼
[dashboard.state.DashboardState] (SSoT dos dados calculados)
       ├── Métricas de P&L, Dividend Yield e Proventos
       ├── Alocação Macro (Bolsa de Valores vs Tesouro Direto)
       └── Alocação Dinâmica nas 5 Classes de Ativos
```

### Classificação e 5 Classes de Ativos
A carteira é agregada dinamicamente tanto em nível **Macro** quanto em **5 Classes de Ativos**:
1. **Ações** (Ações nacionais listadas na B3)
2. **BDRs** (Brazilian Depositary Receipts)
3. **Tesouro Pós-fixado** (Tesouro Selic)
4. **Tesouro Inflação** (Tesouro IPCA+ / Educa+)
5. **Tesouro Prefixado** (Tesouro Prefixado com e sem juros semestrais)

---

## 3. Relatório de Qualidade de Dados (`RelatorioQualidade`)

Durante a ingestão, o sistema audita proativamente anomalias sem interromper a execução da aplicação:
- `ATIVO_DESCONHECIDO`: Produto não encontrado no catálogo canônico (`CATALOGO_ATIVOS`).
- `CLASSE_DIVERGENTE`: Quando a aba da planilha de posição (ex.: `BDR`) diverge da classe cadastrada do ativo (ex.: `AÇÕES`).

---

## 4. Guia Operacional para IA e Desenvolvedores

Ao trabalhar neste repositório (refatorando, criando novos gráficos ou atualizando loaders):

### Comando Canônico de Testes (Rápido e Conciso)
Sempre execute os testes unitários utilizando o comando no ambiente virtual:

```powershell
.\.venv\Scripts\pytest -q --tb=short
```

### Fluxo Ideal de Refatoração (Obrigatório)
1. **Proteja:** Verifique/crie os testes unitários cobrindo o comportamento atual antes de qualquer alteração estrutural.
2. **Isole a Verdade (SSoT):** Identifique regras duplicadas e centralize-as em uma única estrutura ou módulo; ajuste os testes para refletir essa centralização.
3. **Elimine a Duplicação (DRY):** Limpe redundâncias tanto no código de teste quanto no código de produção.
4. **Divida (SRP):** Quebre funções e classes grandes em componentes coesos de responsabilidade única, validando cada etapa com a execução contínua de:
   ```powershell
   .\.venv\Scripts\pytest -q --tb=short
   ```