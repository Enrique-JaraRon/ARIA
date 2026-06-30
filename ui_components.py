"""
ARIA - Reusable Streamlit UI components.

The functions in this module keep visual presentation out of the
quantitative modules. They render small, reusable HTML blocks through
Streamlit and return the generated HTML to make them easy to test.
"""

from html import escape

import streamlit as st

RISK_STYLES = {
    "low": {
        "label": "Risque faible",
        "background": "#EAF7F0",
        "border": "#B7E4CA",
        "color": "#176B45",
    },
    "moderate": {
        "label": "Risque modere",
        "background": "#FFF7E6",
        "border": "#FBD38D",
        "color": "#9A5B00",
    },
    "high": {
        "label": "Risque eleve",
        "background": "#FEECEC",
        "border": "#F8B4B4",
        "color": "#B42318",
    },
    "critical": {
        "label": "Risque critique",
        "background": "#2B0A0A",
        "border": "#F97066",
        "color": "#FFFFFF",
    },
    "neutral": {
        "label": "Neutre",
        "background": "#EEF2F7",
        "border": "#CBD5E1",
        "color": "#334155",
    },
}


def _markdown(html: str) -> str:
    """Render HTML in Streamlit and return it for tests."""

    st.markdown(
        html,
        unsafe_allow_html=True,
    )
    return html


def get_risk_style(level: str | None) -> dict[str, str]:
    """Return the visual style associated with a risk level."""

    if not level:
        return RISK_STYLES["neutral"]

    normalized = level.strip().lower()

    if normalized in {
        "faible",
        "low",
        "risque faible",
    }:
        return RISK_STYLES["low"]

    if normalized in {
        "modere",
        "modéré",
        "moderate",
        "risque modere",
        "risque modéré",
    }:
        return RISK_STYLES["moderate"]

    if normalized in {
        "eleve",
        "élevé",
        "high",
        "risque eleve",
        "risque élevé",
    }:
        return RISK_STYLES["high"]

    if normalized in {
        "critique",
        "critical",
        "risque critique",
    }:
        return RISK_STYLES["critical"]

    return RISK_STYLES["neutral"]


def inject_custom_css() -> str:
    """Inject a restrained finance-dashboard visual layer."""

    css = """
<style>
    :root {
        --aria-ink: #111827;
        --aria-muted: #64748B;
        --aria-panel: #FFFFFF;
        --aria-line: #D8DEE8;
        --aria-soft: #F6F8FB;
        --aria-accent: #2563EB;
    }

    .block-container {
        padding-top: 1.35rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background: #F7F9FC;
        border-right: 1px solid var(--aria-line);
    }

    [data-testid="stMetric"] {
        background: var(--aria-panel);
        border: 1px solid var(--aria-line);
        border-radius: 8px;
        padding: 0.85rem 0.95rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stDataEditor"] {
        border: 1px solid var(--aria-line);
        border-radius: 8px;
        overflow: hidden;
    }

    .aria-header {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: flex-start;
        padding: 1.1rem 1.25rem;
        margin-bottom: 1.2rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #F4F7FB 100%);
        border: 1px solid var(--aria-line);
        border-radius: 8px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
    }

    .aria-eyebrow {
        color: var(--aria-accent);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .aria-title {
        color: var(--aria-ink);
        font-size: 2rem;
        line-height: 1.15;
        font-weight: 760;
        margin: 0;
    }

    .aria-subtitle {
        color: var(--aria-muted);
        font-size: 0.98rem;
        max-width: 780px;
        margin-top: 0.35rem;
    }

    .aria-section-title {
        margin: 1.15rem 0 0.65rem;
        padding-left: 0.65rem;
        border-left: 4px solid var(--aria-accent);
    }

    .aria-section-title h2 {
        margin: 0;
        color: var(--aria-ink);
        font-size: 1.15rem;
        line-height: 1.25;
    }

    .aria-section-title p {
        margin: 0.2rem 0 0;
        color: var(--aria-muted);
        font-size: 0.9rem;
    }

    .aria-card {
        background: var(--aria-panel);
        border: 1px solid var(--aria-line);
        border-radius: 8px;
        padding: 0.95rem 1rem;
        min-height: 104px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
    }

    .aria-card-label {
        color: var(--aria-muted);
        font-size: 0.78rem;
        font-weight: 650;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .aria-card-value {
        color: var(--aria-ink);
        font-size: 1.45rem;
        font-weight: 760;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }

    .aria-card-help {
        color: var(--aria-muted);
        font-size: 0.85rem;
        margin-top: 0.35rem;
    }

    .aria-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        border: 1px solid;
        padding: 0.26rem 0.62rem;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
    }

    .aria-info-card {
        background: #F8FAFC;
        border: 1px solid var(--aria-line);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        color: #334155;
    }

    .aria-info-card strong {
        color: var(--aria-ink);
    }

    .aria-metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.75rem;
        margin: 0.6rem 0 1rem;
    }
</style>
"""

    return _markdown(css)


