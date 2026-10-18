# Documentação de Schemas de Dados B3 (XLSX / CSV)

Esta pasta contém as especificações técnicas, contratos canônicos e diretrizes de engenharia dos relatórios exportados pela **Área do Investidor da B3** e consumidos pelo Dashboard B3.

---

## Estrutura da Documentação

- [**area_do_investido.md**](area_do_investido.md): Visão geral da Área do Investidor, pipeline de processamento, regras antiduplicação, 5 Classes de Ativos, auditoria de qualidade e guia de refatoração para IAs e desenvolvedores.
- [**movimentacao_b3_xlsx.md**](movimentacao_b3_xlsx.md): Contrato e schema de movimentações cronológicas (compras, vendas, proventos, frações do Tesouro, sinais e colunas derivadas).
- [**posicao_b3_xlsx.md**](posicao_b3_xlsx.md): Contrato e schema da posição em custódia (snapshot a mercado, mapeamento de abas, detecção de divergência e agregação em 5 classes).

---

## 🤖 Guia Operacional para IA e Engenheiros

### Execução de Testes Unitários
Ao realizar alterações ou verificar integridade:

```powershell
.\.venv\Scripts\pytest -q --tb=short
```

### Fluxo Ideal de Refatoração
1. **Proteja:** Verifique/crie testes cobrindo o comportamento atual antes de qualquer alteração.
2. **Isole a Verdade (SSoT):** Centralize regras em uma única estrutura ou módulo de modelo.
3. **Elimine a Duplicação (DRY):** Remova redundâncias de código e de testes.
4. **Divida (SRP):** Quebre funções e classes grandes em componentes coesos, validando cada etapa com:
   ```powershell
   .\.venv\Scripts\pytest -q --tb=short
   ```
