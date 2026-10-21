# Especificação Técnica de Arquitetura: Ingestão e Tratamento de Movimentações B3 (XLSX)

**Documento:** Especificação Técnica de Engenharia de Dados e Arquitetura de Software  
**Módulo Alvo:** `dashboard/loaders/movimentacao.py`, `dashboard/models/`, `dashboard/aliases/`, `dashboard/metrics/`  
**Destino:** `doc/arq_movimentacao_b3_padronizacao.md`  
**Status:** Canônico / "A Verdade do Código"  

---

## 1. Visão Geral e Fluxo de Ingestão

### 1.1 Contexto de Negócio e Origem dos Dados
A Área do Investidor da B3 (antigo CEI - Canal Eletrônico do Investidor) é a câmara oficial centralizadora de custódia e liquidação de ativos do mercado financeiro brasileiro. Os investidores exportam relatórios periódicos em formato de planilha para acompanhar o histórico transacional consolidado de múltiplas corretoras e agentes de custódia.

No ecossistema da aplicação, o extrato de **Movimentação** é a fonte canônica cronológica de fatos geradores (ledger transacional de eventos). Ele registra toda e qualquer mutação patrimonial ocorrida no tempo:
- Operações de mercado (compras e vendas no mercado à vista e fracionário).
- Eventos de custódia e transferências (transferências de custódia, liquidações, amortizações, resgates).
- Eventos em dinheiro (proventos recebidos: dividendos, Juros sobre Capital Próprio - JCP, rendimentos de fundos imobiliários).
- Eventos corporativos em ativos (desdobramentos, grupamentos, bonificações, frações em leilão).

### 1.2 Portas de Entrada no Sistema
O arquivo XLSX de movimentação entra no sistema por duas vias complementares:

```
                  ┌────────────────────────────────────────┐
                  │ Interface Streamlit (dashboard/app.py) │
                  └──────────────────┬─────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
        [Upload Interativo]                     [Carga em Disco/Batch]
    st.sidebar.file_uploader              find_latest(folder, "movimentacao")
   (BytesIO / UploadedFile)                Varredura hierárquica em pastas:
                 │                         1. xlsx/movimentacao/
                 │                         2. xlsx/
                 │                         3. csv/
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                     read_movimentacao_file(source)
                                     │
                ┌────────────────────┴────────────────────┐
                │ Detecta sufixo .xlsx / .xls ou stream?  │
                └────────────────────┬────────────────────┘
                       Sim           │           Não
                        ┌────────────┴────────────┐
                        ▼                         ▼
              read_movimentacao_excel    read_movimentacao_csv
              (engine="openpyxl")        (utf-8-sig / latin-1)
```

1. **Ingestão Interativa (Streamlit UI):**  
   Via widget `st.sidebar.file_uploader("Movimentação (XLSX)", type=["xlsx", "xls"], key="movimentacao")`. O arquivo trafega na memória da sessão como um `BytesIO` (`UploadedFile`).
2. **Descoberta Automática de Arquivo Padrão (`find_latest` em `dashboard/utils.py`):**  
   Quando o usuário não realiza upload interativo, a rotina `load_default_movimentacao()` executa uma busca determinística nos seguintes diretórios relativos à raiz do projeto:
   1. `xlsx/movimentacao`
   2. `xlsx`
   3. `csv`

### 1.3 Regras de Priorização e Seleção de Arquivo
A função `find_latest(folder, prefix)` implementa um algoritmo estrito de desempate e segurança:
- **Exclusão de Locks Temporários:** Arquivos cujo nome inicia com `~$` (arquivos de lock temporários gerados pelo Microsoft Excel) são ignorados sumariamente para evitar exceções de concorrência ou I/O incompleto.
- **Prioridade Absoluta XLSX:** Caso coexistam arquivos `.xlsx`/`.xls` e `.csv` no mesmo diretório, o sistema filtra e descarta os arquivos `.csv`, elegendo exclusivamente os arquivos Excel (`.xlsx` é prioritário).
- **Critério de Desempate Temporal:** A ordenação dos candidatos utiliza a tupla determinística:
  $$\text{Chave} = (\text{Data extraída do nome } (AAAA, MM, DD), \text{timestamp de modificação do SO } (\text{mtime}), \text{nome do arquivo})$$
  Isso garante que arquivos nomeados como `movimentacao-2026-10-17.xlsx` tenham precedência absoluta sobre `movimentacao-2026-10-15.xlsx`.

### 1.4 Diretriz de Dependências: Banimento do Calamine
Por decisão arquitetural estrita e validada por teste de regressão em `tests/test_xlsx_priority.py`:
- O motor de leitura de Excel é invocado explicitamente com `engine="openpyxl"`.
- A dependência `calamine` foi **banida** do projeto (`assert "calamine" not in requirements.txt`), evitando problemas de compilação em ambientes Windows restritos e eliminando binários C/Rust desnecessários para a volumetria típica de arquivos da B3.

---

## 2. Abstração de CRUD sobre o XLSX

O arquivo Excel de movimentação da B3 atua na arquitetura como um **Log Imutável Append-Only (Event Store)**. O sistema não utiliza o arquivo como um banco relacional bidirecional mutável, mas sim como um repositório imutável de eventos passados onde operações CRUD são mapeadas sob o paradigma de **Event Sourcing Contábil**.

### 2.1 Read (Leitura, Parsing e Varredura de Abas)
A leitura implementada em `read_movimentacao_excel` em `dashboard/loaders/movimentacao.py` executa os seguintes passos:

1. **Instanciação do Motor de Planilha:**
   ```python
   xls = pd.ExcelFile(file_source, engine="openpyxl")
   ```
2. **Varredura Polimórfica de Abas (Multi-Sheet Scanning):**  
   Diferente do extrato de posição (onde cada aba representa uma classe de ativo, como *Ações*, *BDR*, *Tesouro Direto*), o extrato de movimentação pode vir distribuído em uma ou várias abas (ex.: movimentações por ano, por conta ou consolidadas).
3. **Extração Isenta de Tipagem Precoce (`dtype=object`):**  
   Cada aba é parseada com `xls.parse(sheet_name, dtype=object)` para impedir que o pandas faça coerções automáticas indesejadas (por exemplo, converter tickers alfanuméricos em números ou formatar datas incorretamente).
4. **Descarte de Abas Vazias e Inválidas:**  
   - Linhas totalmente nulas são eliminadas imediatamente via `df.dropna(how="all")`.
   - Se a aba estiver vazia após a remoção de linhas nulas, ela é ignorada.
   - A aba passa pelo pipeline de validação estrutural (`_normalize_movimentacao_df`). Se faltar qualquer uma das colunas obrigatórias, o bloco `try/except ValueError` captura a falha e descarta a aba silenciosamente (`continue`).
5. **Concatenação e Integridade Mínima:**  
   As abas válidas são empilhadas em memória com `pd.concat(frames, ignore_index=True)`. Se nenhuma aba estruturada for identificada, o sistema levanta uma exceção fatal:
   ```python
   raise ValueError("Nenhuma aba com o formato de movimentação foi lida corretamente.")
   ```

