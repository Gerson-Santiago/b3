# Issue 6.1 — Schema `proventos_recebidos_b3_xlsx.md`

**Fase:** 6 — Loader de Proventos Recebidos
**Status:** ⏳ Backlog
**Estimativa:** 1 hora
**Dependência:** Arquivo `xlsx/proventos-recebidos/proventos-recebidos-*.xlsx` presente ✅

> ⚠️ **Pré-condição:** Abrir o arquivo XLSX real e mapear todas as colunas antes de escrever qualquer código. Este documento é o contrato que define o que `loaders/proventos_recebidos.py` deve produzir.

---

## Por que esta tarefa é valiosa?

Seguindo o padrão do projeto (`doc/schema_db_xlsx/movimentacao_b3_xlsx.md` e `posicao_b3_xlsx.md`), toda fonte de dados externa deve ter seu schema documentado **antes** do loader. Isso garante que aliases, testes e o reader estejam alinhados a uma fonte única da verdade.

---

## Critérios de Aceite (Definition of Done)

- [ ] Arquivo `doc/schema_db_xlsx/proventos_recebidos_b3_xlsx.md` criado.
- [ ] Documentadas: todas as colunas brutas (nome exato B3), tipo inferido e coluna normalizada (snake_case).
- [ ] Exemplos de valores reais (anonimizados se necessário).
- [ ] Observações sobre particularidades do formato (datas, valores monetários, colunas opcionais).

---

## Checklist de Ações

- [ ] Abrir `xlsx/proventos-recebidos/proventos-recebidos-*.xlsx` e listar todas as colunas.
- [ ] Para cada coluna: anotar nome exato, tipo de dado, exemplo de valor.
- [ ] Criar `doc/schema_db_xlsx/proventos_recebidos_b3_xlsx.md` seguindo a estrutura de `posicao_b3_xlsx.md`.
- [ ] Identificar qual coluna distingue o tipo de provento (Dividendo / JCP / Rendimento FII).
- [ ] Identificar colunas de data: data ex, data pagamento, competência.

---

## Definição de "Testável"

```
# Revisão manual: o schema descreve com precisão o XLSX aberto lado a lado.
# Sem código novo nesta issue — apenas documentação.
# Issue 6.2 depende deste documento.
```
