# Issue 6.5 — Seção de Reconciliação de Proventos na View (`views/reconciliacao.py`)

**Fase:** 6 — Loader de Proventos Recebidos
**Status:** ✅ Concluído
**Estimativa:** 2–3 horas
**Dependência:** Issue 6.4 ✅ (métrica de reconciliação de proventos)

> **Princípio:** Seguir o fluxo de refatoração: **1. Proteja** (testes de renderização/smoke da view) → **2. Isole a Verdade (SSoT)** (view consome apenas resultados já calculados no `DashboardState`) → **3. Elimine a Duplicação (DRY)** (reutilizar componentes de cards de alerta/sucesso) → **4. Divida (SRP)** (view apenas exibe os dados, sem regras de matching).


---

## Por que esta tarefa é valiosa?

Com o cálculo de reconciliação de proventos pronto (Issue 6.4), o usuário precisa visualizar de forma clara na interface se seus proventos do extrato e de movimentação batem 100%, ou se há inconsistências a serem verificadas na corretora.

---

## Critérios de Aceite (Definition of Done)

- [x] Nova seção adicionada na aba de reconciliação (`views/reconciliacao.py`): `"### Reconciliação de Proventos (Movimentação vs Extrato de Proventos)"`.
- [x] Exibição de tabela interativa com status de conciliação.
- [x] Mensagens de alerta (`st.warning`) se houver divergência ou sucesso (`st.success`) se todos os proventos baterem.
- [x] `app.py` e `DashboardState` atualizados para carregar o arquivo padrão de proventos recebidos se disponível.
- [x] Teste de fumaça na view garantindo que a renderização ocorre sem exceções quando há e quando não há dados.


---

## Checklist de Ações

### 1. Proteja (Testes Primeiro)
- [ ] Criar ou estender teste em `tests/test_reconciliacao.py` validando que a chamada à view aceita os novos dados.

### 2. Isole a Verdade (SSoT)
- [ ] Integrar no `DashboardState` o DataFrame de proventos recebidos brutos/filtrados e a reconciliação calculada.

### 3. Elimine a Duplicação (DRY)
- [ ] Reutilizar a formatação condicional de tabelas já aplicada na reconciliação de custódia.

### 4. Divida (SRP)
- [ ] Manter a renderização contida em subfunção `_render_reconciliacao_proventos()` dentro de `views/reconciliacao.py`.

---

## Definição de "Testável"

```bash
pytest tests/test_reconciliacao.py -v
# → PASSED
# Dashboard exibe a nova subseção de auditoria de proventos
```
