"""Tests for the guided AI portfolio generator utilities."""

import pandas as pd
import pytest

from portfolio_engine.portfolio_ai_generator import (
    fallback_portfolio,
    generated_portfolio_to_aria_table,
    validate_generated_portfolio,
)


def test_validate_generated_portfolio_merges_duplicates_and_normalizes_weights():
    raw = pd.DataFrame(
        [
            {
                "ticker": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "weight": 30,
                "asset_class": "Equity ETF",
                "sector": "US equities",
            },
            {
                "ticker": "vti",
                "name": "Duplicate VTI",
                "weight": 30,
                "asset_class": "Equity ETF",
                "sector": "US equities",
            },
            {
                "ticker": "BND",
                "name": "Vanguard Total Bond Market ETF",
                "weight": 20,
                "asset_class": "Bond ETF",
                "sector": "Core bonds",
            },
        ]
    )

    clean, warnings = validate_generated_portfolio(raw)

    assert clean["ticker"].tolist() == ["VTI", "BND"]
    assert clean["weight"].sum() == pytest.approx(100.0)
    assert any("Tickers en double" in warning for warning in warnings)


def test_fallback_portfolio_is_diversified_and_loadable_in_aria_schema():
    result = fallback_portfolio(
        {
            "risk_level": "Moderate",
            "style": "Balanced",
        }
    )

    generated = result["portfolio"]
    aria_table = generated_portfolio_to_aria_table(
        generated,
        total_value=100_000,
    )

    assert result["used_llm"] is False
    assert generated["weight"].sum() == pytest.approx(100.0)
    assert generated["ticker"].nunique() >= 5
    assert not aria_table.empty
    assert set(aria_table["Asset type"]) == {"stock"}
    assert aria_table["Weight"].sum() == pytest.approx(100.0)
    assert aria_table["Value"].sum() == pytest.approx(100_000.0)
    assert (aria_table["Quantity"] > 1).any()
    assert {"Ticker", "Quantity", "Price", "Instrument"}.issubset(
        aria_table.columns
    )


def test_fallback_portfolio_generates_real_option_rows_when_requested():
    result = fallback_portfolio(
        {
            "risk_level": "Équilibré",
            "objective": "Couverture",
            "instruments": ["ETF", "Options"],
        }
    )

    aria_table = generated_portfolio_to_aria_table(
        result["portfolio"],
        total_value=100_000,
    )
    option_rows = aria_table[aria_table["Asset type"] == "option"]

    assert not option_rows.empty
    assert set(option_rows["Option type"]).issubset({"call", "put"})
    assert option_rows["Strike"].notna().all()
    assert option_rows["Maturity"].notna().all()
    assert option_rows["Prime"].notna().all()
    assert option_rows["Position"].isin(["Long", "Short"]).all()
    assert aria_table["Weight"].sum() == pytest.approx(100.0)


def test_validate_generated_portfolio_accepts_numeric_option_fields():
    raw = pd.DataFrame(
        [
            {
                "ticker": "SPY",
                "name": "SPY protective put",
                "weight": 10,
                "asset_class": "Option",
                "sector": "Index options",
                "instrument_type": "option",
                "underlying": "SPY",
                "option_type": "put",
                "position": "long",
                "spot": 500.0,
                "strike": 475.0,
                "maturity": 0.25,
                "premium": 9.0,
                "implied_volatility": 0.24,
                "contract_size": 100,
            },
            {
                "ticker": "BND",
                "name": "Bond ETF",
                "weight": 70,
                "asset_class": "ETF / action",
                "sector": "Core bonds",
            },
        ]
    )

    clean, warnings = validate_generated_portfolio(raw)

    option_row = clean.loc[clean["instrument_type"] == "option"].iloc[0]
    assert warnings == []
    assert option_row["maturity"] == pytest.approx(0.25)
    assert option_row["strike"] == pytest.approx(475.0)
