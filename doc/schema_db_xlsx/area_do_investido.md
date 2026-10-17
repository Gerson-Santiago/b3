# Área do Investidor B3

A Área do Investidor é o portal da B3 que reúne informações sobre ativos mantidos em custódia em diferentes instituições. Os relatórios exportados pelo portal são a origem dos arquivos de movimentação e posição usados neste projeto.

## Relatórios usados pelo dashboard

- **Movimentação:** eventos como compras, vendas e proventos, com data, produto, instituição, quantidade e valores da operação. O formato aceito e as transformações aplicadas estão em [movimentacao_b3_xlsx.md](movimentacao_b3_xlsx.md).
- **Posição:** fotografia dos ativos em custódia, normalmente organizada em abas por classe de ativo. O formato aceito e as transformações aplicadas estão em [posicao_b3_xlsx.md](posicao_b3_xlsx.md).

O dashboard não consulta a Área do Investidor diretamente. É necessário exportar os relatórios e carregá-los na aplicação em CSV (movimentação) ou Excel `.xlsx`. Arquivos `.xls` legados podem não ser lidos pelo engine utilizado.

## Interpretação dos dados

Os relatórios são fontes diferentes e complementares: movimentações representam eventos ao longo do tempo; posição representa quantidades e valores em uma data de referência. Não some uma posição às movimentações como se fosse outro evento de compra: isso duplicaria quantidades e valores. A posição também pode ser usada para conferir saldos calculados a partir do histórico.

Os dados exportados refletem as informações e datas disponibilizadas pela B3 e pelas instituições participantes. Divergências de custódia, eventos corporativos ou diferenças de período podem exigir conferência no relatório original.