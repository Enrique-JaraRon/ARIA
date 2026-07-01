"""Tests for professional portfolio analytics."""

import pandas as pd
import pytest

from portfolio_analytics import (
    get_model_portfolio,
    get_model_portfolio_names,
    model_portfolio_to_dataframe,
    portfolio_diagnosis,
    portfolio_exposure_table,
    rebalancing_recommendations,
    validate_portfolio_table,
)


def test_model_portfolios_are_available_and_weights_sum_to_one():
    names = get_model_portfolio_names()

    assert "Conservative Balanced Portfolio" in names
    assert "Crisis-Resilient Portfolio" in names
    assert "AI & Semiconductors Portfolio" in names
    assert "Global ETF Core Portfolio" in names
    assert "Long-Term Compounders Portfolio" in names

    for name in names:
        model = get_model_portfolio(name)
        assert sum(model.target_weights.values()) == pytest.approx(1.0)
        assert 0 < model.expected_return < 0.20
        assert 0 < model.volatility < 0.40
        assert model.diversification_score > 0


def test_model_portfolio_dataframe_uses_professional_schema():
    model = get_model_portfolio("Moderate Growth Portfolio")
    data = model_portfolio_to_dataframe(
        model,
        total_value=100_000,
    )

    assert not data.empty
    assert set(data["Asset type"]) == {"stock"}
    assert "Ticker" in data.columns
    assert "Sector" in data.columns
    assert "Price" in data.columns
    assert "Quantity" in data.columns
    assert "Weight" in data.columns
    assert "Value" in data.columns
    assert data["Weight"].sum() == pytest.approx(100.0)
    assert data["Value"].sum() == pytest.approx(100_000)


def test_stock_validation_does_not_require_option_fields():
    data = pd.DataFrame(
        [
            {
                "Asset type": "stock",
                "Ticker": "VTI",
                "Quantity": 10,
                "Price": 285,
                "Currency": "USD",
                "Sector": "US equities",
            }
        ]
    )

    assert validate_portfolio_table(data) == []


def test_option_validation_requires_option_fields():
    data = pd.DataFrame(
        [
            {
                "Asset type": "option",
                "Ticker": "SPY",
                "Quantity": 1,
                "Price": 500,
                "Currency": "USD",
            }
        ]
    )

    errors = validate_portfolio_table(data)

    assert any("option type" in error for error in errors)
    assert any("strike" in error for error in errors)
    assert any("maturity" in error for error in errors)
    assert any("volatility" in error for error in errors)
    assert any("rate" in error for error in errors)


def test_exposure_weights_sum_to_one():
    model = get_model_portfolio("Global Diversified Portfolio")
    data = model_portfolio_to_dataframe(
        model,
        total_value=100_000,
    )

    exposure = portfolio_exposure_table(data)

    assert exposure["Gross weight"].sum() == pytest.approx(1.0)
    assert exposure["Ticker"].nunique() == len(model.target_weights)
    for column in [
        "Name",
        "Currency",
        "Quantity",
        "Price",
        "Data source",
    ]:
        assert column in exposure.columns


def test_portfolio_diagnosis_identifies_concentration():
    data = pd.DataFrame(
        [
            {
                "Asset type": "stock",
                "Ticker": "NVDA",
                "Sector": "Semiconductors",
                "Quantity": 100,
                "Price": 100,
            },
            {
                "Asset type": "stock",
                "Ticker": "BND",
                "Sector": "Core bonds",
                "Quantity": 10,
                "Price": 100,
            },
        ]
    )

    diagnosis = portfolio_diagnosis(data)

    assert diagnosis["top_position"] == "NVDA"
    assert diagnosis["top_weight"] > 0.80
    assert diagnosis["concentration_level"] == "Élevée"


def test_rebalancing_recommendations_are_coherent():
    current = pd.DataFrame(
        [
            {
                "Asset type": "stock",
                "Ticker": "NVDA",
                "Sector": "Semiconductors",
                "Quantity": 100,
                "Price": 100,
            }
        ]
    )
    target = get_model_portfolio("Conservative Balanced Portfolio")

    recommendations, summary = rebalancing_recommendations(
        current_table=current,
        target_model=target,
    )

    assert not recommendations.empty
    assert "Reduce" in recommendations["Action"].to_list()
    assert summary["target_model"] == "Conservative Balanced Portfolio"
    assert summary["target_diversification_score"] == target.diversification_score
