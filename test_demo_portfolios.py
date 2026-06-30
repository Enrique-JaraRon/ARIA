"""
Tests for demo option portfolios.
"""

import pytest

from demo_portfolios import (
    create_demo_portfolio,
    get_demo_portfolio_names,
    portfolio_to_dataframe,
)


def test_get_demo_portfolio_names_returns_non_empty_list():
    """Demo portfolio names should be available for the UI."""

    names = get_demo_portfolio_names()

    assert isinstance(
        names,
        list
    )
    assert names


@pytest.mark.parametrize(
    "name",
    get_demo_portfolio_names()
)
def test_each_demo_portfolio_is_usable(name):
    """Each demo portfolio should be priced and have Greeks."""

    portfolio = create_demo_portfolio(
        name=name,
        spot=500.0,
        maturity=0.25,
        rate=0.05,
        volatility=0.20,
    )

    greeks = portfolio.total_greeks()

    assert portfolio.positions
    assert isinstance(
        portfolio.total_market_value(),
        float
    )
    assert "delta" in greeks
    assert "gamma" in greeks
    assert "vega" in greeks


def test_create_demo_portfolio_rejects_unknown_name():
    """Unknown demo names should fail explicitly."""

    with pytest.raises(
        ValueError
    ):
        create_demo_portfolio(
            name="Unknown Strategy"
        )


def test_portfolio_to_dataframe_matches_streamlit_columns():
    """Demo portfolios should convert to the editor table schema."""

    portfolio = create_demo_portfolio(
        name="Covered Call"
    )

    data = portfolio_to_dataframe(
        portfolio
    )

    assert not data.empty
    assert list(data.columns) == [
        "Instrument",
        "Nom",
        "Type option",
        "QuantitÃ©",
        "Multiplicateur",
        "Strike",
        "MaturitÃ©",
    ]
