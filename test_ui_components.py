"""
Tests for reusable Streamlit UI components.
"""

import ui_components


def test_get_risk_style_maps_known_levels():
    """Known risk labels should map to a configured style."""

    low_style = ui_components.get_risk_style(
        "Risque faible"
    )
    critical_style = ui_components.get_risk_style(
        "critical"
    )

    assert low_style["label"] == "Risque faible"
    assert critical_style["label"] == "Risque critique"


def test_get_risk_style_falls_back_to_neutral():
    """Unknown risk labels should use the neutral style."""

    style = ui_components.get_risk_style(
        "unknown"
    )

    assert style["label"] == "Neutre"


def test_render_section_title_returns_html(monkeypatch):
    """Section titles should render through Streamlit and return HTML."""

    rendered = []

    def fake_markdown(
        html,
        unsafe_allow_html=False
    ):
        rendered.append(
            (
                html,
                unsafe_allow_html
            )
        )

    monkeypatch.setattr(
        ui_components.st,
        "markdown",
        fake_markdown
    )

    html = ui_components.render_section_title(
        "Portfolio",
        "Risk view"
    )

    assert "Portfolio" in html
    assert "Risk view" in html
    assert rendered[0][1] is True


def test_render_kpi_card_escapes_content(monkeypatch):
    """KPI cards should escape user-provided text."""

    monkeypatch.setattr(
        ui_components.st,
        "markdown",
        lambda html, unsafe_allow_html=False: None
    )

    html = ui_components.render_kpi_card(
        "<script>",
        "100",
        helper="<unsafe>"
    )

    assert "&lt;script&gt;" in html
    assert "&lt;unsafe&gt;" in html


def test_render_status_pill_can_return_without_rendering():
    """Status pills can be embedded in other HTML blocks."""

    html = ui_components.render_status_pill(
        "Yahoo Finance",
        status="neutral",
        render=False
    )

    assert "Yahoo Finance" in html
    assert "aria-pill" in html
