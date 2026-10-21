# Schema de Proventos Recebidos B3 (XLSX)

## 1. Finalidade

Descreve o contrato de dados consumido e processado pelo loader [`dashboard/loaders/proventos_recebidos.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/dashboard/loaders/proventos_recebidos.py). O relatório de proventos recebidos representa o extrato detalhado de proventos (dividendos, JCP, rendimentos de FIIs, amortizações e juros de títulos públicos) creditados em conta, extraído diretamente da Área do Investidor da B3.

O arquivo típico possui o padrão de nomenclatura `proventos-recebidos-*.xlsx` e contém uma aba principal denominada `Proventos Recebidos`.

---

## 2. Colunas de Entrada (Normalização via `ALIASES_PROV_RECEBIDOS`)

Os cabeçalhos brutos da planilha B3 são mapeados para nomes canônicos sem diferenciar maiúsculas/minúsculas, acentos ou espaços:

| Coluna Canônica | Cabeçalho B3 Reconhecido | Obrigatória | Tipo Destino | Interpretação |
| :--- | :--- | :---: | :---: | :--- |
| `produto` | `Produto` | **Sim** | `str` | Descrição do ativo (ex.: `PETR4 - PETROLEO BRASILEIRO S/A PETROBRAS`, `Tesouro Educa+ 2026`). Linhas nulas ou de total são descartadas. |
| `data_pagamento` | `Pagamento`, `Data do Pagamento`, `Data Pagamento` | **Sim** | `datetime64` | Data em que o provento foi efetivamente creditado (`DD/MM/AAAA`). |
| `tipo_evento` | `Tipo de Evento`, `Tipo`, `Evento` | **Sim** | `str` | Natureza do provento: `Dividendo`, `Juros Sobre Capital Próprio`, `Rendimento`, `Amortização`, `Juros`. |
| `instituicao` | `Instituição`, `Instituicao` | **Sim** | `str` | Corretora ou instituição financeira onde o provento foi creditado. |
| `quantidade` | `Quantidade` | **Sim** | `float` | Quantidade de cotas/ações detidas na data com (suporta fracionários para Tesouro, ex.: `0,13`). |
| `preco_unitario` | `Preço unitário`, `Preco unitario` | **Sim** | `float` | Valor unitário bruto do provento pago por cota/ação via `parse_money`. |
| `valor_liquido` | `Valor líquido`, `Valor liquido` | **Sim** | `float` | Valor financeiro total líquido creditado na conta via `parse_money`. |

---

## 3. Particularidades da B3 e Limpeza de Totais

A exportação da B3 possui as seguintes características no final da tabela:
1. **Linhas Vazias:** Linhas onde todas as colunas ou `Produto` são nulos.
2. **Linha de Rótulo Total:** Uma linha no rodapé onde a coluna `Valor líquido` contém a string `"Total"` e as demais colunas são nulas.
3. **Linha de Somatório:** A linha seguinte onde `Valor líquido` contém a soma total dos proventos do período (ex.: `313.15`).

**Regra de Descarte:** O loader deve descartar qualquer linha onde:
- `produto` seja nulo, vazio, hífen (`-`) ou contenha `"Total"`.
- `valor_liquido` seja o texto `"Total"` ou não seja conversível em valor numérico válido.

---

## 4. Tipagem e Tratamento Numérico

- **Datas:** Convertidas para `pd.Timestamp` via `pd.to_datetime(col, format="%d/%m/%Y", errors="coerce")`.
- **Quantidades:** Tratadas via `parse_qtd`, permitindo decimais com vírgula (ex.: `"0,13"` ➔ `0.13`).
- **Valores Monetários:** Tratados via `parse_money` (ex.: `"R$ 10,33"` ou `10.33` ➔ `10.33`).

---

## 5. Colunas Enriquecidas Produzidas pelo Loader

O loader enriquece o DataFrame com metadados padronizados para integração no dashboard e reconciliação:

| Coluna | Regra de Transformação / Origem |
| :--- | :--- |
| `ticker` / `ativo` | Ticker canônico extraído via `anotar_ativos(df)` (ex.: `PETR4`, `VALE3`, `Tesouro Educa+ 2026`). |
| `tipo_provento` | Padronização via `classificar_tipo_provento(tipo_evento)` (ex.: `"Dividendo"`, `"JCP"`, `"Rendimento FII"`). |
| `data` | Cópia de `data_pagamento` em formato `datetime64[ns]` para compatibilidade de filtros temporais. |
| `mes` | Ano-mês no formato `AAAA-MM` derivado de `data_pagamento`. |
| `ano` | Ano numérico (`int`) derivado de `data_pagamento`. |

---

## 6. Papel na Reconciliação (Fase 6.4)

O DataFrame produzido por este loader é comparado com os lançamentos de proventos extraídos de `dashboard/loaders/movimentacao.py`:
- **Consistência de Valores:** A soma dos proventos por ativo e mês no extrato deve bater com as movimentações de crédito.
- **Auditoria de Eventos:** Detecta eventos presentes no extrato mas ausentes na movimentação (ou vice-versa).