### 2.2 Create / Insert (Ingestão de Novos Eventos)
Novas movimentações inseridas pelo usuário (seja via novo arquivo XLSX ou via linhas adicionadas à planilha) entram no ecossistema passando por um portão de validação estrita (gatekeeper) definido em `_normalize_movimentacao_df`:

```
Linha Bruta (Excel)
       │
       ▼
Strip nos Nomes de Coluna: [str(c).strip() for c in df.columns]
       │
       ▼
Normalização de Aliases: normaliza_colunas(df, ALIASES_MOV)
       │
       ▼
Validação de Schema Obrigatório:
required = {"entrada_saida", "data", "movimentacao", "produto",
            "instituicao", "quantidade", "preco_unitario", "valor_operacao"}
       │
       ├── Falta coluna? ──► Lança ValueError("Colunas ausentes...")
       │
       ▼
Instanciação do Dataclass: Movimentacao.from_row(row)
```

- Cada tupla é materializada em memória ou consumida diretamente no `DataFrame` vetorizado com todas as colunas canônicas tipadas.
- O sistema calcula e injeta de forma determinística os atributos derivados de posição e fluxo de caixa:
  - `sinal`: direção multiplicadora ($+1$ para crédito, $-1$ para débito).
  - `qtd_liquida`: $\text{quantidade} \times \text{sinal}$.
  - `valor_liquido`: $\text{valor\_operacao} \times \text{sinal}$.
  - `mes`: discretização temporal no padrão `AAAA-MM` (`PeriodIndex`).

### 2.3 Update / Delete (Estornos, Cancelamentos e Imutabilidade)
No domínio de engenharia financeira e contábil, **dados transacionais de extrato nunca devem ser atualizados (`UPDATE`) ou deletados (`DELETE`) de forma destrutiva**.

A B3 implementa cancelamentos e correções através de **eventos de contrapartida (compensação)**. A arquitetura reflete essa regra com precisão cirúrgica:

1. **Fonte da Verdade em Disco é Read-Only:**  
   O arquivo físico XLSX nunca é regravado ou modificado pelo sistema. Isso preserva a auditabilidade forense do extrato original fornecido pela câmara de liquidação.
2. **Atualizações de Posição via Eventos Cumulativos:**  
   Não existe `UPDATE` em uma movimentação. Se uma quantidade mudou devido a um grupamento ou evento de liquidação, um novo registro contábil de ajuste é processado na linha do tempo.
3. **Cancelamentos e Estornos como Contrapartida Contábil:**  
   - Se um dividendo provisionado for suspenso ou retificado pela assembleia da empresa, a B3 emite uma linha:  
     `movimentacao="dividendo - cancelado"` com `entrada_saida="debito"`.
   - O catálogo canônico de eventos (`dashboard/models/efeitos.py`) mapeia essa linha para `TipoMovimentacao.PROVENTO` com efeito financeiro de compensação (`semantica_quantidade=SemanticaQuantidade.NENHUMA`, `eh_provento=False`).
   - Leilões e frações residuais de grupamento geram linhas de `"fracao em ativos"` (`debito`) e posterior `"leilao de fracao"` (`credito`), compensando as quantidades em carteira sem violar a integridade referencial.
4. **Regra de Esvaziamento no Motor de Custódia (`PosicaoAcumulada`):**  
   Quando ocorrem vendas ou transferências de saída que liquidam totalmente o ativo:
   ```python
   def reduzir(self, qtd_removida: float) -> None:
       if self.quantidade <= 0 or qtd_removida >= self.quantidade:
           self.zerar()
           return
       custo_unitario = self.custo_total / self.quantidade if self.quantidade else 0.0
       self.custo_total -= qtd_removida * custo_unitario
       self.quantidade -= qtd_removida
   ```
   A deleção lógica da custódia é uma consequência matemática da redução do saldo a zero ($\text{quantidade} = 0 \implies \text{custo\_total} = 0$).

---

## 3. Engenharia Reversa e Regras de Negócio ("A Verdade do Código")

Esta seção detalha como as regras de negócio reais foram implementadas a partir da inspeção do código-fonte do projeto.

### 3.1 Mapeamento e Classificação de Tipos de Movimentação

A B3 utiliza uma variedade de terminologias históricas nos extratos. Para unificar esses termos, o sistema adota um padrão de normalização em dois níveis:

```
Texto Bruto da B3 (ex: "Rendimento - Pago", "Bonificação em Ativos")
                               │
                               ▼
    normalizar_texto(texto) em dashboard/models/texto.py:
    1. Normalização Unicode NFKD
    2. Conversão para ASCII (eliminação total de acentos)
    3. Hífen unificado: \u2013 e \u2014 substituídos por "-"
    4. Conversão para caixa baixa (.lower())
    5. Compactação de múltiplos espaços em branco em espaço único
                               │
                               ▼
        Busca Exata em CATALOGO_MOVIMENTACOES (dicionário O(1))
                               │
                   ┌───────────┴───────────┐
                Encontrou?               Não encontrou?
                   │                       │
                   ▼                       ▼
            Retorna Enum          Busca por Prefixo Longest-Match
                                  sorted(CATALOGO, key=len, reverse=True)
                                  se normalizado.startswith(chave):
                                      retorna TipoMovimentacao
                                           │
                                           ▼
                                  Se falhar: TipoMovimentacao.DESCONHECIDA
```

#### Tabela Canônica do `CATALOGO_MOVIMENTACOES` (`dashboard/models/movimentacao.py`)

| Texto Normalizado da B3 | `TipoMovimentacao` (Enum) | Grupo Semântico |
| :--- | :--- | :--- |
| `compra` | `TipoMovimentacao.COMPRA` | Operação no Mercado |
| `venda` | `TipoMovimentacao.VENDA` | Operação no Mercado |
| `dividendo` | `TipoMovimentacao.PROVENTO` | Renda Passiva |
| `dividendo - cancelado` | `TipoMovimentacao.PROVENTO` | Estorno de Renda |
| `juros`, `juros sobre capital proprio`, `jcp` | `TipoMovimentacao.PROVENTO` | Renda Passiva Tributável |
| `rendimento` | `TipoMovimentacao.PROVENTO` | Renda Passiva (FIIs) |
| `provento`, `atualizacao` | `TipoMovimentacao.PROVENTO` | Eventos de Renda |
| `desdobro`, `desdobro de acoes`, `split` | `TipoMovimentacao.DESDOBRAMENTO` | Evento Societário |
| `grupamento`, `agrupamento` | `TipoMovimentacao.GRUPAMENTO` | Evento Societário |
| `bonificacao`, `bonificacao em ativos` | `TipoMovimentacao.BONIFICACAO` | Distribuição de Ativos |
| `transferencia`, `transferencia - liquidacao` | `TipoMovimentacao.TRANSFERENCIA` | Custódia / Corretora |
| `liquidacao`, `resgate`, `amortizacao` | `TipoMovimentacao.TRANSFERENCIA` | Liquidação / Renda Fixa |
| `fracao em ativos`, `leilao de fracao` | `TipoMovimentacao.AJUSTE_QUANTIDADE` | Ajustes de Sobras de Ações |
| `direito de subscricao`, `direitos de subscricao - nao exercido` | `TipoMovimentacao.AJUSTE_QUANTIDADE` | Direitos e Opções de Subscrição |
| `ajuste` | `TipoMovimentacao.AJUSTE_QUANTIDADE` | Ajuste Manual |

