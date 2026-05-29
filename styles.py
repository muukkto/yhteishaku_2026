import plotly.graph_objects as go
import plotly.io as pio

# --- Väripaletti ---

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
        font=dict(family="Arial, sans-serif", size=13, color="#333333"),
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
            sequential="Blues",
        ),
        margin=dict(l=60, r=40, t=60, b=60),
    )
)

# NOTE: Do NOT assign go.Bar() to template.data.bar — Plotly 6 tagify will break.
# Bar styling is applied via apply_bar_style() instead.

pio.templates.default = "plotly_white+valintakoe"


def apply_bar_style(fig):
    """Yhteinen tyyli kaikille bar charteille."""
    fig.update_layout(
        xaxis=dict(tickformat="d"),
        yaxis=dict(tickformat="d"),
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=15, family="Arial Bold, sans-serif"),
        marker=dict(line=dict(width=0)),
        selector=dict(type="bar"),
    )
    return fig
