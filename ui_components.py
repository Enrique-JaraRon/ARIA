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
        "background": "rgba(52, 211, 153, 0.14)",
        "border": "#34D399",
        "color": "#A7F3D0",
    },
    "moderate": {
        "label": "Risque modere",
        "background": "rgba(245, 185, 68, 0.14)",
        "border": "#F5B944",
        "color": "#FDE68A",
    },
    "high": {
        "label": "Risque eleve",
        "background": "rgba(255, 77, 109, 0.14)",
        "border": "#FF4D6D",
        "color": "#FDA4AF",
    },
    "critical": {
        "label": "Risque critique",
        "background": "rgba(255, 77, 109, 0.22)",
        "border": "#FF4D6D",
        "color": "#FFE4E6",
    },
    "neutral": {
        "label": "Neutre",
        "background": "rgba(0, 213, 255, 0.12)",
        "border": "#00D5FF",
        "color": "#BAE6FD",
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
    """Inject the ARIA futuristic risk-cockpit visual layer."""

    css = """
<style>
    :root {
        --aria-bg: #080C10;
        --aria-bg-2: #0D131A;
        --aria-panel: #111923;
        --aria-panel-2: #151F2A;
        --aria-panel-3: #0B1118;
        --aria-ink: #F4F7FB;
        --aria-muted: #9CA9BA;
        --aria-soft: #D5E2F2;
        --aria-line: #263546;
        --aria-line-strong: #36506A;
        --aria-cyan: #00D5FF;
        --aria-green: #34D399;
        --aria-amber: #F5B944;
        --aria-red: #FF4D6D;
        --aria-violet: #8B5CF6;
        --aria-shadow: rgba(0, 0, 0, 0.35);
    }

    html,
    body,
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(110deg, rgba(0, 213, 255, 0.06), transparent 34%, rgba(245, 185, 68, 0.05) 72%, transparent),
            linear-gradient(135deg, #080C10 0%, #0D131A 46%, #11140F 100%);
        background-size: 28px 28px, 28px 28px, auto, auto;
        color: var(--aria-ink);
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background:
            linear-gradient(90deg, transparent 0%, rgba(0, 213, 255, 0.05) 48%, transparent 52%),
            repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 3px, transparent 7px);
        opacity: 0.28;
        mix-blend-mode: screen;
        z-index: 0;
    }

    [data-testid="stAppViewContainer"] > .main {
        position: relative;
        z-index: 1;
    }

    .block-container {
        max-width: 1480px;
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(17, 25, 35, 0.98), rgba(8, 12, 16, 0.98)),
            repeating-linear-gradient(135deg, rgba(0, 213, 255, 0.05) 0 1px, transparent 1px 12px);
        border-right: 1px solid rgba(0, 213, 255, 0.28);
        box-shadow: 12px 0 40px rgba(0, 0, 0, 0.28);
    }

    [data-testid="stSidebar"] * {
        color: var(--aria-soft);
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--aria-ink);
        font-size: 0.92rem;
        font-weight: 760;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(0, 213, 255, 0.20);
        padding-bottom: 0.35rem;
        margin-top: 1.15rem;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: var(--aria-muted);
        font-size: 0.82rem;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] select {
        background: #0B1118 !important;
        color: var(--aria-ink) !important;
        border: 1px solid rgba(0, 213, 255, 0.28) !important;
        border-radius: 8px !important;
    }

    [data-testid="stMetric"] {
        background: var(--aria-panel);
        border: 1px solid rgba(0, 213, 255, 0.22);
        border-radius: 8px;
        padding: 0.95rem 1rem;
        box-shadow: 0 18px 42px var(--aria-shadow);
    }

    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--aria-muted);
    }

    [data-testid="stMetricValue"] {
        color: var(--aria-ink);
        font-weight: 760;
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stDataEditor"] {
        border: 1px solid rgba(0, 213, 255, 0.24);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.32);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(8, 12, 16, 0.72);
        border: 1px solid rgba(0, 213, 255, 0.18);
        border-radius: 8px;
        padding: 0.35rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 2.55rem;
        border-radius: 6px;
        color: var(--aria-muted);
        font-weight: 720;
        background: transparent;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, rgba(0, 213, 255, 0.18), rgba(52, 211, 153, 0.10));
        color: var(--aria-ink);
        border: 1px solid rgba(0, 213, 255, 0.34);
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 8px !important;
        border: 1px solid rgba(0, 213, 255, 0.42) !important;
        background: linear-gradient(135deg, rgba(0, 213, 255, 0.22), rgba(52, 211, 153, 0.18)) !important;
        color: #F8FBFF !important;
        font-weight: 760 !important;
        box-shadow: 0 12px 32px rgba(0, 213, 255, 0.14);
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        border-color: rgba(52, 211, 153, 0.72) !important;
        box-shadow: 0 18px 40px rgba(52, 211, 153, 0.16);
    }

    [data-testid="stAlert"] {
        border-radius: 8px;
        border: 1px solid rgba(0, 213, 255, 0.22);
        background: rgba(17, 25, 35, 0.88);
        color: var(--aria-ink);
    }

    h1,
    h2,
    h3,
    p,
    span,
    label {
        letter-spacing: 0;
    }

    h2,
    h3 {
        color: var(--aria-ink);
    }

    hr {
        border-color: rgba(0, 213, 255, 0.16);
    }

    .aria-header {
        position: relative;
        overflow: hidden;
        padding: 1.25rem 1.35rem 1.1rem;
        margin-bottom: 1.1rem;
        background:
            linear-gradient(90deg, rgba(0, 213, 255, 0.10), transparent 44%),
            linear-gradient(135deg, rgba(21, 31, 42, 0.98), rgba(10, 15, 20, 0.98));
        border: 1px solid rgba(0, 213, 255, 0.30);
        border-radius: 8px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.38);
    }

    .aria-header::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(90deg, rgba(0, 213, 255, 0.18) 0 1px, transparent 1px 100%),
            linear-gradient(0deg, rgba(255, 255, 255, 0.04) 0 1px, transparent 1px 100%);
        background-size: 56px 56px;
        opacity: 0.28;
        pointer-events: none;
    }

    .aria-header-main {
        position: relative;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 1rem;
        align-items: start;
        z-index: 1;
    }

    .aria-eyebrow {
        display: inline-flex;
        align-items: center;
        color: var(--aria-cyan);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .aria-title {
        color: var(--aria-ink);
        font-size: 2.35rem;
        line-height: 1.15;
        font-weight: 820;
        margin: 0;
        text-shadow: 0 0 26px rgba(0, 213, 255, 0.20);
    }

    .aria-subtitle {
        color: #C8D3E0;
        font-size: 1rem;
        max-width: 840px;
        margin-top: 0.45rem;
        line-height: 1.55;
    }

    .aria-header-status {
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }

    .aria-system-strip {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 1rem;
    }

    .aria-system-cell {
        background: rgba(8, 12, 16, 0.68);
        border: 1px solid rgba(0, 213, 255, 0.18);
        border-radius: 8px;
        padding: 0.68rem 0.75rem;
    }

    .aria-system-label {
        color: var(--aria-muted);
        font-size: 0.72rem;
        font-weight: 740;
        text-transform: uppercase;
    }

    .aria-system-value {
        color: var(--aria-ink);
        font-size: 0.96rem;
        font-weight: 760;
        margin-top: 0.18rem;
    }

    .aria-section-title {
        display: grid;
        grid-template-columns: 3px minmax(0, 1fr);
        gap: 0.7rem;
        align-items: center;
        margin: 1.2rem 0 0.75rem;
    }

    .aria-section-title::before {
        content: "";
        width: 3px;
        height: 100%;
        min-height: 38px;
        background: linear-gradient(180deg, var(--aria-cyan), var(--aria-green));
        border-radius: 999px;
        box-shadow: 0 0 18px rgba(0, 213, 255, 0.42);
    }

    .aria-section-copy {
        min-width: 0;
    }

    .aria-section-title h2 {
        margin: 0;
        color: var(--aria-ink);
        font-size: 1.12rem;
        line-height: 1.25;
        font-weight: 800;
    }

    .aria-section-title p {
        margin: 0.2rem 0 0;
        color: var(--aria-muted);
        font-size: 0.9rem;
    }

    .aria-card {
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(180deg, rgba(21, 31, 42, 0.96), rgba(11, 17, 24, 0.96));
        border: 1px solid rgba(0, 213, 255, 0.22);
        border-radius: 8px;
        padding: 0.95rem 1rem 0.9rem;
        min-height: 104px;
        box-shadow: 0 18px 44px rgba(0, 0, 0, 0.30);
    }

    .aria-card::after {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--aria-cyan), var(--aria-green), transparent);
        opacity: 0.72;
    }

    .aria-card-label {
        color: var(--aria-muted);
        font-size: 0.73rem;
        font-weight: 760;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .aria-card-value {
        color: var(--aria-ink);
        font-size: 1.34rem;
        font-weight: 760;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }

    .aria-card-help {
        color: #B4C2D3;
        font-size: 0.82rem;
        margin-top: 0.35rem;
    }

    .aria-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        border: 1px solid;
        padding: 0.34rem 0.72rem;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
        box-shadow: 0 0 20px rgba(0, 213, 255, 0.12);
    }

    .aria-info-card {
        background:
            linear-gradient(180deg, rgba(17, 25, 35, 0.94), rgba(11, 17, 24, 0.94));
        border: 1px solid rgba(0, 213, 255, 0.22);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        color: #B7C6D8;
        box-shadow: 0 14px 36px rgba(0, 0, 0, 0.22);
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

    @media (max-width: 760px) {
        .aria-header-main,
        .aria-system-strip {
            grid-template-columns: 1fr;
        }

        .aria-header-status {
            justify-content: flex-start;
        }

        .aria-title {
            font-size: 1.72rem;
        }
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
    <div class="aria-header-main">
        <div>
            <div class="aria-eyebrow">{escape(badge)}</div>
            <h1 class="aria-title">{escape(title)}</h1>
            <div class="aria-subtitle">{escape(subtitle)}</div>
        </div>
        <div class="aria-header-status">
            {render_status_pill("Production-style prototype", render=False)}
        </div>
    </div>
    <div class="aria-system-strip">
        <div class="aria-system-cell">
            <div class="aria-system-label">Core engine</div>
            <div class="aria-system-value">Black-Scholes + Greeks</div>
        </div>
        <div class="aria-system-cell">
            <div class="aria-system-label">Risk stack</div>
            <div class="aria-system-value">Stress, VaR, ES, Alerts</div>
        </div>
        <div class="aria-system-cell">
            <div class="aria-system-label">Reporting layer</div>
            <div class="aria-system-value">Executive report + LLM</div>
        </div>
    </div>
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
    <div class="aria-section-copy">
        <h2>{escape(title)}</h2>
        {subtitle_html}
    </div>
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