#### Classificação Específica de Proventos (`classificar_tipo_provento`)
Para alimentar a interface analítica de renda passiva (`dashboard/views/proventos.py`), os eventos do tipo `PROVENTO` são particionados segundo a regra estrita:
- Se contiver `"juros"` ou `"jcp"` $\implies$ **"JCP"** (Juros sobre Capital Próprio, sujeito a 15% de IR retido na fonte).
- Se contiver `"dividendo"` $\implies$ **"Dividendo"** (isentos de IR na pessoa física).
- Se contiver `"rendimento"` ou `"fii"` $\implies$ **"Rendimento FII"** (proventos imobiliários isentos).
- Caso contrário $\implies$ **"Outros"**.

---

### 3.2 Tabela de Efeitos Contábeis e Acumulação de Posição (`dashboard/models/efeitos.py`)

A simples classificação não é suficiente para calcular o Preço Médio e a Posição Histórica. A arquitetura define um contrato rigoroso por meio do dataclass imutável `EfeitoMovimentacao`:

$$\text{Chave} = (\text{TipoMovimentacao / String Normalizada}, \text{Sentido Contábil: 'credito' | 'debito'})$$

```python
class SemanticaQuantidade(str, Enum):
    DELTA = "DELTA"        # Modifica por soma ou subtração relativa à posição anterior
    TOTAL = "TOTAL"        # Sobrescreve/define o total acumulado da posição (Snapshot)
    SNAPSHOT = "SNAPSHOT"  # Ponto de corte estático
    NENHUMA = "NENHUMA"    # Não afeta estoque de ações (ex: dinheiro de dividendos)
```

#### Mapeamento Real de Efeitos do Sistema

| Evento B3 | Sentido | `SemanticaQuantidade` | Efeito Custo | Quantidade Calculada | `eh_provento` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `compra` | `credito` | `DELTA` | `soma` | Soma quantidade e valor ao custo | `False` |
| `venda` | `debito` | `DELTA` | `subtrai` | Subtrai quantidade; abate custo proporcional | `False` |
| `desdobro` | `credito` | `DELTA` | `nenhum` | Soma quantidade; mantém custo inalterado | `False` |
| `grupamento` | `credito` | `TOTAL` | `nenhum` | Define nova quantidade absoluta; mantém custo | `False` |
| `bonificacao` | `credito` | `DELTA` | `nenhum` | Soma novas cotas/ações a custo zero | `False` |
| `transferencia` | `credito` | `DELTA` | `soma` | Adiciona estoque vindo de outra custódia | `False` |
| `transferencia` | `debito` | `DELTA` | `subtrai` | Remove estoque enviado para outra custódia | `False` |
| `amortizacao` | `debito` | `DELTA` | `subtrai` | Amortização de principal (FIIs/Renda Fixa) | `False` |
| `dividendo` | `credito` | `NENHUMA` | `ignora` | Quantidade ignorada; gera fluxo financeiro | `True` |
| `dividendo - cancelado` | `debito` | `NENHUMA` | `ignora` | Quantidade ignorada; estorna financeiro | `False` |
| `juros / jcp` | `credito` | `NENHUMA` | `ignora` | Quantidade ignorada; gera fluxo financeiro | `True` |
| `rendimento` | `credito` | `NENHUMA` | `ignora` | Quantidade ignorada; gera fluxo financeiro | `True` |
| `fracao em ativos` | `debito` | `DELTA` | `nenhum` | Reduz frações que foram a leilão | `False` |
| `leilao de fracao` | `credito` | `NENHUMA` | `nenhum` | Entrada de caixa referente à sobra liquidada | `False` |

---

### 3.3 Tratamento de Inconsistências Reais do Excel

O Microsoft Excel e as exportações web da B3 apresentam desvios de formatação recorrentes. O sistema neutraliza essas anomalias em `dashboard/utils.py` e `dashboard/loaders/movimentacao.py`:

#### A. Tratamento de Células Vazias e Nulas
- **Linhas inteiras em branco:** Removidas por `df.dropna(how="all")`.
- **Campos textuais ausentes:**
  - `produto.fillna("Sem nome")`: Evita erros de chamada de método de string (`.str.strip()`).
  - `instituicao.fillna("Sem instituição")`: Mantém integridade na agregação por corretora.
  - `entrada_saida.fillna("")` e `movimentacao.fillna("")`: Evitam quebras no cálculo de hash ou catálogo.

#### B. Parsing Robusto de Datas (Formatos Mistos e Datas Flutuantes)
As exportações da B3 misturam serialização padrão do Excel (`datetime` nativo), strings formatadas em português (`DD/MM/AAAA`) e padrões ISO (`AAAA-MM-DD`). O código aplica uma estratégia de parsing em duas etapas:

```python
raw_data = df["data"].astype(str).str.strip()
# 1. Tentativa primária determinística com padrão brasileiro (dia primeiro)
df["data"] = pd.to_datetime(raw_data, format="%d/%m/%Y", dayfirst=True, errors="coerce")

# 2. Fallback resiliente para datas em formatos mistos remanescentes
if df["data"].isna().any() and not raw_data.empty:
    df["data"] = df["data"].fillna(
        pd.to_datetime(raw_data, format="mixed", dayfirst=True, errors="coerce")
    )
```

#### C. Sanitização Monetária e Notações Contábeis — Estudo Aprofundado

Esta seção aprofunda a camada de parsing monetário do sistema, cobrindo a **arquitetura em dois níveis** (entrada e saída), a **árvore de decisão exaustiva** com todos os casos reais cobertos em testes e as **armadilhas inerentes** ao formato B3.

---

##### C.1 Arquitetura Dual: Parsing de Entrada vs. Formatação de Saída

O sistema mantém **duas funções distintas e complementares** para lidar com valores monetários:

| Camada | Função | Módulo | Direção | Responsabilidade |
| :--- | :--- | :--- | :---: | :--- |
| **Ingestão (ETL)** | `parse_money(value)` | `dashboard/utils.py` | Entrada ← | Converte texto/objeto bruto do Excel → `float` canônico |
| **Exibição (UI)** | `format_moeda_brl(valor)` | `dashboard/views/_helpers.py` | Saída → | Converte `float` canônico → string formatada em BRL (`"R$ 1.234,56"`) |

