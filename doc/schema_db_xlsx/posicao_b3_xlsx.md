# Schema de Posição B3 (XLSX)

## 1. Finalidade

Descreve o contrato de dados consumido e processado pelo loader `dashboard/loaders/posicao.py`. O relatório de posição representa um **snapshot (fotografia pontual)** dos ativos mantidos em custódia em uma data de referência específica. Não representa um fluxo contínuo de eventos, mas sim os saldos finais e valores a mercado.

O loader lê todas as abas da planilha Excel (`.xlsx`), filtra cabeçalhos ou linhas de totais e concatena os registros válidos em um DataFrame unificado.

---

## 2. Colunas de Entrada (Normalização via `ALIASES_POS`)

Os cabeçalhos brutos da planilha B3 são mapeados para nomes canônicos sem diferenciar maiúsculas/minúsculas, acentos ou espaços:

| Coluna Canônica | Cabeçalho B3 Reconhecido | Obrigatória | Tipo | Observação |
| :--- | :--- | :---: | :---: | :--- |
| `produto` | `Produto` | **Sim** | `str` | Descrição do ativo. Linhas vazias, `-` ou `Total` são descartadas. |
| `data_posicao` | `Data da posição`, `Data da posicao` | Não | `date` | Data de referência do snapshot de custódia. |
| `instituicao` | `Instituição`, `Instituicao` | Não | `str` | Instituição custodiante (corretora). |
| `conta` | `Conta` | Não | `str` | Número da conta na instituição. |
| `codigo_negociacao` | `Código de Negociação`, `Codigo de Negociacao` | Não | `str` | Ticker de negociação informado pela B3. |
| `cnpj_empresa` | `CNPJ da Empresa` | Não | `str` | CNPJ do emissor do ativo. |
| `codigo_isin` | `Código ISIN / Distribuição` | Não | `str` | Código ISIN internacional do título. |
| `tipo` | `Tipo` | Não | `str` | Subtipo de ativo (ex.: ON, PN, CI). |
| `escriturador` | `Escriturador` | Não | `str` | Instituição escrituradora do ativo. |
| `quantidade` | `Quantidade` | Não | `float` | Quantidade total em custódia (inteira ou fracionária). |
| `quantidade_disponivel` | `Quantidade Disponível` | Não | `float` | Quantidade livre para negociação. |
| `quantidade_indisponivel` | `Quantidade Indisponível` | Não | `float` | Quantidade bloqueada (garantias, aluguel, etc.). |
| `motivo` | `Motivo` | Não | `str` | Motivo de eventual bloqueio ou indisponibilidade. |
| `preco_fechamento` | `Preço de Fechamento` | Não | `float` | Cotação de fechamento no dia da posição. |
| `valor_atualizado` | `Valor Atualizado` | Não | `float` | Saldo financeiro a mercado informado pela B3. |
| `categoria` | `Categoria` | Não | `str` | Substituída pela categoria inferida da aba. |

---

## 3. Classificação Automática por Abas da Planilha

O nome da aba na planilha da B3 define a `categoria` primária da custódia (`_categorizar_sheet`):
- Abas cujo nome contenha `tesouro` (case-insensitive) ➔ `TESOURO`
- Abas cujo nome contenha `bdr` (case-insensitive) ➔ `BDR`
- Todas as demais abas válidas contendo a coluna `Produto` ➔ `AÇÕES`

---

## 4. Colunas Produzidas e Enriquecimento Canônico

O loader padroniza os campos para torná-los compatíveis com o modelo unificado de carteira:

| Coluna | Regra de Transformação / Origem |
| :--- | :--- |
| `categoria` | Categoria calculada a partir do nome da aba (`AÇÕES`, `BDR` ou `TESOURO`). |
| `valor_operacao` | `valor_atualizado` tratado por `parse_money` (saldo financeiro atual). |
| `quantidade` | `quantidade` tratada por `parse_qtd` (aceita fracionários para Tesouro). |
| `valor_liquido` | Cópia de `valor_operacao` (saldo financeiro positivo). |
| `qtd_liquida` | Cópia de `quantidade`. |
| `entrada_saida` | Constante `'credito'` (para fins de agregação compatível). |
| `movimentacao` | Constante `'posicao'`. |
| `data_posicao` | Data do snapshot. Se ausente, preenche com a data atual normalizada. |
| `data` | Cópia de `data_posicao`. |
| `mes` | Mês de referência no formato `AAAA-MM`. |
| `ativo` | Ticker canônico resolvido via `anotar_ativos()` (ex.: `PETR4`, `ROXO34`, `Tesouro IPCA+ 2026`). |
| `ativo_id` | Instância `AtivoId(classe, codigo)` gerada pelo catálogo canônico. |

---

## 5. Auditoria de Qualidade & Detecção de Divergências

Ao final da carga, o loader executa auditoria via `dashboard.models.qualidade`:
- **`ATIVO_DESCONHECIDO`:** Disparado caso algum produto não conste no `CATALOGO_ATIVOS`.
- **`CLASSE_DIVERGENTE`:** Disparado se a categoria da aba (ex.: `AÇÕES`) for inconsistente com a classe real do ativo cadastrado no catálogo (ex.: `BDR` ou `TESOURO`).

---

## 6. Agrupamento em 5 Classes de Ativos & Visão Macro

A partir do DataFrame de posição, o dashboard deriva duas camadas essenciais de visualização:

1. **Alocação Macro (Bolsa vs Tesouro):**
   - **Bolsa de Valores:** Soma de Ações e BDRs.
   - **Tesouro Direto:** Títulos públicos federais de Renda Fixa.
   - Apresentado com métricas de P&L e gráfico de rosquinha (donut) padronizado.

2. **5 Classes de Ativos (`calcular_alocacao_5_classes`):**
   - Ações
   - BDRs
   - Tesouro Pós-fixado (Selic)
   - Tesouro Inflação (IPCA+ e Educa+)
   - Tesouro Prefixado (com e sem juros semestrais)

---

## 7. Diretrizes para IA e Desenvolvedores

Ao trabalhar neste loader, modelos de ativos ou visualizações de custódia:

1. **Comando de Testes Canônico (Rápido e Conciso):**
   ```powershell
   .\.venv\Scripts\pytest -q --tb=short
   ```
2. **Ciclo de Desenvolvimento:**
   - **Proteja:** Mantenha testes de regressão em `test_position_metrics.py`, `test_position_classification.py` e `test_quantidade_tesouro.py`.
   - **SSoT:** A classificação em classes e 5 classes pertence unicamente a `dashboard/models/categorias.py` e `dashboard/models/identidade.py`.
   - **DRY:** Reutilize `_categorizar_sheet`, `anotar_ativos` e os utilitários de parsing.
   - **SRP:** O loader apenas carrega e enriquece a posição; o estado consolidado é construído exclusivamente pelo `DashboardState.build()`.
