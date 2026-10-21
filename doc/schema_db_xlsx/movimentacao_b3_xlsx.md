# Schema de Movimentação B3 (CSV / XLSX)

## 1. Finalidade

Descreve o contrato de dados consumido e processado pelo loader [`dashboard/loaders/movimentacao.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/dashboard/loaders/movimentacao.py). O relatório de movimentação representa eventos operacionais cronológicos da carteira (compras, vendas, transferências e proventos creditados). Cada linha válida corresponde a uma movimentação individual.

O loader suporta tanto arquivos **CSV** quanto planilhas **Excel (.xlsx)** com múltiplas abas.

> [!IMPORTANT]
> Para a especificação técnica completa de arquitetura, regras de negócio aprofundadas e árvores de decisão de cada parser, consulte:
> [`doc/arq_movimentacao_b3_padronizacao.md`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/doc/arq_movimentacao_b3_padronizacao.md)

---

## 2. Colunas de Entrada (Normalização via `ALIASES_MOV`)

Os cabeçalhos brutos da B3 são normalizados automaticamente em [`dashboard/aliases/movimentacao.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/dashboard/aliases/movimentacao.py) com decodificação Unicode NFKD (remove acentos, unifica caixa e espaços):

| Coluna Canônica | Cabeçalho B3 Reconhecido | Obrigatória | Tipo Destino | Interpretação |
| :--- | :--- | :---: | :---: | :--- |
| `entrada_saida` | `Entrada/Saída`, `Entrada/Saida` | **Sim** | `str` | Direção do lançamento: `credito` (adiciona) ou `debito` (subtrai). |
| `data` | `Data` | **Sim** | `datetime64` | Data da operação (`DD/MM/AAAA` ou formato ISO flexível). Datas inválidas → `NaT`. |
| `movimentacao` | `Movimentação`, `Movimentacao` | **Sim** | `str` | Tipo do evento: Compra, Venda, Dividendo, JCP, Rendimento, etc. |
| `produto` | `Produto` | **Sim** | `str` | Descrição completa ou ticker informado no relatório B3. Fallback: `"Sem nome"`. |
| `instituicao` | `Instituição`, `Instituicao` | **Sim** | `str` | Corretora ou instituição financeira. Fallback: `"Sem instituição"`. |
| `quantidade` | `Quantidade` | **Sim** | `float` | Quantidade movimentada via `parse_qtd`. Suporta frações do Tesouro Direto (`0,12`). |
| `preco_unitario` | `Preço unitário`, `Preco unitario` | **Sim** | `float` | Preço de execução por unidade via `parse_money`. |
| `valor_operacao` | `Valor da Operação`, `Valor da Operacao` | **Sim** | `float` | Valor financeiro total da operação via `parse_money`. |

> Se faltar qualquer coluna obrigatória após a normalização, o loader lança `ValueError` detalhando as colunas ausentes. Abas XLSX sem o conjunto mínimo são descartadas silenciosamente.

---

## 3. Formatos Suportados e Tratamento Numérico

### 3.1 Formatos de Arquivo

| Formato | Detalhes |
| :--- | :--- |
| **CSV** | Delimitador `;`, vírgula como separador decimal. Decodificação em cadeia: `utf-8-sig` (BOM) → `latin-1`. |
| **Excel (.xlsx / .xls)** | Motor exclusivo `openpyxl` (calamine banido). Todas as abas são varridas. Abas vazias ou fora do schema são descartadas. |

### 3.2 Parsers Numéricos — SSoT: `dashboard/utils.py`