A separação é deliberada e garante que o sistema nunca apresente ao usuário o dado bruto da B3 não tratado, e nunca armazene em memória um valor pré-formatado para exibição que seria inutilizável para cálculos aritméticos.

```
          ┌──────────────────┐         ┌──────────────────┐
 Excel    │                  │  float  │                  │  "R$ 1.234,56"
 "1.234,56" ──► parse_money() ──────► cálculos P&L ──► format_moeda_brl() ──► UI
 "R$300,00"│ dashboard/utils  │  64-bit │ state_pipeline   │  dashboard/views │
           └──────────────────┘  IEEE   └──────────────────┘   /_helpers.py   │
```

---

##### C.2 A Função `parse_money`: Anatomia Completa

O código canônico em [`dashboard/utils.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/dashboard/utils.py#L43-L88) implementa uma máquina de estados linear de 7 fases:

```python
def parse_money(value: Any):
```

**Fase 1 — Curto-circuito para Nulos:**
```python
if value is None or pd.isna(value):
    return pd.NA
```
> `pd.NA` (e não `None` ou `0`) é retornado para que colunas monetárias mantenham compatibilidade com tipos anuláveis do pandas (`Int64`, `Float64`). Isso evita contaminação silenciosa de somas com zero.

**Fase 2 — Curto-circuito para Tipos Nativos Numéricos:**
```python
if isinstance(value, (int, float)) and not isinstance(value, bool):
    return float(value)
```
> A exclusão de `bool` é crítica: `True` e `False` são subtipos de `int` em Python (`isinstance(True, int) == True`). Sem essa guarda, `parse_money(True)` retornaria `1.0` — um erro silencioso em colunas binárias que possam vazar para colunas monetárias.

**Fase 3 — Extração de Sinal Contábil (Notação com Parênteses):**
```python
negative = False
if text.startswith("(") and text.endswith(")"):
    negative = True
    text = text[1:-1]
```
> A B3 e sistemas contábeis tradicionais representam débitos e valores negativos com parênteses:  
> `(1.234,56)` → `-1234.56`. Isso é diferente de um sinal negativo convencional (`-1234.56`).  
> A fase é executada **antes** da remoção de símbolos para que parênteses internos residuais (ex.: `(R$ 300,00)`) também sejam tratados nas fases seguintes.

**Fase 4 — Limpeza de Símbolos de Moeda e Espaços:**
```python
text = text.replace("R$", "").replace(" ", "")
text = text.replace("USD", "").replace("BRL", "")
text = text.replace("(", "").replace(")", "")
```
> Remove todos os prefixos monetários reconhecidos. A remoção de `(` e `)` residuais protege contra variantes como `(R$ 1.234,56)` onde o símbolo está dentro dos parênteses contábeis.

**Fase 5 — Heurística de Ambiguidade de Separadores (núcleo do algoritmo):**

Essa é a fase mais complexa. O problema central é que o mesmo caractere pode ser separador decimal ou de milhar, dependendo do contexto e locale:

```
"1.234,56"  →  BR: 1234.56  ✓
"1,234.56"  →  US: 1234.56  ✓
"102,5"     →  BR decimal: 102.5  ✓
"1,000"     →  US milhar: 1000.0  ← ambíguo!
"1.000"     →  BR milhar? ou decimal 1.0?
```

O algoritmo de resolução implementado:

```
Entrada: string numérica após limpeza de símbolos
           │
           ├─ [Vírgula E Ponto]
           │       │
           │       └─ rfind(",") > rfind(".")  ?
           │               │ SIM: BR → remove ".", substitui "," por "."
           │               │       ex: "1.234,56" → "1234.56"
           │               │
           │               └ NÃO: US → remove ","
           │                       ex: "1,234.56" → "1234.56"
           │
           ├─ [Apenas Vírgula]
           │       │
           │       └─ len(text.split(",")[-1]) <= 2 ?
           │               │ SIM: decimal BR → substitui "," por "."
           │               │       ex: "102,5"   → "102.5"
           │               │           "1.234,56" já tratado acima
           │               │
           │               └ NÃO: milhar → remove ","
           │                       ex: "1,000" → "1000" (US sem ponto decimal)
           │
           └─ [Apenas Ponto]
                   │
                   └─ text.count(".") > 1 ?
                           │ SIM: múltiplos pontos = milhar
                           │       ex: "1.234.567" → verifica último bloco
                           │           ≤2 dígitos? → "1234567." + decimais?
                           │           >2 dígitos? → remove todos os pontos
                           │
                           └ NÃO: ponto único
                                   │
                                   └─ len(text.split(".")[-1]) > 2 ?
                                           SIM: milhar sem decimal → remove "."
                                                ex: "1.234" → "1234" (3 dígitos após ponto)
                                           NÃO: decimal US standard
                                                ex: "9.99" → "9.99"
```

**Fase 6 — Conversão Aritmética e Aplicação do Sinal:**
```python
try:
    number = float(text)
    return -number if negative else number
except ValueError:
    return pd.NA
```

**Fase 7 — Degradação Graciosa:**
> Em vez de levantar exceção e abortar o processamento de toda a planilha, o parser retorna `pd.NA`. Isso permite que o pipeline continue processando as demais linhas e que o `RelatorioQualidade` capture os campos inválidos posteriormente.

---

##### C.3 Tabela Exaustiva de Casos Reais e Resultados Verificados em Teste

Extraída diretamente dos testes em [`tests/test_file_selection.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_file_selection.py#L34-L60) e [`tests/test_b3_architecture.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_b3_architecture.py#L63-L67):

| Valor de Entrada (Bruto B3) | Resultado `parse_money` | Caminho da Heurística | Observação |
| :--- | :---: | :--- | :--- |
| `102.5` (`float`) | `102.5` | Fase 2 (curto-circuito primitivo) | Número nativo sem conversão |
| `1.0` (`float`) | `1.0` | Fase 2 (curto-circuito primitivo) | Número nativo sem conversão |
| `-5.75` (`float`) | `-5.75` | Fase 2 (curto-circuito primitivo) | Negativo nativo preservado |
| `"102,5"` | `102.5` | Fase 5: apenas vírgula, 1 dígito após → decimal | Compra de título fracionário |
| `"1.234,56"` | `1234.56` | Fase 5: vírgula > ponto → BR milhar/decimal | Formato padrão B3 |
| `"R$ 1.234,56"` | `1234.56` | Fase 4 remove `R$` + Fase 5: vírgula > ponto | Exportação da UI da B3 |
| `"USD 42.50"` | `42.5` | Fase 4 remove `USD` + Fase 5: ponto único com 2 dígitos | BDR cotado em dólar |
| `"(1.234,56)"` | `-1234.56` | Fase 3 detecta parênteses → negativo | Débito contábil B3 |
| `"1.234"` | `1234.0` | Fase 5: ponto único, **3 dígitos** após → milhar | Valor sem centavos |
| `"1.234,5"` | `1234.5` | Fase 5: vírgula > ponto → BR milhar/decimal | 1 casa decimal |
| `"1.234.567,89"` | `1234567.89` | Fase 5: vírgula > ponto → BR múltiplos milhares | Valores grandes de Tesouro |
| `"1,234.56"` | `1234.56` | Fase 5: ponto > vírgula → US padrão | CSV exportado em locale US |
| `"12.345,67"` | `12345.67` | Fase 5: vírgula > ponto → BR | |
| `"0"` | `0.0` | Sem separadores → `float("0")` | Dividendo zerado |
| `"-12,34"` | `-12.34` | Sinal explícito + Fase 5: apenas vírgula decimal | Débito explícito sem parênteses |
| `"(12,34)"` | `-12.34` | Fase 3 parênteses + Fase 5: apenas vírgula decimal | Débito em notação contábil |
| `"R$ 0,00"` | `0.0` | Fase 4 remove `R$` + Fase 5: vírgula com 2 dígitos | Operação zerada |
| `"  9.99  "` | `9.99` | `.strip()` + Fase 5: ponto único com 2 dígitos | Espaços irrelevantes |
| `"1.234.567"` | `1234567.0` | Fase 5: múltiplos pontos, último bloco com 3 dígitos → remove todos | Saldo de milionário |
| `"99"` | `99.0` | Sem separadores → `float("99")` | Valor simples inteiro |
| `""` | `pd.NA` | Fase 1 da string vazia → `pd.NA` | Célula em branco |
| `None` | `pd.NA` | Fase 1 (`pd.isna`) | Nulo do pandas |
| `30.78` (`float`) | `30.78` | Fase 2 (curto-circuito) | Preço unitário de ação |

> [!WARNING]
> **Ambiguidade Intrínseca**: A string `"1,234"` (sem ponto) é tratada como milhar americano → `1234.0`, pois o bloco após a vírgula tem 3 dígitos. Contudo `"1,23"` é tratado como decimal brasileiro → `1.23` (2 dígitos após vírgula). Se a B3 exportar um valor de `R$ 1,234` (um real e duzentos e trinta e quatro milésimos, formato incomum), o resultado seria errado. **Essa limitação é conhecida, aceita e documentada** pois nunca ocorre nos extratos reais da B3 que sempre seguem o padrão de 2 casas decimais.

---

##### C.4 Re-exportação de `parse_money` pelo Módulo Loader

Os testes em [`tests/test_file_selection.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_file_selection.py#L8) e [`tests/test_b3_architecture.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_b3_architecture.py#L13) importam `parse_money` de `dashboard.loaders.movimentacao`, não de `dashboard.utils`:

```python
from dashboard.loaders.movimentacao import parse_money
```

Porém, inspecionando o loader, ele **apenas re-importa** `parse_money` de `dashboard.utils`:

```python
# dashboard/loaders/movimentacao.py
from dashboard.utils import parse_money, parse_qtd
```

Isso significa que `parse_money` **não é implementada no loader**; ela é importada para o namespace do módulo `movimentacao`, e os testes a consomem por conveniência de caminho de importação. A implementação canônica permanece em [`dashboard/utils.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/dashboard/utils.py#L43-L88), que é a **Single Source of Truth (SSoT)** desta função.

---

##### C.5 Onde `parse_money` é Aplicada no Pipeline

```python
# Em _normalize_movimentacao_df (dashboard/loaders/movimentacao.py)
for col in ["preco_unitario", "valor_operacao"]:
    df[col] = df[col].apply(parse_money)

# Em read_posicao_excel (dashboard/loaders/posicao.py)
df["valor_operacao"] = df["valor_operacao"].apply(parse_money)
df["valor_aplicado"]  = df["valor_aplicado"].apply(parse_money)
```

- **`preco_unitario`:** O preço de execução por unidade do ativo — essencial para o cálculo de Preço Médio Ponderado.
- **`valor_operacao`:** O valor financeiro bruto total da operação (quantidade × preço unitário).
- **`valor_aplicado`:** Valor efetivamente aplicado reportado pela B3 para títulos do Tesouro Direto (pode diferir do `valor_operacao` por acréscimos de juros acumulados).

---

##### C.6 A Camada de Saída: `format_moeda_brl` em `dashboard/views/_helpers.py`

A função inversa, responsável por renderizar valores monetários na UI do Streamlit:

```python
def format_moeda_brl(valor: float | int | None) -> str:
    """Formata valor numérico como moeda brasileira (ex.: 2943.59 -> 'R$ 2.943,59')."""
    if valor is None or pd.isna(valor):
        return "—"
    try:
        v = float(valor)
        s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
    except (ValueError, TypeError):
        return "—"
```

**Mecânica do Swap de Separadores:**
A string de formato Python `f"{v:,.2f}"` produz saída em locale americano (ex.: `"2,943.59"`). A cadeia de substituições triplas converte para locale brasileiro:
1. `","` → `"X"` (placeholder temporário para milhar)
2. `"."` → `","` (ponto decimal vira vírgula)
3. `"X"` → `"."` (placeholder de milhar vira ponto)

Resultado: `"2,943.59"` → `"2X943.59"` → `"2X943,59"` → `"2.943,59"` → `"R$ 2.943,59"`.

**Casos de Fronteira em `format_moeda_brl`:**

| Valor de Entrada | Saída | Observação |
| :--- | :---: | :--- |
| `2943.59` | `"R$ 2.943,59"` | Caso padrão Tesouro |
| `0.0` | `"R$ 0,00"` | Ativo zerado |
| `None` | `"—"` | Campo ausente (travessão em UI) |
| `pd.NA` | `"—"` | Nulo pandas |
| `-300.5` | `"R$ -300,50"` | P&L negativo — tratado pelo chamador |
| `1234567.89` | `"R$ 1.234.567,89"` | Patrimônio grande |

> [!NOTE]
> A formatação de P&L negativo é gerenciada **pelo chamador** (`_render_card`), que aplica lógica de sinal e prefixo `"+"` ou `"-"` sobre o `abs(pl)` antes de chamar `format_moeda_brl`. A função em si não assume semântica de sinal — ela formata o valor absoluto recebido.

---

#### D. Parsing Numérico de Quantidades Fracionárias — Estudo Aprofundado

##### D.1 Problema de Domínio: Por Que Quantidades Requerem Parser Especializado

No mercado financeiro brasileiro, a semântica da `quantidade` é radicalmente diferente dependendo da classe de ativo:

| Classe de Ativo | Granularidade Mínima | Exemplo Real | Complexidade |
| :--- | :---: | :--- | :--- |
| Ações (lote padrão) | `1` inteiro | `100`, `200` | Baixa |
| Ações (mercado fracionário) | `1` inteiro | `37`, `1` | Baixa |
| BDRs | `1` inteiro | `5`, `17` | Baixa |
| FIIs | `1` inteiro | `20` | Baixa |
| **Tesouro Direto** | `0,01` fração | `0,12`, `0,05`, `1,45` | **Alta** |
| ITSA4 (caso real) | fracionário via evento | `24.15` | **Alta** (sobra de grupamento) |

O Excel exportado pela B3, quando aberto em ambiente Windows com locale `pt-BR`, serializa quantidades com **vírgula como separador decimal**. Ao ser lido pelo pandas com `dtype=object`, a célula chega como string `"0,12"`.

Se o sistema não usar `parse_qtd` e confiar na coerção automática do pandas (`pd.to_numeric("0,12")`), o resultado seria `pd.NA` (erro de conversão). Antes da implementação de `parse_qtd`, um `"0,12"` era convertido silenciosamente para `0.0` ou gerava `NaN`, zerando a posição do investidor no título do Tesouro — um bug crítico de precisão financeira.

---

##### D.2 Código Canônico e Árvore de Decisão de `parse_qtd`

```python
def parse_qtd(value: Any):
    if value is None or pd.isna(value):
        return pd.NA                             # Fase 1: nulos

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)                      # Fase 2: primitivos nativos

    text = str(value).strip().replace(" ", "")   # Fase 3: conversão e limpeza
    if not text:
        return pd.NA

    if "," in text and "." in text:              # Fase 4: ambos separadores
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")  # BR: 1.234,56
        else:
            text = text.replace(",", "")                    # US: 1,234.56

    elif "," in text:                            # Fase 5: apenas vírgula
        text = text.replace(",", ".")            # SEMPRE decimal em quantidades!

    elif "." in text and text.count(".") > 1:   # Fase 6: múltiplos pontos
        text = text.replace(".", "")             # milhar sem decimal

    try:
        return float(text)                       # Fase 7: conversão final
    except ValueError:
        return pd.NA                             # Fase 8: degradação graciosa
```

> [!IMPORTANT]
> **Diferença crítica entre `parse_qtd` e `parse_money` na Fase de Vírgula Única:**
>
> | Função | `"1,000"` (apenas vírgula, 3 dígitos) | Razão |
> | :--- | :---: | :--- |
> | `parse_money` | `1000.0` (milhar US) | Valores monetários têm 2 casas; 3 dígitos = milhar |
> | `parse_qtd` | `1.0` (decimal) | Quantidades B3 NUNCA usam vírgula como milhar → sempre decimal |
>
> Para quantidades, a vírgula é **sempre** tratada como separador decimal. A B3 nunca exporta quantidades com separador de milhar em vírgula — portanto a heurística de "3 dígitos = milhar" de `parse_money` **não se aplica** a `parse_qtd`. Isso elimina a ambiguidade e preserva a precisão de frações como `0,12`.

---

##### D.3 Tabela Exaustiva: Casos Reais e Cobertura de Testes

Extraída de [`tests/test_quantidade_tesouro.py`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_quantidade_tesouro.py):

| Valor de Entrada | Resultado `parse_qtd` | Classe Ativo Típica | Fase da Árvore |
| :--- | :---: | :--- | :--- |
| `"0,12"` | `0.12` | Tesouro Direto | Fase 5: vírgula → decimal |
| `"0,05"` | `0.05` | Tesouro Direto | Fase 5: vírgula → decimal |
| `"1,45"` | `1.45` | Tesouro Direto | Fase 5: vírgula → decimal |
| `"1,00"` | `1.0` | Tesouro (1 título inteiro) | Fase 5: vírgula → decimal |
| `"100"` | `100.0` | Ação lote padrão | Fase 7 direto |
| `"1000"` | `1000.0` | Ação lote | Fase 7 direto |
| `0.12` (`float`) | `0.12` | Tesouro (já float) | Fase 2: primitivo |
| `100` (`int`) | `100.0` | Ações (já int) | Fase 2: primitivo |
| `"-5"` | `-5.0` | Venda/débito explícito | Fase 7 com sinal |
| `"-0,12"` | `-0.12` | Venda de fração Tesouro | Fase 5 + sinal negativo |
| `"1.000"` | `1.0` | **⚠ Ambíguo** | Fase 6: ponto único, 3 dígitos |
| `None` | `pd.NA` | — | Fase 1 |
| `""` | `pd.NA` | — | Fase 3: string vazia |
| `"abc"` | `pd.NA` | — | Fase 8: ValueError |

> [!WARNING]
> **Limitação Documentada de `parse_qtd` para `"1.000"`**:  
> O teste [`test_string_1ponto000_interpretada_como_decimal`](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/tests/test_quantidade_tesouro.py#L59-L66) explicita que `parse_qtd("1.000")` retorna `1.0` (decimal) e não `1000.0` (milhar). Isso é uma **limitação conhecida e aceita**, pois os extratos reais da B3 nunca geram quantidades de ações com ponto de milhar — os campos de quantidade são sempre inteiros sem separador ou decimais com vírgula. O teste garante que o comportamento anômalo seja ao menos **detectável e documentado**, sem ser um bug silencioso.

---

##### D.4 Garantia de Integridade: O Teste da Fração do Tesouro

O teste central que valida o comportamento end-to-end da correção, chamado de "garantia central da correção":

```python
# tests/test_quantidade_tesouro.py
def test_fracao_tesouro_nao_vira_zero(self):
    """Garantia central da correção: 0,12 não pode resultar em 0."""
    resultado = parse_qtd("0,12")
    assert resultado != pytest.approx(0.0)
    assert resultado == pytest.approx(0.12)
```

E o teste de cobertura completa dos múltiplos de 0,01 (granularidade mínima do Tesouro Direto):

```python
def test_multiplos_de_001(self):
    """Tesouro permite múltiplos de 0,01 conforme regra do programa."""
    for centesimos in range(1, 100):
        valor_str = f"0,{centesimos:02d}"
        esperado = centesimos / 100
        assert parse_qtd(valor_str) == pytest.approx(esperado, abs=1e-9)
```

Este teste valida **99 casos** (`0,01` a `0,99`) em um único passe, garantindo que nenhuma fração fracionária do Tesouro seja truncada ou zerada.

---

##### D.5 Formatação de Saída de Quantidade: Lógica por Classe de Ativo

A exibição da quantidade nos cards da interface segue uma regra dual que reflete a semântica de cada classe de ativo:

```python
# Lógica extraída de dashboard/views/_helpers.py (_render_card)
if "TESOURO" in categoria.upper():
    # 2 casas decimais para frações de título
    qtd_str = f"{quantidade:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    # 0.12 → "0,12" | 1.0 → "1,00" | 1.45 → "1,45"
else:
    # Inteiro sem casas para ações, BDRs, FIIs
    qtd_str = f"{int(round(quantidade)):,}".replace(",", ".")
    # 100.0 → "100" | 1000.0 → "1.000" | 10000.0 → "10.000"
```

**Tabela de Exemplos de Saída da UI:**

| Quantidade Interna | Categoria | Exibição UI | Teste de Regressão |
| :---: | :---: | :---: | :--- |
| `0.12` | `TESOURO` | `"0,12"` | `test_tesouro_zero_virgula_doze` |
| `0.05` | `TESOURO` | `"0,05"` | `test_tesouro_zero_virgula_zero_cinco` |
| `1.0` | `TESOURO` | `"1,00"` | `test_tesouro_um_titulo_inteiro` |
| `1.45` | `TESOURO` | `"1,45"` | `test_tesouro_um_virgula_quarenta_cinco` |
| `100.0` | `ACOES` | `"100"` | `test_nao_tesouro_exibe_inteiro` |
| `1000.0` | `ACOES` | `"1.000"` | `test_acoes_milhares_usa_ponto_br` |
| `10000.0` | `ACOES` | `"10.000"` | `test_acoes_dez_mil_usa_ponto_br` |
| `100.000000001` | `ACOES` | `"100"` | `test_acoes_arredonda_float_impreciso` |

> A última linha é especialmente relevante: imprecisões de ponto flutuante IEEE 754 (como `100.000000001`) são silenciosamente arredondadas via `int(round(...))` para evitar que o usuário veja `"100"` em um caso e `"101"` em outro por artefatos numéricos.

---

## 4. Normalização e Padronização de Dados

### 4.1 Arquitetura do Pipeline de ETL (Extract, Transform, Load)

```
┌────────────────────────────────────────────────────────────────────────┐
│ EXTRACT                                                                │
│ - pd.ExcelFile(engine="openpyxl") / pd.read_csv                        │
│ - Leitura de todas as abas com dtype=object                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRANSFORM 1: Sintaxe & Cabeçalhos                                      │
│ - Normalização NFKD de acentuação e caixa baixa (normalize_alias)      │
│ - Renomeação via dicionário ALIASES_MOV                                │
│ - Validação estrita do conjunto de 8 colunas canônicas                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRANSFORM 2: Tipagem e Saneamento Numérico                             │
│ - Parsing de data duplo (DD/MM/AAAA + mixed fallback)                  │
│ - Coerção parse_money em preco_unitario e valor_operacao               │
│ - Coerção parse_qtd em quantidade (suporte a fracionário do Tesouro)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRANSFORM 3: Resolução de Identidade Canônica                          │
│ - anotar_ativos -> resolver_ativo_seguro(produto, qualidade)           │
│ - Extração do Ticker Canônico (ativo) e AtivoId(classe, codigo)        │
│ - Auditoria de qualidade: registro de aviso ATIVO_DESCONHECIDO         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRANSFORM 4: Enriquecimento Contábil Vetorial                          │
│ - sinal = entrada_saida.map(SINAL_ENTRADA_SAIDA)                       │
│ - qtd_liquida = quantidade * sinal                                     │
│ - valor_liquido = valor_operacao * sinal                               │
│ - mes = data.dt.to_period("M").astype(str)                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LOAD: Consumo pelo DashboardState & Motores de Negócio                 │
│ - aplicar_eventos_ordenados (Preço Médio, Posição Acumulada)           │
│ - Matriz de Reconciliação (Movimentação vs Posição B3)                 │
│ - Alocação nas 5 Classes Canônicas e P&L Histórico                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Contrato e Dicionário de Transformação de Dados

A tabela abaixo descreve o contrato de entrada (bruto da B3), o processo de transformação e o estado final do schema relacional em memória:

| Coluna Bruta B3 | Coluna Canônica | Tipo Destino | Regra de Limpeza / Transformação | Restrição |
| :--- | :--- | :---: | :--- | :---: |
| `Entrada/Saída`, `Entrada/Saida` | `entrada_saida` | `str` | `.strip().lower()` $\implies$ `"credito"` ou `"debito"` | Not Null |
| `Data` | `data` | `datetime64[ns]` | `pd.to_datetime` com `format="%d/%m/%Y"`, fallback `format="mixed"` | Nullable |
| `Movimentação`, `Movimentacao` | `movimentacao` | `str` | `.strip().lower()`, mapeado para `TipoMovimentacao` | Not Null |
| `Produto` | `produto` | `str` | `.strip()`. Fallback para `"Sem nome"` se nulo | Not Null |
| `Instituição`, `Instituicao` | `instituicao` | `str` | `.strip()`. Fallback para `"Sem instituição"` se nulo | Not Null |
| `Quantidade` | `quantidade` | `float64` | `parse_qtd()`. Preserva até 4 casas decimais | Not Null ($\ge 0$) |
| `Preço unitário`, `Preco unitario` | `preco_unitario` | `float64` | `parse_money()`. Remove moedas e converte decimais | Not Null |
| `Valor da Operação`, `Valor da Operacao` | `valor_operacao` | `float64` | `parse_money()`. Remove moedas e converte decimais | Not Null |
| *(Derivada)* | `sinal` | `int64` | `map({"credito": 1, "debito": -1}).fillna(0)` | $\in \{-1, 0, 1\}$ |
| *(Derivada)* | `qtd_liquida` | `float64` | `quantidade * sinal` | Computada |
| *(Derivada)* | `valor_liquido` | `float64` | `valor_operacao * sinal` | Computada |
| *(Derivada)* | `mes` | `str` | `data.dt.to_period("M").astype(str)` (Ex.: `"2026-08"`) | Computada |
| *(Enriquecida)* | `ativo` | `str` | Código canônico resolvido (ex.: `"PETR4"`, `"ROXO34"`) | Not Null |
| *(Enriquecida)* | `ativo_id` | `AtivoId` | Objeto de valor imutável `AtivoId(classe, codigo)` | Not Null |

---

### 4.3 Resolução de Identidade do Ativo (`dashboard/models/catalogo.py`)

O campo `produto` nas planilhas da B3 apresenta descrições longas, heterogêneas e mutáveis ao longo dos anos. Exemplos reais:
- `"PETR4 - PETROLEO BRASILEIRO S/A - PETROBRAS"`
- `"CPFE3 - CPFL ENERGIA S/A"` vs `"CPFE3 - CPFL ENERGIA S.A."`
- Mudança societária de BDR: `"NUBR33"` e `"NUBR35"` virando `"ROXO34"` (Nu Holdings)

O motor de resolução implementado em `resolver_ativo` garante tipagem forte e unicidade através da entidade canônica:

```python
@dataclass(frozen=True, order=True)
class AtivoId:
    classe: Classe     # Enum: ACOES, BDR, ETF, FII, TESOURO, DESCONHECIDO
    codigo: str        # Ticker canônico ou nome oficial do título
```

#### Algoritmo de Resolução de Ativo:
1. **Curto-Circuito:** Se o argumento já for uma instância de `AtivoId`, retorna imediatamente.
2. **Validação de Nulos:** Rejeita strings vazias ou nulas com `AtivoDesconhecido`.
3. **Normalização Prévia de Produto (`normalizar_nome` em `dashboard/models/texto.py`):**
   - Converte para caixa alta sem acento.
   - Substitui variações societárias como `\bS/A\b` por `"S.A."`.
   - Remove hífens redundantes como `"- PETROBRAS"`.
4. **Resolução em 3 Fases:**
   - **Fase 1 (Catálogo Completo):** Verifica se a descrição normalizada coincide com algum alias cadastrado no catálogo.
   - **Fase 2 (Divisão por Hífen / Prefixo de Ticker):** Se o produto contiver `" - "`, isola o prefixo antes do hífen (ex.: `"PETR4"` de `"PETR4 - PETROLEO..."`) e consulta a tabela rápida de tickers (`_MAPA_TICKERS`).
   - **Fase 3 (Ticker Direto):** Testa a string diretamente contra o mapa de tickers.
5. **Degradação Graciosa e Auditoria de Qualidade (`resolver_ativo_seguro`):**
   - Caso um novo ativo ainda não esteja presente no catálogo oficial, o pipeline **não aborta a aplicação**.
   - O ativo é registrado como `Classe.DESCONHECIDO` utilizando o nome normalizado.
   - Um aviso estruturado é despachado para a instância de `RelatorioQualidade`:
     ```python
     qualidade.add(Aviso(
         tipo="ATIVO_DESCONHECIDO",
         produto=str(produto),
         detalhe="Ativo não encontrado no catálogo canônico"
     ))
     ```

---

### 4.4 Agrupamento Canônico nas 5 Classes de Ativos

Para fins de balanço patrimonial, cálculo de risco e renderização de gráficos, os dados normalizados de movimentação e custódia são classificados dinamicamente em 5 macro-classes canônicas (`dashboard/models/categorias.py`):

```
                                  Ativo Consolidado
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 ▼                                                 ▼
        Bolsa de Valores                                    Tesouro Direto
                 │                                                 │
        ┌────────┴────────┐                       ┌────────────────┼────────────────┐
        ▼                 ▼                       ▼                ▼                ▼
    1. Ações         2. Internacional      3. Renda Fixa    4. Renda Fixa    5. Renda Fixa
 (Ações Nacionais)   (BDRs, ROXO34...)     Pós-Fixada       Inflação         Prefixada
                                          (Tesouro Selic) (Tesouro IPCA+ /  (Prefixado c/ e
                                                            Educa+)          s/ juros sem.)
```

A função determinística `classificar_classe_5(produto, categoria)` implementa essa árvore de decisão:
- Se categoria for `AÇÕES` ou similar $\implies$ **"Ações"**.
- Se categoria for `BDR` $\implies$ **"Internacional"**.
- Se for `TESOURO`:
  - Contém `"SELIC"` $\implies$ **"Renda fixa pós-fixada"**.
  - Contém `"PREFIXADO"` $\implies$ **"Renda fixa prefixada"**.
  - Contém `"IPCA"` ou `"EDUCA"` $\implies$ **"Renda fixa inflação"**.

---

### 4.5 Motor Contábil: Cálculo de Preço Médio e Posição Acumulada

O pipeline `aplicar_eventos_ordenados` (`dashboard/models/pipeline_eventos.py`) constitui o coração computacional que transforma a série histórica de movimentações no estado patrimonial da carteira:

1. **Ordenação Temporal Estável:**  
   O histórico de movimentações é agrupado por ativo e ordenado de forma determinística por data:
   ```python
   base = base.sort_values(["ativo_id", "data"], kind="mergesort", na_position="last")
   ```
2. **Máquina de Estados de Custódia (`PosicaoAcumulada` e `_aplicar_linha`):**  
   Para cada registro cronológico de um ativo, a classe `PosicaoAcumulada` transiciona segundo as fórmulas contábeis padrão da Receita Federal do Brasil / B3:

   - **Compra:**  
     $$\text{Qtd}_{novo} = \text{Qtd}_{anterior} + \Delta Q$$
     $$\text{Custo}_{novo} = \text{Custo}_{anterior} + \text{Valor Operação}$$
     $$\text{Preço Médio} = \frac{\text{Custo}_{novo}}{\text{Qtd}_{novo}}$$
   - **Venda / Desinvestimento:**  
     $$\text{Custo Unitário Médio} = \frac{\text{Custo}_{anterior}}{\text{Qtd}_{anterior}}$$
     $$\text{Qtd}_{novo} = \text{Qtd}_{anterior} - \Delta Q_{venda}$$
     $$\text{Custo}_{novo} = \text{Custo}_{anterior} - (\Delta Q_{venda} \times \text{Custo Unitário Médio})$$
     *(O preço médio unitário permanece matematicamente inalterado durante uma venda parcial).*
   - **Desdobramento (Split):**  
     Aumenta a quantidade $\Delta Q$ sem alterar o custo total. O preço médio unitário sofre deflação automática.
   - **Grupamento (Reverse Split):**  
     Aplica semântica `TOTAL`, redefinindo a quantidade total para o novo saldo consolidado sem alterar o custo acumulado.
   - **Proventos em Dinheiro:**  
     Afetam exclusivamente as métricas de retorno e renda acumulada, sem modificar a quantidade ou o custo patrimonial do ativo.

---

### 4.6 Reconciliação Contábil Automática (Movimentação vs Posição)

Para fechar o ciclo de governança de dados, o sistema audita se as movimentações históricas consolidadas justificam com precisão matemática a fotografia estática presente na planilha de Posição da B3 (`dashboard/metrics/reconciliacao.py`).

O módulo `comparar()` calcula:
$$\Delta = \text{Qtd Custódia (Posição B3)} - \text{Qtd Acumulada (Movimentações até a data)}$$

- Se $|\Delta| \le 10^{-4}$: O ativo é considerado **100% conciliado**.
- Se $|\Delta| > 10^{-4}$: O sistema emite alerta analítico na interface (`st.warning`), indicando que existem eventos não capturados, aportes externos ou transferências de custódia pendentes de conciliação.
- Se a divergência for proveniente de eventos com efeito `define` (como atualização periódica de saldo), a tabela rotula a discrepância com a observação `"ajuste por atualização"`.

---

## 5. Diretrizes Operacionais de Engenharia e Manutenção

Para qualquer modificação futura nos loaders, modelos de movimentação ou aliases:

1. **Protocolo Canônico de Testes Unitários:**
   ```powershell
   .\.venv\Scripts\pytest -q --tb=short
   ```
2. **Princípios de Arquitetura Mandatórios:**
   - **Single Source of Truth (SSoT):** Regras de sinais contábeis pertencem unicamente a `dashboard/models/movimentacao.py`. Mapeamento de efeitos pertence exclusivamente a `dashboard/models/efeitos.py`.
   - **Don't Repeat Yourself (DRY):** Parsers numéricos e sanitizadores de string não devem ser reimplementados nas views; utilize `dashboard.utils` e `dashboard.models.texto`.
   - **Single Responsibility Principle (SRP):** Os loaders apenas extraem, normalizam e enriquecem o dado bruto. Agregações patrimoniais, curvas de rentabilidade e métricas de P&L devem permanecer desacopladas nos módulos de `dashboard.metrics` e `dashboard.state_pipeline`.
