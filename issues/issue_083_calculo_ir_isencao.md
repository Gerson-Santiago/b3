# Issue 8.3 — Motor de Cálculo de IR, Isenção e Prejuízos a Compensar (`metrics/ir.py`)

**Fase:** 8 — Vendas, Lucro Realizado e IR
**Status:** ⏳ Backlog
**Estimativa:** 4–5 horas
**Dependência:** Issue 8.2 ✅ (agregação de vendas por mês e categoria)

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes com matriz completa de cenários fiscais) → **2. Isole a Verdade (SSoT)** (regras da Receita Federal codificadas em constantes e funções puras) → **3. Elimine a Duplicação (DRY)** (carry-forward unificado por cesta de compensação) → **4. Divida (SRP)** (módulo puramente fiscal, sem acoplamento com visualização).

---

## Por que esta tarefa é valiosa?

A apuração tributária para pessoa física em renda variável no Brasil possui regras rígidas e cheias de particularidades que geram erros frequentes se calculadas manualmente:

1. **Isenção de R$ 20 mil/mês (Ações Swing Trade):**
   - A soma do volume bruto de vendas no mês considera **apenas ações em operações normais (swing trade)**.
   - **BDRs e ETFs NÃO entram nessa soma** e **NÃO possuem isenção**.
2. **Incidência do Imposto Acima de R$ 20 mil:**
   - Se o total vendido em ações ultrapassar R$ 20.000 no mês, **o imposto de 15% incide sobre TODO o lucro líquido apurado no mês** (e NÃO apenas sobre o valor que exceder R$ 20 mil), após abater prejuízos acumulados anteriores da mesma cesta.
3. **Mês Isento Não Consome Prejuízo:**
   - Se um mês de ações teve vendas ≤ R$ 20.000 com lucro, o investidor é isento. Nesse mês, **nenhum prejuízo acumulado anterior é consumido**, pois prejuízos acumulados servem exclusivamente para abater lucro tributável.
4. **Cestas de Compensação de Prejuízos (Segregação Tributária):**
   - **Cesta Comum / Swing Trade (15%):** Ações swing trade, BDRs e ETFs de renda variável compensam resultados e prejuízos entre si.
   - **Cesta FII / Fiagro (20%):** Alíquota de 20%. Prejuízos apurados em FII só abatem lucros futuros de FII.
   - **Cesta Day Trade (20%):** Alíquota de 20%. Prejuízos apurados em day trade só compensam com lucros futuros de day trade.
5. **DARF (Código 6015):**
   - Vencimento fixado no **último dia útil do mês subsequente** ao das operações com lucro tributável.
   - DARF com valor inferior a R$ 10,00 acumula para pagamento quando atingir o piso mínimo.
6. ⚠️ **Nota Regulatória Pendente (A Confirmar):**
   - Há menções em fontes do mercado sobre uma eventual unificação/nova regra de 2026 para compensação entre diferentes classes de ativos. Este ponto fica registrado formalmente como **"A CONFIRMAR"** antes de alterar as regras clássicas das 3 cestas vigentes.

---

## Critérios de Aceite (Definition of Done)

- [ ] Módulo `dashboard/metrics/ir.py` com função `apurar_ir_mensal(vendas_df: pd.DataFrame) -> pd.DataFrame`.
- [ ] Retorna tabela detalhada mês a mês contendo:
  - `mes` (formato YYYY-MM)
  - `cesta` (`"Swing / Comum"`, `"FII"`, `"Day Trade"`)
  - `total_vendas_acoes_mes` (volume bruto de vendas de ações no mês para controle do teto)
  - `isento` (True se ações swing trade ≤ R$ 20.000, False para BDR/FII ou vendas de ações > R$ 20k)
  - `lucro_ou_prejuizo_mes` (resultado líquido bruto das operações do mês na cesta)
  - `prejuizo_acumulado_anterior` (saldo de prejuízo trazido de meses passados)
  - `prejuizo_consumido_mes` (montante de prejuízo utilizado para abater lucro tributável; **zero se mês for isento**)
  - `base_calculo_ir` (`max(0, lucro_tributavel - prejuizo_consumido)`)
  - `prejuizo_acumulado_fim_mes` (saldo remanescente para carregar ao mês seguinte)
  - `aliquota_ir` (0.15 ou 0.20)
  - `ir_devido` (`base_calculo_ir * aliquota_ir`)
  - `data_vencimento_darf` (último dia útil do mês subsequente)
- [ ] Cobertura completa de testes em `tests/test_ir.py`.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar `tests/test_ir.py` cobrindo cenários:
  - **Cenário 1 (Isenção pura):** Venda R$ 18.000 em ações com lucro de R$ 3.000. Retorna `isento=True`, `ir_devido=0.0`.
  - **Cenário 2 (Isenção não consome prejuízo):** Saldo anterior de prejuízo = R$ 2.000. Mês com vendas de R$ 15.000 e lucro de R$ 4.000 (isento). O saldo de prejuízo deve continuar intacto em R$ 2.000 para os meses seguintes!
  - **Cenário 3 (Acima de 20k):** Venda de R$ 21.000 em ações com lucro de R$ 5.000 e sem prejuízo anterior. IR deve ser `15% * R$ 5.000 = R$ 750,00` (incidência sobre todo o lucro, não sobre a fração de 1.000).
  - **Cenário 4 (BDR sem isenção):** Venda de BDR de R$ 2.000 com lucro de R$ 500. `isento=False`, IR = R$ 75,00.
  - **Cenário 5 (Compensação na cesta comum):** Prejuízo de R$ 1.000 em BDR compensando lucro tributável de R$ 2.000 em Ações.
  - **Cenário 6 (Segregação de FII):** Prejuízo de FII de R$ 1.000 **NÃO** abate lucro tributável de ações. FII tributa a 20%.

### 2. Isole a Verdade (SSoT)
- [ ] Definir constantes regulatórias:
  ```python
  LIMITE_ISENCAO_ACOES_SWING = 20000.0
  ALIQUOTA_SWING_COMUM = 0.15
  ALIQUOTA_FII = 0.20
  ALIQUOTA_DAY_TRADE = 0.20
  CODIGO_RECEITA_DARF = "6015"
  ```

### 3. Elimine a Duplicação (DRY)
- [ ] Motor único de carry-forward parametrizado por cesta de compensação.

### 4. Divida (SRP)
- [ ] Cálculo puramente matemático e fiscal, desacoplado de Streamlit.

---

## Definição de "Testável"

```bash
.venv\Scripts\pytest.exe tests/test_ir.py -v
# → PASSED
```
