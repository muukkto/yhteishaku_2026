import textwrap

import plotly.graph_objects as go
import plotly.io as pio

# --- Väripaletti ---

TEXT_COLOR = "#333333"
UNKNOWN_COLOR = "#333333"

YEAR_COLORS = {"2025": "#636EFA", "2026": "#EF553B"}

SEQUENTIAL_COLORSCALE = "Blues"

EXAM_COLORS = {
    'A': '#1f77b4',
    'B': '#ff7f0e',
    'C': '#2ca02c',
    'D': '#d62728',
    'E': '#9467bd',
    'F': '#8c564b',
    'G': '#e377c2',
    'H': '#7f7f7f',
    'I': '#bcbd22',
}

COLORWAY = list(EXAM_COLORS.values())

# --- Plotly-teema ---

pio.templates["valintakoe"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Arial, sans-serif", size=13, color=TEXT_COLOR),
        colorway=COLORWAY,
        paper_bgcolor="white",
        plot_bgcolor="white",
        title=dict(font=dict(size=16), x=0.5, xanchor="center"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#eeeeee",
            linecolor="#cccccc",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#eeeeee",
            linecolor="#cccccc",
            zeroline=False,
        ),
        colorscale=dict(
            sequential=SEQUENTIAL_COLORSCALE,
        ),
        margin=dict(l=60, r=40, t=60, b=60),
    )
)

pio.templates["valintakoe"].data.bar = [
    go.Bar(
        textposition="outside",
        textfont=dict(size=15, weight="bold"),
        marker=dict(
            line=dict(width=0),
        ),
    )
]

pio.templates.default = "plotly_white+valintakoe"


TITLE_WRAP_WIDTH = 70
TITLE_LINE_HEIGHT = 22
BASE_TOP_MARGIN = 60

HEATMAP_SIZE = 700
HEATMAP_MARGIN = dict(l=100, r=150, t=80, b=100)


def wrap_title(fig):
    """Rivittää pitkän otsikon ja kasvattaa ylämarginaalia rivien määrän mukaan."""
    text = fig.layout.title.text
    if not text:
        return fig
    lines = textwrap.wrap(text, width=TITLE_WRAP_WIDTH, break_long_words=False)
    top = max(fig.layout.margin.t or BASE_TOP_MARGIN, BASE_TOP_MARGIN)
    fig.update_layout(
        title_text="<br>".join(lines),
        margin_t=top + TITLE_LINE_HEIGHT * (len(lines) - 1),
    )
    return fig


def apply_bar_style(fig):
    """Yhteinen tyyli kaikille bar charteille."""
    fig.update_layout(
        xaxis=dict(tickformat="d"),
        yaxis=dict(tickformat="d"),
    )
    return wrap_title(fig)


def apply_heatmap_style(fig):
    """Yhteinen tyyli lämpökartoille."""
    fig.update_layout(
        width=HEATMAP_SIZE,
        height=HEATMAP_SIZE,
        margin=HEATMAP_MARGIN,
    )
    return wrap_title(fig)


def apply_treemap_style(fig):
    """Yhteinen tyyli treemapeille."""
    return wrap_title(fig)
