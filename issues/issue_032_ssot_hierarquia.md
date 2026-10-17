# Issue 3.2 — SSoT: Mover Regras de Remapeamento de Categoria de `treemap.py` para `models/categorias.py`

**Fase:** 3 — SSoT & DRY
**Status:** ⏳ Backlog
**Estimativa:** 2–3 horas
**Dependência:** Issue 2.1 a 2.4 ✅ (todos os testes de `charts/` verdes)

---

## Por que esta tarefa é valiosa?

Hoje, `treemap.py` contém este dicionário hardcoded na camada de **visualização**:

```python
{"AÇÕES": "Bolsa de Valores", "BDR": "Bolsa de Valores", "TESOURO": "Tesouro Direto"}
```

Esta regra de negócio ("AÇÕES e BDR pertencem à Bolsa de Valores") já existe no domínio — parcialmente em `models/categorias.py` através de `CATEGORIAS_BOLSA` e `agrupar_bolsa()`. Ter essa regra duplicada na camada visual viola o SSoT e cria o risco de divergência: se o nome da categoria mudar no modelo, o treemap quebra silenciosamente.

---

## Critérios de Aceite (Definition of Done)

- [ ] O dicionário de remapeamento é removido de `treemap.py`.
- [ ] `treemap.py` passa a consumir a lógica existente de `dashboard.models.categorias`.
- [ ] `pytest tests/test_treemap.py` continua passando sem modificação.
- [ ] A função `_preparar_dados_hierarquia()` não contém mais strings de categoria hardcoded.

---

## Checklist de Ações

- [ ] Ler `dashboard/models/categorias.py` para mapear o que já existe (`CATEGORIAS_BOLSA`, `CATEGORIA_TESOURO`, `agrupar_bolsa()`).
- [ ] Identificar se `agrupar_bolsa()` já faz o remapeamento — se sim, reutilizar diretamente.
- [ ] Se necessário, criar função auxiliar `nome_exibicao_categoria(categoria: str) -> str` em `categorias.py` que traduz `"AÇÕES"` → `"Bolsa de Valores"` etc.
- [ ] Reescrever `_preparar_dados_hierarquia()` em `treemap.py` para usar essa função do domínio.
- [ ] Executar `pytest tests/test_treemap.py -v` → todos devem passar.

---

## Contexto — Violação Atual (SSoT)

```python
# treemap.py — linha com regra de negócio hardcoded na camada visual ❌
df["categoria_hierarquia"] = df["categoria"].replace(
    {"AÇÕES": "Bolsa de Valores", "BDR": "Bolsa de Valores", "TESOURO": "Tesouro Direto"}
)
```

## Contexto — Domínio já existente para reusar

```python
# dashboard/models/categorias.py — o que já existe ✅
CATEGORIAS_BOLSA = [...]   # contém "AÇÕES", "BDR"
CATEGORIA_TESOURO = "TESOURO"
def agrupar_bolsa(pos_categoria: pd.DataFrame) -> pd.DataFrame: ...
```
