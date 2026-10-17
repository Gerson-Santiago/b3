# Schema de posição B3 (XLSX)

## Finalidade

Descreve as colunas reconhecidas pelo loader `dashboard/loaders/posicao.py`. O relatório representa uma fotografia dos ativos em custódia, não uma sequência de eventos. O loader lê todas as abas da planilha e concatena as linhas de produto reconhecidas.

## Colunas de entrada

Os cabeçalhos reconhecidos são normalizados sem diferenciar maiúsculas/minúsculas nem acentos. Os nomes da coluna **canônica** são usados no DataFrame resultante. Com exceção de `Produto`, os campos abaixo são opcionais para aceitar uma linha.

| Coluna canônica | Cabeçalho B3 reconhecido | Observação |
| --- | --- | --- |
| `data_posicao` | `Data da posição` ou `Data da posicao` | Data de referência, quando fornecida. |
| `produto` | `Produto` | Obrigatória; linhas vazias, `-` e `Total` são descartadas. |
| `instituicao` | `Instituição` ou `Instituicao` | Instituição de custódia. |
| `conta` | `Conta` | Identificação da conta. |
| `codigo_negociacao` | `Código de Negociação` ou `Codigo de Negociacao` | Código/ticker informado pela B3. |
| `cnpj_empresa` | `CNPJ da Empresa` | Identificação da empresa. |
| `codigo_isin` | `Código ISIN / Distribuição` ou `Codigo ISIN / Distribuicao` | Código ISIN/distribuição reconhecido pelo alias do loader. |
| `tipo` | `Tipo` | Tipo/classe do ativo. |
| `escriturador` | `Escriturador` | Escriturador, quando aplicável. |
| `quantidade` | `Quantidade` | Quantidade total. |
| `quantidade_disponivel` | `Quantidade Disponível` ou `Quantidade Disponivel` | Parcela disponível; mantida como campo de origem. |
| `quantidade_indisponivel` | `Quantidade Indisponível` ou `Quantidade Indisponivel` | Parcela indisponível; mantida como campo de origem. |
| `motivo` | `Motivo` | Motivo de eventual indisponibilidade. |
| `preco_fechamento` | `Preço de Fechamento` ou `Preco de Fechamento` | Preço informado no relatório. |
| `valor_atualizado` | `Valor Atualizado` | Se não existir `valor_operacao`, é usado como seu valor de origem. |
| `categoria` | `Categoria` | A categoria final é determinada pela aba, não pelo conteúdo desta coluna. |

Abas do Tesouro podem conter campos adicionais, como indexador, vencimento e valores aplicado/bruto/líquido. Esses campos não têm aliases canônicos neste loader; podem permanecer com o cabeçalho normalizado, mas não são convertidos pelos tratamentos numéricos descritos abaixo.

## Abas e classificação

O nome da aba determina `categoria`: nomes contendo `tesouro` resultam em `TESOURO`; contendo `bdr`, em `BDR`; todas as demais abas com `Produto` são classificadas como `AÇÕES`. A busca não diferencia maiúsculas/minúsculas. Portanto, nomeie as abas conforme a classe para evitar classificação incorreta.

## Colunas produzidas e conversões

| Coluna | Regra |
| --- | --- |
| `categoria` | Categoria calculada a partir do nome da aba, substituindo eventual categoria de entrada. |
| `valor_operacao` | Valor atualizado convertido para `valor_operacao` se esse campo ainda não existir; é convertido para número quando presente. |
| `quantidade` | Convertida para número quando presente. |
| `valor_liquido` | Cópia de `valor_operacao`, ou zero se não houver esse campo. |
| `qtd_liquida` | Cópia de `quantidade`, ou zero se não houver esse campo. |
| `entrada_saida` | Valor constante `credito`. |
| `movimentacao` | Valor constante `posicao`. |
| `data_posicao` | Se ausente, recebe a data atual. |
| `data` | Usa `data_posicao` quando não há `data`; datas inválidas ou ausentes recebem a data atual. |
| `mes` | Mês de `data`, no formato `AAAA-MM`. |

Campos de quantidade disponível/indisponível e preço de fechamento são reconhecidos pelo nome, mas não participam da criação de `qtd_liquida` ou `valor_liquido`. A posição usa a quantidade total e o valor atualizado para essas colunas derivadas.

## Limitações e validação

- O loader chama `openpyxl` para ler os arquivos Excel. O formato `.xlsx` é o formato esperado; arquivos `.xls` são encaminhados ao mesmo engine, que não lê planilhas binárias legadas.
- Abas vazias ou sem a coluna `Produto` são ignoradas. Se nenhuma aba válida for encontrada, a leitura falha.
- Linhas em que o produto seja vazio, `-` ou `Total` são removidas para não incluir linhas de resumo no dashboard.
- A ausência de `Data da posição` não impede a leitura, mas atribui a data da execução. Para análises históricas, mantenha a data correta no arquivo de origem.