Ambas as funções residem em [`dashboard/utils.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/dashboard/utils.py) — essa é a **Single Source of Truth**. Os loaders importam e re-exportam esses símbolos; testes que importam de `dashboard.loaders.movimentacao` acessam o mesmo objeto.

#### `parse_money(value)` — Valores Monetários

Converte qualquer representação textual monetária para `float` Python:

| Entrada | Saída | Caso de Uso |
| :--- | :---: | :--- |
| `"R$ 1.234,56"` | `1234.56` | Exportação padrão da B3 |
| `"1.234,56"` | `1234.56` | BR: ponto=milhar, vírgula=decimal |
| `"1,234.56"` | `1234.56` | US: vírgula=milhar, ponto=decimal |
| `"(1.234,56)"` | `-1234.56` | Notação contábil de débito |
| `"USD 42.50"` | `42.5` | BDR cotado em dólar |
| `"R$ 0,00"` | `0.0` | Operação zerada |
| `30.78` (`float`) | `30.78` | Tipo nativo — curto-circuito |
| `None` / `""` | `pd.NA` | Nulo ou célula vazia |

> **Heurística de vírgula única:** se o bloco após a vírgula tiver ≤ 2 dígitos → decimal (`"102,5"` → `102.5`); se tiver 3+ dígitos → milhar (`"1,000"` → `1000.0`).

#### `parse_qtd(value)` — Quantidades

> [!IMPORTANT]
> **Diferença crítica vs. `parse_money`:** Para quantidades, a vírgula é **sempre** tratada como separador decimal, independente do número de dígitos após ela. A B3 nunca exporta quantidades com vírgula como separador de milhar.
>
> - `parse_money("1,000")` → `1000.0` (milhar US, 3 dígitos)
> - `parse_qtd("1,000")` → `1.0` (decimal, vírgula = sempre decimal)

| Entrada | Saída | Classe de Ativo |
| :--- | :---: | :--- |
| `"0,12"` | `0.12` | Tesouro Direto (fração de título) |
| `"0,05"` | `0.05` | Tesouro Direto |
| `"100"` | `100.0` | Ações / BDR / FII |
| `"-5"` | `-5.0` | Saída por venda |
| `"1.000"` | `1.0` | ⚠ Limitação: ponto único interpretado como decimal |
| `None` / `""` | `pd.NA` | Nulo ou célula vazia |

> **Limitação documentada:** `parse_qtd("1.000")` retorna `1.0` (decimal), não `1000.0`. Isso é aceito pois extratos reais da B3 nunca geram quantidades com ponto de milhar.

### 3.3 Parsing de Datas

Estratégia em duas tentativas dentro de `_normalize_movimentacao_df`:

1. **Primária:** `format="%d/%m/%Y"` com `dayfirst=True` — padrão brasileiro.
2. **Fallback:** `format="mixed"` com `dayfirst=True` — resolve datas em formatos ISO ou mistos remanescentes.

Datas não parseáveis em ambas as tentativas são convertidas para `NaT`.

---

## 4. Colunas Produzidas e Enriquecidas

Após a validação e tipagem, o DataFrame é enriquecido com colunas derivadas e de identidade canônica:

| Coluna | Tipo | Regra de Cálculo / Origem | Exemplo |
| :--- | :---: | :--- | :--- |
| `sinal` | `int` | `entrada_saida.map(SINAL_ENTRADA_SAIDA).fillna(0)`: `credito=1`, `debito=-1`, desconhecido=`0` | `1` |
| `qtd_liquida` | `float` | `quantidade * sinal` | `10.0` (compra) / `-5.0` (venda) |
| `valor_liquido` | `float` | `valor_operacao * sinal` | `300.00` |
| `mes` | `str` | `data.dt.to_period("M").astype(str)` | `"2026-08"` |
| `ativo` | `str` | Código canônico via `anotar_ativos` + `CATALOGO_ATIVOS` | `"PETR4"`, `"Tesouro Selic 2029"` |
| `ativo_id` | `AtivoId` | Objeto de valor imutável `AtivoId(classe, codigo)` | `AtivoId(classe='AÇÕES', codigo='PETR4')` |

### API Pública do Loader

| Função | Assinatura | Descrição |
| :--- | :--- | :--- |
| `read_movimentacao_file` | `(source, qualidade=None) → DataFrame` | Ponto de entrada principal — detecta CSV ou XLSX pelo sufixo/nome. |
| `read_movimentacao_excel` | `(source, qualidade=None) → DataFrame` | Leitura direta de XLSX com varredura de abas. |
| `read_movimentacao_csv` | `(source, qualidade=None) → DataFrame` | Leitura direta de CSV com fallback de encoding. |
| `load_movimentacao` | `(source, qualidade=None) → DataFrame` | Alias de `read_movimentacao_file` para compatibilidade retroativa. |

### Auditoria de Qualidade (`RelatorioQualidade`)

Durante o enriquecimento via `anotar_ativos`, produtos não encontrados no `CATALOGO_ATIVOS` recebem `Classe.DESCONHECIDO` e geram um aviso `ATIVO_DESCONHECIDO` no `RelatorioQualidade` — sem interromper a execução.

---

## 5. Exemplo Conceitual

**Entrada (Linha da B3):**
```text
Entrada/Saída: Credito | Data: 06/08/2026 | Movimentação: Compra
Produto: PETR4 - PETROLEO BRASILEIRO S.A. | Instituição: XP INVESTIMENTOS
Quantidade: 10 | Preço unitário: 30,00 | Valor da Operação: 300,00
```

**Saída Processada (DataFrame Canônico):**
```text
entrada_saida: "credito"  | data: 2026-08-06   | movimentacao: "compra"
produto: "PETR4 - PETROLEO BRASILEIRO S.A."    | instituicao: "XP INVESTIMENTOS"
quantidade: 10.0          | preco_unitario: 30.0 | valor_operacao: 300.0
sinal: 1  | qtd_liquida: 10.0  | valor_liquido: 300.0  | mes: "2026-08"
ativo: "PETR4"  | ativo_id: AtivoId(classe='AÇÕES', codigo='PETR4')
```

---

## 6. Diretrizes para IA e Desenvolvedores

Ao trabalhar neste loader, pipelines derivados ou métricas de movimentação:

### Comando Canônico de Testes
```powershell
.\.venv\Scripts\pytest -q --tb=short
```

### Testes de Regressão Críticos para este Módulo

| Arquivo de Teste | Cobre |
| :--- | :--- |
| [`tests/test_xlsx_priority.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_xlsx_priority.py) | Prioridade XLSX > CSV, engine openpyxl, arquivos corrompidos |
| [`tests/test_quantidade_tesouro.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_quantidade_tesouro.py) | `parse_qtd` frações Tesouro (0,01..0,99), loaders integrados |
| [`tests/test_file_selection.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_file_selection.py) | `parse_money` com 19+ casos reais de entrada, `find_latest` |
| [`tests/test_default_loader.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_default_loader.py) | `load_default` — busca em diretórios, propagação de erros |
| [`tests/test_b3_metrics.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_b3_metrics.py) | Métricas derivadas das movimentações lidas |

### Princípios de Arquitetura

- **SSoT dos Parsers:** `parse_money` e `parse_qtd` vivem exclusivamente em `dashboard/utils.py`. Não reimplemente lógica de parsing nos loaders ou views.
- **SSoT de Sinais:** `SINAL_ENTRADA_SAIDA` pertence a `dashboard/models/movimentacao.py`. O loader importa e aplica; não redefine.
- **SRP do Loader:** O loader apenas **extrai**, **normaliza** e **enriquece** com identidade canônica. Cálculos acumulados (preço médio, P&L, posição) pertencem a `dashboard.metrics` e `dashboard.state_pipeline`.
- **DRY:** Reutilize `_normalize_movimentacao_df` para qualquer nova fonte de dados no mesmo formato. Não duplique a lógica de validação de schema.
- **Nunca use calamine:** O motor é `openpyxl` — validado em teste de regressão. A dependência calamine está banida do `requirements.txt`.