def render_header(
    title: str = "ARIA",
    subtitle: str = (
        "Adaptive Risk Intelligence Agent for equity and option portfolios."
    ),
    badge: str = "Risk Management Dashboard",
) -> str:
    """Render the main application header."""

    html = f"""
<div class="aria-header">
    <div>
        <div class="aria-eyebrow">{escape(badge)}</div>
        <h1 class="aria-title">{escape(title)}</h1>
        <div class="aria-subtitle">{escape(subtitle)}</div>
    </div>
    <div>{render_status_pill("Production-style prototype", render=False)}</div>
</div>
"""

    return _markdown(html)


def render_kpi_card(
    label: str,
    value: str | int | float,
    helper: str | None = None,
    risk_level: str | None = None,
) -> str:
    """Render a compact KPI card."""

    style = get_risk_style(risk_level)
    border = style["border"] if risk_level else "#D8DEE8"

    helper_html = ""
    if helper:
        helper_html = f'<div class="aria-card-help">{escape(str(helper))}</div>'

    html = f"""
<div class="aria-card" style="border-color: {border};">
    <div class="aria-card-label">{escape(label)}</div>
    <div class="aria-card-value">{escape(str(value))}</div>
    {helper_html}
</div>
"""

    return _markdown(html)


def render_risk_badge(
    level: str,
    label: str | None = None,
    render: bool = True,
) -> str:
    """Render a risk-level badge."""

    style = get_risk_style(level)
    text = label or style["label"]
    html = (
        f'<span class="aria-pill" style="'
        f'background: {style["background"]}; '
        f'border-color: {style["border"]}; '
        f'color: {style["color"]};'
        f'">{escape(text)}</span>'
    )

    if render:
        return _markdown(html)

    return html


def render_status_pill(
    label: str,
    status: str = "neutral",
    render: bool = True,
) -> str:
    """Render a small status pill."""

    return render_risk_badge(
        level=status,
        label=label,
        render=render,
    )


def render_section_title(
    title: str,
    subtitle: str | None = None,
) -> str:
    """Render a consistent section title."""

    subtitle_html = ""
    if subtitle:
        subtitle_html = f"<p>{escape(subtitle)}</p>"

    html = f"""
<div class="aria-section-title">
    <h2>{escape(title)}</h2>
    {subtitle_html}
</div>
"""

    return _markdown(html)


def render_info_card(
    title: str,
    body: str,
) -> str:
    """Render a restrained informational card."""

    html = f"""
<div class="aria-info-card">
    <strong>{escape(title)}</strong><br>
    {escape(body)}
</div>
"""

    return _markdown(html)


def render_metric_row(
    metrics: list[dict[str, str | int | float]],
) -> str:
    """Render several KPI cards as one responsive HTML row."""

    cards = []

    for metric in metrics:
        label = escape(str(metric.get("label", "")))
        value = escape(str(metric.get("value", "")))
        helper = metric.get("helper")
        risk_level = metric.get("risk_level")
        style = get_risk_style(str(risk_level)) if risk_level else None
        border = style["border"] if style else "#D8DEE8"
        helper_html = ""

        if helper:
            helper_html = (
                f'<div class="aria-card-help">{escape(str(helper))}</div>'
            )

        cards.append(
            f"""
<div class="aria-card" style="border-color: {border};">
    <div class="aria-card-label">{label}</div>
    <div class="aria-card-value">{value}</div>
    {helper_html}
</div>
"""
        )

    html = f"""
<div class="aria-metric-grid">
    {''.join(cards)}
</div>
"""

    return _markdown(html)
