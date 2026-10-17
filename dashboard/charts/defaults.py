"""
Configurações visuais padrão dos gráficos do Dashboard B3.
Altere este arquivo para ajustar cores, fontes e estilos globalmente.
"""

# ---------------------------------------------------------------------------
# Tipografia
# ---------------------------------------------------------------------------
FONT_FAMILY = "Arial, sans-serif"
FONT_SIZE_BASE = 12
FONT_SIZE_TITLE = 20
FONT_COLOR_TITLE = "#262730"  # cor padrão de heading do Streamlit

# ---------------------------------------------------------------------------
# Margens e dimensões
# ---------------------------------------------------------------------------
MARGIN_DEFAULT = dict(l=30, r=30, t=60, b=40)
MARGIN_NO_LEGEND = dict(l=30, r=30, t=60, b=20)

HEIGHT_PIE = 420
HEIGHT_PIE_SMALL = 380
HEIGHT_BAR = 400
HEIGHT_LINE = 400
HEIGHT_LINE_COMPARATIVO = 430

# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
# Cor primária de aportes / custo acumulado
COLOR_CUSTO = "#64748b"

# Patrimônio
COLOR_PATRIMONIO = "#2563eb"
COLOR_PATRIMONIO_MARKER = "#1d4ed8"

# Proventos (barras)
COLOR_PROVENTOS = "#10b981"

# Dividend Yield (barras)
COLOR_DY = "#0284c7"

# Sequência de cores para gráficos de pizza (Plotly Express)
PIE_COLOR_SEQUENCE = [
    "#2563eb",  # azul
    "#10b981",  # verde
    "#f59e0b",  # âmbar
    "#ef4444",  # vermelho
    "#8b5cf6",  # violeta
    "#06b6d4",  # ciano
    "#f97316",  # laranja
    "#84cc16",  # lima
    "#ec4899",  # rosa
    "#6366f1",  # índigo
]

# ---------------------------------------------------------------------------
# Hover / tooltip
# ---------------------------------------------------------------------------
HOVERLABEL = dict(bgcolor="white", font_size=12)
