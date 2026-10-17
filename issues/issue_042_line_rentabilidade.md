# Issue 4.2 — Criar `line_rentabilidade_acumulada()` com Benchmark
 
**Fase:** 4 — Novos Gráficos
**Status:** ✅ Concluído
**Estimativa:** 6–8 horas
**Dependência:** Fase 2 ✅ + Fase 3 ✅

> ⚠️ **Nota de Negociabilidade (N do INVEST):** Esta issue é a mais complexa da Fase 4.
> A implementação pode começar com uma versão simplificada (sem benchmark externo) e evoluir.
> O programador tem liberdade para escolher a metodologia de rentabilidade (TWR simplificado ou retorno simples de snapshots).

---

## Por que esta tarefa é valiosa?

A **Pergunta 1** ("Como meu patrimônio evoluiu?") está parcialmente respondida pelo gráfico de `line_comparativo_patrimonio_e_aportes`. Porém, **valor absoluto não é rentabilidade**. Um investidor que aportou R$ 100k e tem R$ 110k hoje teve 10% de retorno, mas se o CDI rendeu 12% no mesmo período, ele perdeu para o benchmark. Esse gráfico transforma dados absolutos em **percentual comparável**, a visão mais importante para avaliar decisões de alocação.

---

## Critérios de Aceite (Definition of Done)

- [x] Função `line_rentabilidade_acumulada(curva_patrimonio, curva_referencia=None)` criada em `charts/lines.py`.
- [x] Linha de rentabilidade da carteira em `%` acumulado desde a data mais antiga.
- [x] Linha de benchmark opcional (CDI, IPCA ou Ibovespa), se `curva_referencia` for fornecida.
- [x] Hover mostra: `Data` e `Rentabilidade Acumulada (%)`.
- [x] Integrado na view `views/evolucao.py` como uma segunda seção abaixo do gráfico existente.
- [x] Teste unitário básico: DataFrame válido → `go.Figure` com ao menos 1 trace.

---

## Checklist de Ações

### Etapa A — Versão 1 (sem benchmark, apenas carteira)

- [x] Calcular `retorno_pct = (patrimonio / patrimonio[0] - 1) * 100` a partir de `curva_patrimonio["patrimonio_liquido"]`.
- [x] Criar `line_rentabilidade_acumulada(curva_patrimonio, curva_referencia=None)` em `lines.py`.
- [x] Integrar em `views/evolucao.py`: nova seção `"### Rentabilidade Acumulada da Carteira (%)"`.
- [x] Teste: cenário feliz + `curva_patrimonio` com apenas 1 ponto (não deve lançar exceção).

### Etapa B — Versão 2 (com benchmark, negociável)

- [x] Definir estrutura de `curva_referencia`: `pd.DataFrame` com colunas `data` e `valor_referencia` (ou `retorno_pct`).
- [x] Adicionar segunda trace ao gráfico quando `curva_referencia` for fornecida.
- [x] Decidir: o benchmark vem de arquivo local? De API? (Esta decisão pode ser uma issue separada de `metrics/`).

### Etapa C — Exportar

- [x] Adicionar `line_rentabilidade_acumulada` em `charts/__init__.py` e `__all__`.

---

## Contexto — Dado de Entrada Disponível

```python
# state_pipeline.py — curvas_segmentadas() já produz curva_patrimonio com:
# {"data": [...], "patrimonio_liquido": [...]}
# Acesso via state.evol_dict["curva_patrimonio"]
```

---

## Definição de "Testável"

```
pytest tests/test_charts_lines.py -v   # inclui novo teste da versão 1
# → PASSED
# Dashboard exibe o gráfico de rentabilidade em % na aba Evolução & Aportes
```
