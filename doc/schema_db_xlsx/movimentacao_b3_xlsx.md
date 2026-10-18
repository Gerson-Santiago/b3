# Schema de Movimentação B3 (CSV / XLSX)

## 1. Finalidade

Descreve o contrato de dados consumido e processado pelo loader `dashboard/loaders/movimentacao.py`. O relatório de movimentação representa eventos operacionais cronológicos da carteira (compras, vendas, transferências e proventos creditados). Cada linha válida corresponde a uma movimentação individual.

O loader suporta tanto arquivos **CSV** quanto planilhas **Excel (.xlsx)** com múltiplas abas.

---

## 2. Colunas de Entrada (Normalização via `ALIASES_MOV`)

Os cabeçalhos brutos da B3 são normalizados automaticamente ignorando maiúsculas/minúsculas, espaços e acentos:

| Coluna Canônica | Cabeçalho B3 Reconhecido | Obrigatória | Tipo Esperado | Interpretação |
| :--- | :--- | :---: | :---: | :--- |
| `entrada_saida` | `Entrada/Saída`, `Entrada/Saida` | **Sim** | `str` | Direção do lançamento: `Credito` (adiciona) ou `Debito` (subtrai). |
| `data` | `Data` | **Sim** | `date` | Data da operação (`DD/MM/AAAA` ou formato ISO flexível). |
| `movimentacao` | `Movimentação`, `Movimentacao` | **Sim** | `str` | Tipo do evento: Compra, Venda, Dividendo, JCP, Rendimento, etc. |
| `produto` | `Produto` | **Sim** | `str` | Descrição completa ou ticker informado no relatório B3. |
| `instituicao` | `Instituição`, `Instituicao` | **Sim** | `str` | Corretora ou instituição financeira onde ocorreu a operação. |
| `quantidade` | `Quantidade` | **Sim** | `float` | Quantidade movimentada (suporta valores inteiros e fracionários). |
| `preco_unitario` | `Preço unitário`, `Preco unitario` | **Sim** | `float` | Preço de execução por unidade do ativo. |
| `valor_operacao` | `Valor da Operação`, `Valor da Operacao` | **Sim** | `float` | Valor financeiro total da operação. |

> Se faltar qualquer coluna obrigatória, o loader lança `ValueError` detalhando as colunas ausentes.

---

## 3. Formatos Suportados e Tratamento Numérico

- **CSV:** Delimitador `;`, vírgula como separador decimal. Decodificação robusta iniciando em `utf-8-sig` (BOM) com fallback automático para `latin-1`.
- **Excel (.xlsx):** Leitura de todas as abas via motor `openpyxl`. Abas vazias ou sem o conjunto obrigatório de colunas são descartadas silenciosamente.
- **Valores Monetários (`parse_money`):** Converte strings contendo prefixos `R$`, pontos de milhar, vírgulas decimais e notações contábeis com parênteses (ex.: `(1.250,00)` vira `-1250.0`).
- **Quantidades (`parse_qtd`):** Suporta quantidades fracionárias com até 4 casas decimais (essencial para **Tesouro Direto**, ex.: `0,12` título).
- **Datas:** Tentativa primária no padrão brasileiro `DD/MM/AAAA` (`dayfirst=True`), com parsing flexível para formatos mistos. Datas inválidas convertidas em `NaT`.

---

## 4. Colunas Produzidas e Enriquecidas

Após a validação, o DataFrame gerado é enriquecido com colunas operacionais e identidade canônica:

| Coluna | Regra de Cálculo / Origem | Exemplo |
| :--- | :--- | :--- |
| `sinal` | `1` para crédito, `-1` para débito e `0` para direção indefinida (`SINAL_ENTRADA_SAIDA`). | `1` |
| `qtd_liquida` | `quantidade * sinal` | `10.0` (ou `-5.0`) |
| `valor_liquido` | `valor_operacao * sinal` | `300.00` |
| `mes` | Período mensal da coluna `data` no formato `AAAA-MM` | `2026-08` |
| `ativo` | Ticker canônico resolvido via `anotar_ativos` e `CATALOGO_ATIVOS` | `PETR4`, `Tesouro Selic 2029` |
| `ativo_id` | Objeto `AtivoId(classe, codigo)` com identidade de classe e código canônico | `AtivoId(classe='AÇÕES', codigo='PETR4')` |

### Auditoria de Qualidade (`RelatorioQualidade`)
Se um produto da movimentação não for reconhecido pelo catálogo de ativos, ele recebe a classe `DESCONHECIDO` e é registrado no relatório de qualidade com o aviso `ATIVO_DESCONHECIDO`, permitindo monitoramento sem quebrar a execução.

---

## 5. Exemplo Conceitual

**Entrada (Linha da B3):**
```text
Entrada/Saída: Credito | Data: 06/08/2026 | Movimentação: Compra | Produto: PETR4 - PETROLEO BRASILEIRO S.A. | Instituição: XP INVESTIMENTOS | Quantidade: 10 | Preço unitário: 30,00 | Valor da Operação: 300,00
```

**Saída Processada (DataFrame Canônico):**
```text
sinal: 1 | qtd_liquida: 10.0 | valor_liquido: 300.00 | mes: "2026-08" | ativo: "PETR4" | ativo_id: AtivoId(classe='AÇÕES', codigo='PETR4')
```

---

## 6. Diretrizes para IA e Desenvolvedores

Ao trabalhar neste loader, pipelines derivados ou métricas de movimentação:

1. **Comando de Testes Canônico (Rápido e Conciso):**
   ```powershell
   .\.venv\Scripts\pytest -q --tb=short
   ```
2. **Ciclo de Desenvolvimento:**
   - **Proteja:** Valide regressões com os testes de `test_default_loader.py` e `test_b3_metrics.py`.
   - **SSoT:** Regras de sinais pertencem exclusivamente a `dashboard/models/movimentacao.py`.
   - **DRY:** Use os parsers centralizados `parse_money` e `parse_qtd` de `dashboard.utils`.
   - **SRP:** O loader apenas ingere e enriquece; cálculos acumulados pertencem a `dashboard.metrics` e `dashboard.state_pipeline`.
