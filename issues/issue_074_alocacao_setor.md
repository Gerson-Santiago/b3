# Issue 7.4 — Mapeamento Setorial e Alocação por Setor

**Fase:** 7 — Posição Interativa & Alocação Estendida
**Status:** ⏳ Backlog
**Estimativa:** 4–5 horas
**Dependência:** `models/identidade.py` ✅ + `state.pos_cards` ✅

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes com catálogo de setores) → **2. Isole a Verdade (SSoT)** (dicionário/tabela canônica de setores em `models/setores.py`) → **3. Elimine a Duplicação (DRY)** (reutilizar `_criar_donut` e hierarquia de categorias) → **4. Divida (SRP)** (resolução de setor separada da camada de apresentação).

---

## Por que esta tarefa é valiosa?

Um dos pilares de diversificação é a exposição por setor econômico (Financeiro, Energia Elétrica, Saneamento, Commodities, Varejo, Tecnologia, Renda Fixa Pública). Uma carteira com 10 ações pode parecer diversificada, mas se 8 forem bancos e utilities, o risco setorial é enorme. Um mapeamento canônico de setores para os ativos em carteira permite gerar visualizações de concentração setorial.

---

## Critérios de Aceite (Definition of Done)

- [ ] Módulo `dashboard/models/setores.py` com mapeamento de setores padrão B3 para os principais tickers (ações e FIIs) e classificação automática do Tesouro Direto como `"Renda Fixa / Títulos Públicos"`.
- [ ] Fallback seguro: ativos sem mapeamento conhecido recebem setor `"Outros / Não Classificado"`.
- [ ] Coluna `setor` enriquecida em `state.pos_cards` via pipeline.
- [ ] Gráfico donut / barras de alocação por setor em `charts/pie.py` ou `charts/bars.py`.
- [ ] Testes unitários cobrindo o mapeamento setorial, classificação de ativos conhecidos e fallbacks.

---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar `tests/test_setores.py` testando resolução de setores de ações comuns (PETR4, VALE3, ITUB4), FIIs e Tesouro Direto.

### 2. Isole a Verdade (SSoT)
- [ ] Centralizar a base de setores em `models/setores.py` (ou catálogo de metadados de ativos).

### 3. Elimine a Duplicação (DRY)
- [ ] Chamar `obter_setor_ativo(ativo_id_ou_ticker)` uniformemente no enriquecimento do pipeline.

### 4. Divida (SRP)
- [ ] Isolar a função de enriquecimento dentro de `dashboard/state_pipeline.py`.

---

## Definição de "Testável"

```bash
pytest tests/test_setores.py -v
# → PASSED
```
