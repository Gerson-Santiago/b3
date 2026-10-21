# Issue 4.6 — Ícones SVG de Ativos em Custódia

**Fase:** 4 — Novos Gráficos, Alocação Macro & Identidade Visual  
**Status:** ✅ Concluído  
**Commit:** `5f10e31`  

---

## Por que esta tarefa é valiosa?

Identificar ativos financeiros apenas por texto e código ticker torna a leitura dos cards de custódia densa e homogênea. A inclusão de logotipos SVG oficiais dos ativos (ações, BDRs e Tesouro Direto) proporciona reconhecimento visual instantâneo e eleva o nível estético do cockpit da carteira para o padrão de plataformas de ponta.

---

## Critérios de Aceite (Definition of Done)

- [x] Módulo `views/svg/links.py` contendo mapa de links SVG e função `get_svg_url(ticker)`.
- [x] Renderização assíncrona de imagem `<img loading="lazy">` em `views/_helpers.py` com dimensões fixas (28x28px) e tratamento gracioso para falha de carregamento (`onerror="this.style.display='none'"`).
- [x] Fallback gracioso: caso o ticker não possua logo mapeado, a interface não exibe imagem quebrada nem espaço em branco.
- [x] Testes unitários cobrindo o mapeamento de links e a geração de HTML em `tests/test_svg_links.py` e `tests/test_views_helpers.py`.

---

## Checklist de Ações

- [x] Criar `dashboard/views/svg/links.py` com links CDN de alta disponibilidade.
- [x] Implementar helper `_svg_icon_html(ticker)` em `dashboard/views/_helpers.py`.
- [x] Integrar ícones nos cabeçalhos dos cards em `render_cards_grid()`.
- [x] Adicionar testes unitários em `tests/test_svg_links.py` e `tests/test_views_helpers.py`.
