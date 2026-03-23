BG_PRIMARY = "#1A1A2E"
BG_SECONDARY = "#16213E"
TEXT_PRIMARY = "#EAEAEA"
TEXT_MUTED = "#8892A0"

TILE_COLOURS = {
    "exercise": "#00B4D8",
    "projects": "#FF6B35",
    "reading": "#7B2D8E",
    "work": "#00A86B",
}

EXTRA_COLOURS = [
    "#E63946",
    "#F4A261",
    "#2A9D8F",
    "#E9C46A",
    "#264653",
    "#D62828",
    "#457B9D",
    "#6A4C93",
]

TILE_ICONS = {
    "exercise": "&#x1F3CB;",   # weight lifter
    "projects": "&#x1F680;",   # rocket
    "reading": "&#x1F4DA;",    # books
    "work": "&#x1F4BC;",       # briefcase
}


def get_global_css():
    return """
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&display=swap');

/* Global font and typography — dyslexia friendly */
html, body, [class*="css"], .stMarkdown, .stButton button,
.stTextInput input, .stSelectbox select, .stTextArea textarea,
div[data-testid="stAppViewContainer"], div[data-testid="stHeader"] {
    font-family: 'Lexend', sans-serif !important;
    letter-spacing: 0.03em;
}

/* Body text sizing */
html, body {
    font-size: 16px;
    line-height: 1.6;
}

/* Headings */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}
h1, .stMarkdown h1 { font-size: 28px !important; }
h2, .stMarkdown h2 { font-size: 22px !important; }
h3, .stMarkdown h3 { font-size: 18px !important; }

/* Dark background enforcement */
div[data-testid="stAppViewContainer"],
div[data-testid="stHeader"],
section[data-testid="stSidebar"],
.main .block-container {
    background-color: """ + BG_PRIMARY + """ !important;
}

/* Hide default Streamlit menu and footer for cleaner look */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }

/* All text left-aligned, never justified */
p, li, span, div { text-align: left; }

/* Button base style — flat, no shadow, no border */
.stButton button {
    border: none !important;
    box-shadow: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 16px !important;
    transition: opacity 0.15s ease;
    min-height: 44px;
}
.stButton button:hover {
    opacity: 0.88;
    border: none !important;
    box-shadow: none !important;
}
.stButton button:focus {
    outline: 2px solid #00B4D8 !important;
    outline-offset: 2px;
}

/* Tile card style */
.tile-card {
    border-radius: 8px;
    padding: 22px 20px;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    cursor: pointer;
    transition: opacity 0.15s ease, transform 0.1s ease;
    position: relative;
}
.tile-card:hover {
    opacity: 0.92;
    transform: translateY(-2px);
}
.tile-icon {
    font-size: 28px;
    margin-bottom: 8px;
}
.tile-snippet {
    font-size: 14px;
    opacity: 0.9;
    margin-bottom: 10px;
    line-height: 1.4;
}
.tile-label {
    font-size: 20px;
    font-weight: 600;
    color: white;
}

/* Add tile (+ button) */
.tile-add {
    border: 2px dashed """ + TEXT_MUTED + """;
    border-radius: 8px;
    padding: 22px 20px;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: opacity 0.15s ease;
    background: transparent;
}
.tile-add:hover { opacity: 0.7; }
.tile-add-icon {
    font-size: 36px;
    color: """ + TEXT_MUTED + """;
}
.tile-add-text {
    font-size: 14px;
    color: """ + TEXT_MUTED + """;
    margin-top: 6px;
}

/* Fixed weekly summary button */
.weekly-summary-trigger {
    position: fixed !important;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
}
.weekly-summary-trigger button {
    background: #00B4D8 !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 10px 20px !important;
    border-radius: 24px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

/* Back button styling */
.back-btn button {
    background: transparent !important;
    color: """ + TEXT_PRIMARY + """ !important;
    font-size: 16px !important;
    padding: 8px 16px !important;
}
.back-btn button:hover {
    background: """ + BG_SECONDARY + """ !important;
}

/* Form styling */
div[data-testid="stForm"] {
    background: """ + BG_SECONDARY + """ !important;
    border: none !important;
    border-radius: 8px;
    padding: 20px;
}

/* Tab styling */
button[data-baseweb="tab"] {
    font-family: 'Lexend', sans-serif !important;
    font-size: 16px !important;
    font-weight: 500 !important;
}

/* Metric styling */
div[data-testid="stMetric"] {
    background: """ + BG_SECONDARY + """;
    border-radius: 8px;
    padding: 12px 16px;
}
div[data-testid="stMetric"] label {
    font-size: 14px !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 24px !important;
    font-weight: 600 !important;
}

/* Expander styling */
details[data-testid="stExpander"] {
    background: """ + BG_SECONDARY + """ !important;
    border: none !important;
    border-radius: 8px !important;
}

/* Dialog styling */
div[data-testid="stDialog"] > div {
    background: """ + BG_PRIMARY + """ !important;
    border: 1px solid """ + BG_SECONDARY + """ !important;
}

/* Responsive: mobile single column */
@media (max-width: 768px) {
    .tile-card { min-height: 110px; padding: 16px; }
    .tile-label { font-size: 18px; }
    h1, .stMarkdown h1 { font-size: 24px !important; }
    .stButton button { min-height: 48px; }
}
"""


def page_header(title, colour=None):
    css = f"color: {colour};" if colour else ""
    return f'<h1 style="margin-bottom: 4px; {css}">{title}</h1>'


def coloured_divider(colour):
    return f'<div style="height: 3px; background: {colour}; border-radius: 2px; margin: 4px 0 20px 0;"></div>'
