# Dashboard de Investimentos B3

Dashboard analítico e interativo desenvolvido em **Python**, **Streamlit** e **Plotly** para consolidação, visualização e auditoria de carteiras a partir dos relatórios oficiais exportados da **Área do Investidor da B3**.

---

## 🎯 Funcionalidades e Abas

O painel é estruturado em 4 abas principais com atualização reativa a filtros temporais, por instituição e por ativo:

### 1. 💼 Carteira & Visão Geral
* **Cockpit de Decisão:** Cards de Patrimônio Atual, Custo Total, Lucro/Prejuízo (R$ e %) e Total de Proventos.
* **Alocação Macro:** Divisão entre Bolsa de Valores (Ações e BDRs) e Renda Fixa (Tesouro Direto).
* **Alocação por 5 Classes de Ativos:** Ações, BDRs, Tesouro Selic, Tesouro Inflação (IPCA+ / Educa+) e Tesouro Prefixado.
* **Gráficos Interativos:** Rosquinha (Donut) padronizada e Treemap hierárquico de ativos com links diretos para o *Status Invest*.

### 2. 📈 Evolução Patrimonial
* Histórico temporal de patrimônio e saldo por produto e por categoria.
* Curvas de rentabilidade e aportes acumulados ao longo do tempo.

### 3. 💰 Proventos & Renda
* **Histórico Mensal de Proventos:** Visualização em barras com acumulado anual e segmentação opcional por tipo (Dividendos, JCP, Rendimento FII).
* **Dividend Yield (LTM) & Yield on Cost:** Gráficos e tabela de rentabilidade de proventos sobre valor a mercado e preço médio.
* **Calendário de Proventos Recebidos:** Tabela granular ordenada por data de crédito com ativo, tipo e valor líquido.

### 4. 🔍 Reconciliação B3 (Auditoria Dupla)
* **Reconciliação de Custódia (Movimentações vs Posição):** Compara a quantidade física calculada por movimentações acumuladas contra o snapshot da custódia B3.
* **Reconciliação de Proventos (Movimentação vs Extrato):** Cruza centavo a centavo os créditos da movimentação com o extrato dedicado de proventos recebidos da B3, destacando discrepâncias fiscais ou bancárias.
* **Relatório de Qualidade de Dados:** Alertas de ativos desconhecidos, divergências de classe ou eventos pendentes.

---

## 📂 Estrutura de Pastas e Arquivos de Dados

O dashboard pode carregar os dados automaticamente a partir das pastas locais (selecionando o arquivo mais recente) ou via upload interativo na barra lateral:

```
PROJETOS/b3/
├── dashboard/                     # Código-fonte da aplicação
│   ├── aliases/                   # Mapeamentos centralizados de colunas (SSoT)
│   ├── charts/                    # Componentes visuais reutilizáveis (Plotly)
│   ├── loaders/                   # Leitores tipados para cada fonte B3
│   ├── metrics/                   # Motores de cálculo financeiro e auditoria
│   ├── models/                    # Regras de negócio, catálogo de ativos e eventos
│   ├── views/                     # Abas da interface do usuário
│   ├── app.py                     # Ponto de entrada do Streamlit
│   └── state.py                   # Estado consolidado (DashboardState)
├── doc/                           # Documentação técnica e schemas XLSX
│   └── schema_db_xlsx/            # Contratos de dados de movimentação, posição e proventos
├── issues/                        # Roadmap e especificação técnica das tarefas
├── tests/                         # Suíte de testes automatizados com pytest
└── xlsx/                          # Diretórios de planilhas exportadas da B3
    ├── movimentacao/              # movimentacao-AAAA-MM-DD-*.xlsx
    ├── posicao/                   # posicao-AAAA-MM-DD-*.xlsx
    └── proventos-recebidos/       # proventos-recebidos-*.xlsx
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
* Python 3.10 ou superior instalado.

### 2. Instalação das Dependências
```bash
pip install -r requirements.txt
```

### 3. Execução do Dashboard

* **No Windows (atalho rápido):**
  Basta dar um duplo clique no script:
  ```cmd
  run_dashboard.bat
  ```

* **Via terminal:**
  ```bash
  streamlit run dashboard/app.py
  ```

---

## 🧪 Testes Automatizados

O projeto adota práticas rigorosas de qualidade de software com arquitetura orientada a testes unitários e de integração:

```bash
# Executar todos os testes
python -m pytest

# Executar com saída resumida
python -m pytest -q --tb=short
```

---

## 📖 Documentação Adicional

* [Roadmap de Desenvolvimento](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/issues/00_roadmap.md)
* [Schema de Movimentação B3](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/doc/schema_db_xlsx/movimentacao_b3_xlsx.md)
* [Schema de Posição B3](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/doc/schema_db_xlsx/posicao_b3_xlsx.md)
* [Schema de Proventos Recebidos B3](file:///c:/Users/gerson_6061/Desktop/PROJETOS/b3/doc/schema_db_xlsx/proventos_recebidos_b3_xlsx.md)
