# Schema de movimentação B3 (CSV/XLSX)

## Finalidade

Descreve as colunas reconhecidas pelo loader `dashboard/loaders/movimentacao.py`. O relatório representa eventos da carteira; cada linha válida é uma movimentação individual. O loader aceita CSV e Excel. Em Excel, percorre todas as abas e concatena as que contêm o conjunto de colunas obrigatório.

## Colunas de entrada

Os cabeçalhos são normalizados sem diferenciar maiúsculas/minúsculas nem acentos. Os nomes da coluna **canônica** são os nomes usados no DataFrame resultante.

| Coluna canônica | Cabeçalho B3 reconhecido | Obrigatória | Interpretação |
| --- | --- | :---: | --- |
| `entrada_saida` | `Entrada/Saída` ou `Entrada/Saida` | Sim | Direção do lançamento. `Crédito` soma; `Débito` subtrai. |
| `data` | `Data` | Sim | Data do evento, normalmente `DD/MM/AAAA`. |
| `movimentacao` | `Movimentação` ou `Movimentacao` | Sim | Tipo/descrição do evento, por exemplo compra ou venda. |
| `produto` | `Produto` | Sim | Descrição do ativo ou produto. |
| `instituicao` | `Instituição` ou `Instituicao` | Sim | Instituição relacionada à movimentação. |
| `quantidade` | `Quantidade` | Sim | Quantidade informada no evento. |
| `preco_unitario` | `Preço unitário` ou `Preco unitario` | Sim | Preço por unidade. |
| `valor_operacao` | `Valor da Operação` ou `Valor da Operacao` | Sim | Valor total informado para a operação. |

Se faltar qualquer coluna obrigatória, a leitura falha com indicação das colunas ausentes. Colunas adicionais não fazem parte do contrato canônico documentado.

## Formatos aceitos

- **CSV:** delimitador `;`, vírgula decimal; tenta UTF-8 com BOM e depois Latin-1. Valores numéricos também aceitam formatos como `1.234,56`, `R$ 1.234,56` e números negativos entre parênteses.
- **Excel:** o loader encaminha `.xlsx` e `.xls` ao engine `openpyxl`, que lê o formato `.xlsx`, mas não planilhas binárias `.xls` legadas. Abas vazias ou sem o schema obrigatório são ignoradas; se nenhuma aba for reconhecida, a leitura falha.
- **Datas:** tenta primeiro `DD/MM/AAAA` e depois interpretação flexível com dia primeiro. Datas não reconhecidas ficam como `NaT`.

## Colunas produzidas

Além das colunas de entrada normalizadas, o loader gera:

| Coluna | Regra |
| --- | --- |
| `sinal` | `1` para crédito, `-1` para débito e `0` para direção não reconhecida. |
| `qtd_liquida` | `quantidade * sinal`. |
| `valor_liquido` | `valor_operacao * sinal`. |
| `mes` | Período mensal da coluna `data`, no formato `AAAA-MM`. |

`entrada_saida` e `movimentacao` são convertidas para minúsculas; espaços externos são removidos. Produto e instituição vazios recebem, respectivamente, `Sem nome` e `Sem instituição`. A normalização de valores inválidos pode resultar em valor ausente.

## Exemplo conceitual

| Entrada/Saída | Data | Movimentação | Produto | Instituição | Quantidade | Preço unitário | Valor da Operação |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| Crédito | 06/08/2026 | Compra | PETR4 | Corretora X | 10 | 30,00 | 300,00 |

Para esse exemplo, `sinal = 1`, `qtd_liquida = 10`, `valor_liquido = 300` e `mes = 2026-08`.
